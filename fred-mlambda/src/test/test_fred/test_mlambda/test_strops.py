import pytest

from fred.mlambda._strops import strops


@pytest.mark.parametrize("ops,input_str,expected", [
    ("lower",      "Hello World",  "hello world"),
    ("upper",      "Hello World",  "HELLO WORLD"),
    ("title",      "hello world",  "Hello World"),
    ("capitalize", "hello world",  "Hello world"),
    ("strip",      "  hello  ",    "hello"),
    ("lstrip",     "  hello  ",    "hello  "),
    ("rstrip",     "  hello  ",    "  hello"),
])
def test_strops_known_operations(ops, input_str, expected):
    assert strops(input_str, ops) == expected


def test_strops_unknown_op_returns_none():
    result = strops("hello", "nonexistent_op", fail=False)
    assert result is None


def test_strops_unknown_op_raises_on_fail():
    with pytest.raises(ValueError, match="Unknown operation"):
        strops("hello", "nonexistent_op", fail=True)
