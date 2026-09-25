from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from patcher.core.models import Component, Game

if TYPE_CHECKING:
    from patcher.core.patcher import Patcher


class BaseStep(ABC):
    interruptible = True

    def __init__(self, patcher: Patcher):
        self.patcher = patcher

    @abstractmethod
    def execute(self, game: Game, comp: Component, step_config):
        pass
