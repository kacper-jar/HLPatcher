from abc import ABC, abstractmethod

from patcher.core.models import Component, Game
from patcher.core.patcher import Patcher


class BaseStep(ABC):
    def __init__(self, patcher: Patcher):
        self.patcher = patcher

    @abstractmethod
    def execute(self, game: Game, comp: Component, step_config):
        pass
