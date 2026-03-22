import re
import io
import csv
from dataclasses import dataclass
from typing import Any, Callable, Union, Optional

from fred.mlambda.interface import Arguments, MLambda
from fred.mlambda.catalog import MLambdaCatalog

# Matches: ${path.to.function: param_line}
# Group 1 (dotpath):   "path.to.function"
# Group 2 (param_line): "arg1,arg2,kwarg1=value1,..."
_MLAMBDA_PATTERN = re.compile(
    r"^\$\{\s*(?P<funref>[A-Za-z_][A-Za-z0-9_.]*)\s*:\s*(?P<param_line>[^}]*)\}$"
)

# Supported type annotations via the "::" syntax, e.g. "42::int"
MLAMBDA_TYPES = Optional[Union[int, float, bool, str]]
_NULL_VALUES = ("null", "none", "")
_TYPE_CASTERS: dict[str, Callable] = {
    "int": int,
    "float": float,
    "bool": lambda v: v.strip().lower() not in ("false", "0", "no", ""),
    "str": str,
}


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
        # Check for type annotation
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
    def from_string(cls, string: str) -> "MLambdaParser":
        payload = string.strip()

        match = _MLAMBDA_PATTERN.match(payload)
        if not match:
            raise ValueError(
                f"Invalid MLambda expression: {payload!r}\n"
                "Expected format: ${path.to.function: arg1,arg2,kwarg1=value1,...}"
            )
        # Get the function reference and param_line from the match
        funref: str = match.group("funref")
        param_line: str = match.group("param_line")
        # Parse the CSV-like parameter line
        args, kwargs = cls.parse_line(param_line)
        arguments = Arguments(
            args=args,
            kwargs=kwargs,
        )
        # If the function reference is an alias, get the MLambda from the catalog
        if "." not in funref:
            return cls(
                mlambda=MLambdaCatalog.get_or_create(funref, fail=True),
                arguments=arguments,
            )
        # Split "path.to.function" -> import_pattern="path.to", fname="function"
        import_pattern, fname = funref.rsplit(".", 1)
        return cls(
            mlambda=MLambda(
                name=fname,
                import_pattern=import_pattern
            ),
            arguments=arguments,
        )

    def execute(self) -> Any:
        return self.mlambda.run(arguments=self.arguments)
