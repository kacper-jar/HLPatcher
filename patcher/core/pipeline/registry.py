from typing import Any

from patcher.core.models import StepConfig

STEP_REGISTRY: dict[str, type[Any]] = {}


def step(type_name: str, config: type[StepConfig]):
    """
    Decorator to register a BaseStep subclass with a specific string name and the config class it reads.

    Usage:
        @step("git-fetcher", config=FetchStepConfig)
        class GitFetcher(BaseStep):
            ...
    """

    def decorator(cls):
        cls.config_class = config
        STEP_REGISTRY[type_name] = cls
        return cls

    return decorator


def parse_step_config(data: dict[str, Any]) -> StepConfig:
    step_class = STEP_REGISTRY.get(data.get("type"))
    if step_class is None:
        raise ValueError(f"Unknown step type: {data.get('type')!r}")
    return step_class.config_class(**data)
