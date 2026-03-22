from typing import Any, Optional

from fred.settings import logger_manager


logger = logger_manager.get_logger(__name__)


def count(value: Any, fail: bool = False) -> int:
    if hasattr(value, "__len__"):
        return len(value)
    from collections.abc import Sized
    if isinstance(value, Sized):
        return len(value)
    error = f"Unknown type: {type(value)}"
    logger.warning(error)
    if fail:
        raise ValueError(error)
    return 0
