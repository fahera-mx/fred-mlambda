import pytest

from fred.mlambda.interface import Arguments, MLambda


# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

def test_arguments_stores_args_and_kwargs():
    a = Arguments(args=[1, 2], kwargs={"key": "val"})
    assert a.args == [1, 2]
    assert a.kwargs == {"key": "val"}


def test_arguments_is_frozen():
    a = Arguments(args=[], kwargs={})
    with pytest.raises((AttributeError, TypeError)):
        a.args = [1]  # type: ignore[misc]


# ---------------------------------------------------------------------------
# MLambda
# ---------------------------------------------------------------------------

def test_mlambda_function_resolves_builtin():
    # Use a stdlib module so the test doesn't depend on package internals
    ml = MLambda(name="join", import_pattern="os.path")
    fn = ml.function
    assert callable(fn)


def test_mlambda_function_raises_on_missing_name():
    ml = MLambda(name="does_not_exist_ever", import_pattern="os.path")
    with pytest.raises(ValueError, match="not found in module"):
        _ = ml.function


def test_mlambda_run_via_arguments():
    # math.factorial(5) == 120
    ml = MLambda(name="factorial", import_pattern="math")
    args = Arguments(args=[5], kwargs={})
    assert ml.run(args) == 120


def test_mlambda_callable_interface():
    ml = MLambda(name="factorial", import_pattern="math")
    assert ml(5) == 120


def test_mlambda_is_frozen():
    ml = MLambda(name="factorial", import_pattern="math")
    with pytest.raises((AttributeError, TypeError)):
        ml.name = "other"  # type: ignore[misc]
