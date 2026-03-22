from enum import Enum
from typing import Optional

from fred.mlambda.settings import FRED_MLAMBDA_PARSED_ALIASES
from fred.mlambda.interface import MLambda


class MLambdaCatalog(Enum):
    STROPS = MLambda(
        name="strops",
        import_pattern="fred.mlambda._strops",
    )
    RAND = MLambda(
        name="rand",
        import_pattern="fred.mlambda._rand",
    )

    @classmethod
    def keys(cls) -> list[str]:
        return [
            mem.name
            for mem in cls
        ]

    @classmethod
    def get_or_create(cls, target: str, fail: bool = False) -> Optional[MLambda]:
        if "." in target:
            *import_path, function_name = target.split(".")
            return MLambda(
                name=function_name,
                import_pattern=".".join(import_path),
            )
        return cls.find(
            alias=target,
            fail=fail,
        )

    @classmethod
    def find(cls, alias: str, fail: bool = False, disable_variants: bool = False) -> Optional[MLambda]:
        if "." in alias:
            return None
        variants: list[str] = [alias, alias.upper(), alias.lower()]
        for variant in variants[:(1 if disable_variants else len(variants))]:
            # Check if the target is an alias registered in the environment or defaults
            if variant in FRED_MLAMBDA_PARSED_ALIASES:
                *import_path, function_name = FRED_MLAMBDA_PARSED_ALIASES[variant].split(".")
                return MLambda(
                    name=function_name,
                    import_pattern=".".join(import_path),
                )
            # Check if the alias is a registered MLambdaCatalog Enum
            elif variant in cls.keys():
                return cls[variant].value
        error = f"Unknown MLambda: {alias}"
        if fail:
            raise ValueError(error)
        return None
