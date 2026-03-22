import pytest

from fred.mlambda.parser import MLambdaParser
from fred.mlambda.interface import Arguments, MLambda


# ---------------------------------------------------------------------------
# MLambdaParser.cast()
# ---------------------------------------------------------------------------

class TestCast:
    def test_plain_string(self):
        assert MLambdaParser.cast("hello") == "hello"

    def test_autoinfer_integer(self):
        assert MLambdaParser.cast("42") == 42

    def test_autoinfer_float(self):
        assert MLambdaParser.cast("3.14") == 3.14

    def test_autoinfer_bool_true(self):
        assert MLambdaParser.cast("true") is True

    def test_autoinfer_bool_false(self):
        assert MLambdaParser.cast("false") is False

    def test_autoinfer_null(self):
        assert MLambdaParser.cast("null") is None
        assert MLambdaParser.cast("none") is None
        assert MLambdaParser.cast("") is None

    def test_explicit_int_annotation(self):
        assert MLambdaParser.cast("42::int") == 42
        assert isinstance(MLambdaParser.cast("42::int"), int)

    def test_explicit_float_annotation(self):
        assert MLambdaParser.cast("1.5::float") == 1.5

    def test_explicit_bool_annotation_false(self):
        assert MLambdaParser.cast("false::bool") is False
        assert MLambdaParser.cast("0::bool") is False

    def test_explicit_str_annotation(self):
        # Forces string even for digit input
        assert MLambdaParser.cast("42::str") == "42"
        assert isinstance(MLambdaParser.cast("42::str"), str)

    def test_unknown_type_annotation_raises(self):
        with pytest.raises(ValueError, match="Unknown type annotation"):
            MLambdaParser.cast("42::complex")

    def test_disable_autoinfer_keeps_raw_string(self):
        assert MLambdaParser.cast("42", disable_autoinfer=True) == "42"
        assert MLambdaParser.cast("true", disable_autoinfer=True) == "true"


# ---------------------------------------------------------------------------
# MLambdaParser.parse_line()
# ---------------------------------------------------------------------------

class TestParseLine:
    def test_empty_string_returns_empty(self):
        args, kwargs = MLambdaParser.parse_line("")
        assert args == []
        assert kwargs == {}

    def test_positional_args_only(self):
        args, kwargs = MLambdaParser.parse_line("a,b,c")
        assert args == ["a", "b", "c"]
        assert kwargs == {}

    def test_kwargs_only(self):
        args, kwargs = MLambdaParser.parse_line("x=1,y=2")
        assert args == []
        assert kwargs == {"x": 1, "y": 2}

    def test_mixed_args_and_kwargs(self):
        args, kwargs = MLambdaParser.parse_line("hello,42,verbose=true")
        assert args == ["hello", 42]
        assert kwargs == {"verbose": True}

    def test_typed_args(self):
        args, kwargs = MLambdaParser.parse_line("10::int,3.14::float")
        assert args == [10, 3.14]

    def test_quoted_value_with_comma(self):
        # CSV quoting: "hello, world" is one token
        args, kwargs = MLambdaParser.parse_line('"hello, world",42')
        assert args[0] == "hello, world"
        assert args[1] == 42


# ---------------------------------------------------------------------------
# MLambdaParser.from_string()
# ---------------------------------------------------------------------------

class TestFromString:
    def test_full_dotpath_resolves_mlambda(self):
        expr = "${math.factorial: 5}"
        parsed = MLambdaParser.from_string(expr)
        assert isinstance(parsed.mlambda, MLambda)
        assert parsed.mlambda.name == "factorial"
        assert parsed.mlambda.import_pattern == "math"
        assert parsed.arguments.args == [5]

    def test_alias_resolves_via_catalog(self):
        expr = "${STROPS: hello, lower}"
        parsed = MLambdaParser.from_string(expr)
        assert parsed.mlambda.name == "strops"

    def test_settings_alias_count_resolves(self):
        expr = "${count: hello}"
        parsed = MLambdaParser.from_string(expr)
        assert parsed.mlambda.name == "count"

    def test_kwargs_are_parsed(self):
        expr = "${math.factorial: n=5}"
        parsed = MLambdaParser.from_string(expr)
        assert parsed.arguments.kwargs == {"n": 5}

    def test_no_args_produces_empty_arguments(self):
        expr = "${math.factorial: }"
        parsed = MLambdaParser.from_string(expr)
        assert parsed.arguments.args == []
        assert parsed.arguments.kwargs == {}

    def test_invalid_expression_raises(self):
        with pytest.raises(ValueError, match="Invalid MLambda expression"):
            MLambdaParser.from_string("not_valid_at_all")

    def test_unknown_alias_raises(self):
        with pytest.raises(ValueError):
            MLambdaParser.from_string("${totally_unknown: }")

    def test_execute_runs_function(self):
        expr = "${math.factorial: 6}"
        parsed = MLambdaParser.from_string(expr)
        assert parsed.execute() == 720


