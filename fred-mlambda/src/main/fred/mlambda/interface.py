from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class Arguments:
    args: list
    kwargs: dict


@dataclass(frozen=True, slots=True)
class MLambda:
    name: str
    import_pattern: str

    @property
    def function(self) -> Callable:
        import importlib
        # Import the module
        module = importlib.import_module(self.import_pattern)
        # Get the function from the module
        if not (fn := getattr(module, self.name, None)):
            raise ValueError(f"Function {self.name} not found in module {self.import_pattern}")
        return fn

    def run(self, arguments: Arguments):
        return self.function(*arguments.args, **arguments.kwargs)

    def __call__(self, *args, **kwargs):
        arguments = Arguments(
            args=args,
            kwargs=kwargs
        )
        return self.run(
            arguments=arguments
        )
