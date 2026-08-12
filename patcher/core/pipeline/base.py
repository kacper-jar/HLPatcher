from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from patcher.core.patcher import Patcher
    from patcher.core import Game, Component


class BaseStep(ABC):
    def __init__(self, patcher: Patcher):
        self.patcher = patcher

    @abstractmethod
    def execute(self, game: Game, comp: Component, step_config):
        pass