# ---------------------------------------------------------------------------
# _extract_outer() and _serialize() — internal helpers
# ---------------------------------------------------------------------------

from fred.mlambda.parser import _extract_outer, _serialize


class TestExtractOuter:
    def test_flat_expression(self):
        funref, param_line = _extract_outer("${math.factorial: 5}")
        assert funref == "math.factorial"
        assert param_line.strip() == "5"

    def test_nested_expression_outer_only(self):
        funref, param_line = _extract_outer("${count: ${RAND: alice, bob}}")
        assert funref == "count"
        assert "${RAND: alice, bob}" in param_line

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="Missing ':'"):
            _extract_outer("${RAND}")

    def test_unmatched_brace_raises(self):
        with pytest.raises(ValueError, match="Unmatched"):
            _extract_outer("${RAND: alice")

    def test_trailing_chars_raises(self):
        with pytest.raises(ValueError, match="Unexpected characters"):
            _extract_outer("${RAND: alice} extra")

    def test_invalid_funref_raises(self):
        with pytest.raises(ValueError, match="Invalid function reference"):
            _extract_outer("${123bad: x}")


class TestSerialize:
    def test_none(self):
        assert _serialize(None) == "null"

    def test_true(self):
        assert _serialize(True) == "true"

    def test_false(self):
        assert _serialize(False) == "false"

    def test_int(self):
        assert _serialize(42) == "42"

    def test_float(self):
        assert _serialize(3.14) == "3.14"

    def test_string(self):
        assert _serialize("alice") == "alice"


# ---------------------------------------------------------------------------
# Nested expression integration tests
# ---------------------------------------------------------------------------

_POPULATION = ("alice", "bob", "carol")


class TestNested:
    def test_one_level_nested_execute(self):
        # RAND picks one name; COUNT returns its length
        expr = "${count: ${RAND: alice, bob, carol}}"
        result = MLambdaParser.from_string(expr).execute()
        assert isinstance(result, int)
        assert result in {len(n) for n in _POPULATION}

    def test_two_level_nested_execute(self):
        # ${COUNT: ${STROPS: hello, upper}} -> COUNT("HELLO") -> 5
        expr = "${count: ${STROPS: hello, upper}}"
        result = MLambdaParser.from_string(expr).execute()
        assert result == 5

    def test_sibling_nested_args(self):
        # ${STROPS: ${RAND: hello, world}, upper} -> "HELLO" or "WORLD"
        expr = "${STROPS: ${RAND: hello, world}, upper}"
        result = MLambdaParser.from_string(expr).execute()
        assert result in ("HELLO", "WORLD")

    def test_three_levels_deep(self):
        # RAND -> "hi" or "hello" -> upper -> "HI" or "HELLO" -> count -> 2 or 5
        expr = "${count: ${STROPS: ${RAND: hi, hello}, upper}}"
        result = MLambdaParser.from_string(expr).execute()
        assert result in (2, 5)

    def test_nested_does_not_break_flat(self):
        assert MLambdaParser.from_string("${count: hello}").execute() == 5
        assert MLambdaParser.from_string("${math.factorial: 5}").execute() == 120

    def test_resolve_nested_flat_passthrough(self):
        flat = "alice, bob"
        assert MLambdaParser._resolve_nested(flat) == flat

    def test_resolve_nested_replaces_inner(self):
        result = MLambdaParser._resolve_nested("${STROPS: hello, upper}")
        assert result == "HELLO"
