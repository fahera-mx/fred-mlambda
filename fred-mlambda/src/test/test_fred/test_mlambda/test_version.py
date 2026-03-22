from fred.mlambda.version import version


def test_version():
    assert isinstance(version.value, str)
