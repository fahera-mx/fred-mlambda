import os

from fred.version import Version


version = Version.from_path(
    name="fred.mlambda",
    dirpath=os.path.dirname(__file__)
)
