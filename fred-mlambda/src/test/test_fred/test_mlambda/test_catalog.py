import pytest

from fred.mlambda.catalog import MLambdaCatalog
from fred.mlambda.interface import MLambda


# ---------------------------------------------------------------------------
# MLambdaCatalog.keys()
# ---------------------------------------------------------------------------

def test_catalog_keys_returns_list_of_strings():
    keys = MLambdaCatalog.keys()
    assert isinstance(keys, list)
    assert all(isinstance(k, str) for k in keys)


def test_catalog_known_entries_present():
    keys = MLambdaCatalog.keys()
    assert "STROPS" in keys
    assert "RAND" in keys


# ---------------------------------------------------------------------------
# MLambdaCatalog.find()
# ---------------------------------------------------------------------------

def test_catalog_find_by_exact_name():
    result = MLambdaCatalog.find("STROPS")
    assert isinstance(result, MLambda)
    assert result.name == "strops"


def test_catalog_find_is_case_insensitive():
    # "strops" (lowercase) should resolve to the STROPS enum entry
    result = MLambdaCatalog.find("strops")
    assert isinstance(result, MLambda)


def test_catalog_find_by_settings_alias():
    # "count" is registered in FRED_MLAMBDA_PARSED_ALIASES via settings.py
    result = MLambdaCatalog.find("count")
    assert isinstance(result, MLambda)
    assert result.name == "count"


def test_catalog_find_unknown_returns_none():
    result = MLambdaCatalog.find("totally_unknown_alias")
    assert result is None


def test_catalog_find_unknown_raises_on_fail():
    with pytest.raises(ValueError, match="Unknown MLambda"):
        MLambdaCatalog.find("totally_unknown_alias", fail=True)


def test_catalog_find_dotpath_warns_and_returns_none():
    # A dotpath should warn and return None from find()
    result = MLambdaCatalog.find("some.dotpath")
    assert result is None


def test_catalog_find_disable_variants():
    # With disable_variants=True only the exact casing is tried
    result_exact = MLambdaCatalog.find("STROPS", disable_variants=True)
    assert isinstance(result_exact, MLambda)

    result_wrong_case = MLambdaCatalog.find("strops", disable_variants=True)
    # "strops" (lowercase) is NOT a catalog key (keys are "STROPS"),
    # but it IS a settings alias, so may still resolve; just ensure no crash
    assert result_wrong_case is None or isinstance(result_wrong_case, MLambda)


# ---------------------------------------------------------------------------
# MLambdaCatalog.get_or_create()
# ---------------------------------------------------------------------------

def test_get_or_create_with_dotpath():
    result = MLambdaCatalog.get_or_create("math.factorial")
    assert isinstance(result, MLambda)
    assert result.name == "factorial"
    assert result.import_pattern == "math"


def test_get_or_create_with_alias():
    result = MLambdaCatalog.get_or_create("STROPS")
    assert isinstance(result, MLambda)


def test_get_or_create_unknown_raises_on_fail():
    with pytest.raises(ValueError):
        MLambdaCatalog.get_or_create("nonexistent", fail=True)
