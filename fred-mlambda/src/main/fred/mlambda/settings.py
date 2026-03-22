import os

from fred.settings import get_environ_variable


FRED_MLAMBDA_ALIASES_SEP = get_environ_variable(
    "FRED_MLAMBDA_ALIASES_SEP",
    default=";"
)

FRED_MLAMBDA_ALIASES = [
    alias
    for line in get_environ_variable(
        "FRED_MLAMBDA_ALIASES",
        default="",
    ).split(FRED_MLAMBDA_ALIASES_SEP)
    if "=" in line and (alias := line.strip().split("="))
]

FRED_MLAMBDA_PARSED_ALIASES = {
    "count": "fred.mlambda._count.count",
    **{
        key: val
        for key, val in FRED_MLAMBDA_ALIASES
    }
}
