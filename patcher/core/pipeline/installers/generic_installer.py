from __future__ import annotations

import shutil

from patcher.core import Game
from patcher.core.pipeline import BaseInstaller


class GenericInstaller(BaseInstaller):
    def __init__(self, patcher, target_dir_name: str):
        super().__init__(patcher)
        self.target_dir_name = target_dir_name

    def install(self, game: Game, **kwargs):
        self.patcher.log(f"Installing {self.target_dir_name}...")
        output_dir = self.patcher._context.working_dir / self.target_dir_name / "output"
        shutil.copytree(output_dir, game.path, dirs_exist_ok=True)
