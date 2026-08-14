from typing import Any

STEP_REGISTRY: dict[str, type[Any]] = {}


def step(type_name: str):
    """
    Decorator to register a BaseStep subclass with a specific string name.

    Usage:
        @step("git-fetcher")
        class GitFetcher(BaseStep):
            ...
    """

    def decorator(cls):
        STEP_REGISTRY[type_name] = cls
        return cls

    return decorator
