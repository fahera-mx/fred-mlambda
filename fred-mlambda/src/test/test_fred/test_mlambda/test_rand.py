import pytest

from fred.mlambda._rand import rand

_POPULATION = ("a", "b", "c", "d")


def test_rand_single_returns_scalar():
    # Default k=1 with autoflat → returns a single element, not a list
    result = rand(*_POPULATION)
    assert result in _POPULATION


def test_rand_multiple_returns_list():
    result = rand(*_POPULATION, k=3)
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(item in _POPULATION for item in result)


def test_rand_disable_autoflat_returns_list_of_one():
    result = rand(*_POPULATION, k=1, disable_autoflat=True)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] in _POPULATION


def test_rand_empty_population():
    # random.choices with empty population raises IndexError
    with pytest.raises(IndexError):
        rand(k=1, disable_autoflat=True)


def test_rand_single_element_population():
    result = rand("only", k=2)
    assert result == ["only", "only"]
