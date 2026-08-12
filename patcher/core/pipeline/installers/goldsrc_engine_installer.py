from __future__ import annotations

import shutil

from patcher.core import Game, Component, InstallStepConfig
from patcher.core.pipeline import step
from patcher.core.pipeline.installers import GenericInstaller


@step("goldsrc-engine-installer")
class GoldSrcEngineInstaller(GenericInstaller):
    def execute(self, game: Game, comp: Component, step_config: InstallStepConfig):
        super().execute(game, comp, step_config)

        self.patcher.log("Installing GoldSrc Engine...")
        xash_dir = self.patcher._context.working_dir / step_config.patch_dir_name

        sdl_src = xash_dir / "3rdparty" / "SDL2.framework"
        sdl_dest = game.path / "SDL2.framework"
        shutil.copytree(sdl_src, sdl_dest, dirs_exist_ok=True)

        hl_osx = game.path / "hl_osx"
        xash3d = game.path / "xash3d"
        if hl_osx.exists():
            hl_osx.unlink()
        if xash3d.exists():
            xash3d.rename(hl_osx)
