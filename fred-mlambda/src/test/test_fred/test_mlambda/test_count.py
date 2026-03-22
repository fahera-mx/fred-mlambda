import pytest

from fred.mlambda._count import count


@pytest.mark.parametrize("value,expected", [
    ("hello",          5),
    ("",               0),
    ([1, 2, 3],        3),
    ([],               0),
    ({"a": 1, "b": 2}, 2),
    ({},               0),
    ({1, 2, 3},        3),
    (set(),            0),
    ((1, 2),           2),
])
def test_count_sized_types(value, expected):
    assert count(value) == expected


def test_count_unsized_returns_zero():
    # integers have no __len__
    result = count(42, fail=False)
    assert result == 0


def test_count_unsized_raises_on_fail():
    with pytest.raises(ValueError, match="Unknown type"):
        count(42, fail=True)
