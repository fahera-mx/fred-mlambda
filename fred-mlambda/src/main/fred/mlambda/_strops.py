from typing import Optional


def strops(string: str, ops: str, fail: bool = False) -> Optional[str]:
    match ops:
        case "lower":
            return string.lower()
        case "upper":
            return string.upper()
        case "title":
            return string.title()
        case "capitalize":
            return string.capitalize()
        case "strip":
            return string.strip()
        case "lstrip":
            return string.lstrip()
        case "rstrip":
            return string.rstrip()
        case _:
            msg = f"Unknown operation: {ops}"
            if fail:
                raise ValueError(msg)
            return None
