from typing import Any


def count(value: Any, fail: bool = False) -> int:
    if hasattr(value, "__len__"):
        return len(value)
    from collections.abc import Sized
    if isinstance(value, Sized):
        return len(value)
    error = f"Unknown type: {type(value)}"
    if fail:
        raise ValueError(error)
    return 0
