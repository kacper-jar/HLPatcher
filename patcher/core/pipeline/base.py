from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from patcher.core.patcher import Patcher
    from patcher.core import Game


class BaseFetcher(ABC):
    def __init__(self, patcher: Patcher):
        self.patcher = patcher

    @abstractmethod
    def fetch(self):
        pass


class BaseBuilder(ABC):
    def __init__(self, patcher: Patcher):
        self.patcher = patcher

    @abstractmethod
    def build(self):
        pass


class BaseInstaller(ABC):
    def __init__(self, patcher: Patcher):
        self.patcher = patcher

    @abstractmethod
    def install(self, game: Game, **kwargs):
        pass
