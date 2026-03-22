import os


FRED_MLAMBDA_ALIASES_SEP = os.environ.get(
    "FRED_MLAMBDA_ALIASES_SEP",
    ";",
)

FRED_MLAMBDA_ALIASES = [
    alias
    for line in os.environ.get(
        "FRED_MLAMBDA_ALIASES",
        "",
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
