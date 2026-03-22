import random
from typing import Any


def rand(*args, k=1, disable_autoflat: bool = False) -> list[Any]:
    if not disable_autoflat and k == 1:
        out, *_ = rand(*args, k=k, disable_autoflat=True)
        return out
    return random.choices(
        population=args,
        k=k,
    )
