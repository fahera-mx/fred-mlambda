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
