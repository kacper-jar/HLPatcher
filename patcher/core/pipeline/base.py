from abc import ABC, abstractmethod

from patcher.core.models import Component, Game, StepConfig, StepContext


class BaseStep(ABC):
    interruptible = True
    config_class: type[StepConfig]

    def __init__(self, context: StepContext):
        self.context = context

    @abstractmethod
    def execute(self, game: Game, comp: Component, step_config):
        pass
