import re
import io
import csv
from dataclasses import dataclass
from typing import Any, Callable, Union, Optional

from fred.mlambda.interface import Arguments, MLambda
from fred.mlambda.catalog import MLambdaCatalog

# Matches innermost ${...} — i.e. no $, {, or } inside the braces.
# Used by _resolve_nested to find leaf-level expressions to evaluate first.
_INNER_PATTERN = re.compile(r"\$\{[^${}]*\}")

# Validates the funref portion: "path.to.function" or "ALIAS"
_FUNREF_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")

# Supported type annotations via the "::" syntax, e.g. "42::int"
MLAMBDA_TYPES = Optional[Union[int, float, bool, str]]
_NULL_VALUES = ("null", "none", "")
_TYPE_CASTERS: dict[str, Callable] = {
    "int": int,
    "float": float,
    "bool": lambda v: v.strip().lower() not in ("false", "0", "no", ""),
    "str": str,
}


def _serialize(value: Any) -> str:
    """
    Convert an execution result back into a string token that cast() can
    handle — used when embedding a nested result into its parent param_line.

    Examples:
        None        -> "null"
        True        -> "true"
        False       -> "false"
        42          -> "42"
        3.14        -> "3.14"
        "alice"     -> "alice"
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _extract_outer(string: str) -> tuple[str, str]:
    """
    Parse the outermost ${funref: param_line} shell using a brace-depth
    counter so that nested '}' inside param_line are handled correctly.

    Returns:
        (funref, raw_param_line)

    Raises:
        ValueError: if the string is not a valid outer MLambda expression.
    """
    s = string.strip()

    if not s.startswith("${"):
        raise ValueError(
            f"Invalid MLambda expression: {s!r}\n"
            "Expected format: ${funref: arg1,arg2,kwarg=value,...}"
        )

    # Walk from position 1 (the '{') counting brace depth
    depth = 0
    closing = -1
    for i in range(1, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                closing = i
                break

    if closing == -1:
        raise ValueError(f"Unmatched '{{' in MLambda expression: {s!r}")
    if closing != len(s) - 1:
        raise ValueError(
            f"Unexpected characters after closing '}}' in: {s!r}"
        )

    inner = s[2:closing]  # content between ${ and }

    colon_idx = inner.find(":")
    if colon_idx == -1:
        raise ValueError(
            f"Missing ':' separator in MLambda expression: {s!r}\n"
            "Expected format: ${funref: param_line}"
        )

    funref = inner[:colon_idx].strip()
    param_line = inner[colon_idx + 1:]

    if not _FUNREF_RE.match(funref):
        raise ValueError(
            f"Invalid function reference {funref!r}. "
            "Must be an identifier or dotted path (e.g. 'MY_ALIAS' or 'path.to.func')."
        )

    return funref, param_line


@dataclass(frozen=True, slots=True)
class MLambdaParser:
    mlambda: MLambda
    arguments: Arguments

    @staticmethod
    def cast(raw: str, disable_autoinfer: bool = False) -> MLAMBDA_TYPES:
        """
        Parse a raw token string, applying an optional '::type' suffix.

        Examples:
            "hello"        -> "hello"   (str)
            "42::int"      -> 42        (int)
            "3.14::float"  -> 3.14      (float)
            "true::bool"   -> True      (bool)
        """
        raw = raw.strip()
        # Early exit for None values IF autoinfer is enabled
        if not disable_autoinfer and raw.lower() in ("null", "none", ""):
            return None
        # Check for explicit type annotation
        if "::" in raw:
            value_part, _, type_name = raw.rpartition("::")
            caster = _TYPE_CASTERS.get(type_name.strip())
            if caster is None:
                raise ValueError(
                    f"Unknown type annotation '{type_name}'. "
                    f"Supported: {list(_TYPE_CASTERS)}"
                )
            return caster(value_part.strip())
        if not disable_autoinfer and raw.isdigit():
            return int(raw)
        if not disable_autoinfer and raw.replace(".", "", 1).isdigit():
            return float(raw)
        if not disable_autoinfer and raw.lower() in ("true", "false"):
            return raw.lower() == "true"
        return raw

    @classmethod
    def parse_line(cls, param_line: str) -> tuple[list[MLAMBDA_TYPES], dict[str, MLAMBDA_TYPES]]:
        """
        Split a CSV-like parameter string into positional args and keyword args.

        The CSV reader handles:
        - Comma-separated tokens
        - Quoted values (e.g. "hello, world" treated as a single token)

        Each token is classified as:
        - kwarg if it contains '=' (first '=' is the separator)
        - positional arg otherwise

        Type coercion via '::type' is applied to every value.
        """
        args: list[MLAMBDA_TYPES] = []
        kwargs: dict[str, MLAMBDA_TYPES] = {}

        if not param_line.strip():
            return args, kwargs

        reader = csv.reader(io.StringIO(param_line), skipinitialspace=True)
        for row in reader:
            for token in row:
                token = token.strip()
                if not token:
                    continue
                if "=" in token:
                    key, _, raw_value = token.partition("=")
                    kwargs[key.strip()] = cls.cast(raw_value)
                else:
                    args.append(cls.cast(token))

        return args, kwargs

    @classmethod
    def _resolve_nested(cls, param_line: str) -> str:
        """
        Resolve all nested ${...} expressions within a param_line string,
        evaluating innermost expressions first and working outward.

        For each iteration, _INNER_PATTERN finds expressions with no nested
        braces (guaranteed to be fully flat), evaluates them via from_string,
        and serializes the result back as a plain token string.  Repeats until
        no ${...} remain.

        Example:
            "${RAND: alice, bob, carol}"
            -> (evaluates RAND) -> "alice"

            "${STROPS: ${RAND: hello, world}, upper}"
            -> pass 1: "${RAND: hello, world}" -> "world"
            -> param becomes "world, upper" (no more ${)
            -> parse_line sees: args=["world"], kwargs={"upper": ...}
            ... Wait: that's positional, so: args=["world", "upper"]
        """
        while "${" in param_line:
            resolved = _INNER_PATTERN.sub(
                lambda m: _serialize(cls.from_string(m.group(0)).execute()),
                param_line,
            )
            if resolved == param_line:
                # No substitution made — malformed inner expression
                raise ValueError(
                    f"Could not resolve nested MLambda expression in: {param_line!r}"
                )
            param_line = resolved
        return param_line

    @classmethod
    def from_string(cls, string: str) -> "MLambdaParser":
        """
        Parse a (potentially nested) MLambda expression string.

        Supports expressions at arbitrary nesting depth, e.g.:
            ${COUNT: ${RAND: alice, bob, carol}}
            ${STROPS: ${RAND: hello, world}, upper}
            ${A: ${B: ${C: x}}}
        """
        payload = string.strip()

        # Step 1: extract the outer ${funref: raw_param_line} shell
        # using a stack-based approach that correctly handles nested '}'
        funref, raw_param_line = _extract_outer(payload)

        # Step 2: resolve any nested ${...} within the param_line
        resolved_param_line = cls._resolve_nested(raw_param_line)

        # Step 3: parse the now-flat param_line
        args, kwargs = cls.parse_line(resolved_param_line)
        arguments = Arguments(args=args, kwargs=kwargs)

        # Step 4: resolve the function reference
        if "." not in funref:
            # Bare alias — look up in catalog / settings
            return cls(
                mlambda=MLambdaCatalog.get_or_create(funref, fail=True),
                arguments=arguments,
            )
        # Dotted path — construct MLambda directly
        import_pattern, fname = funref.rsplit(".", 1)
        return cls(
            mlambda=MLambda(name=fname, import_pattern=import_pattern),
            arguments=arguments,
        )

    def execute(self) -> Any:
        return self.mlambda.run(arguments=self.arguments)
