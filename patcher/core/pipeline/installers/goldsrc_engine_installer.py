from __future__ import annotations

import shutil

from patcher.core import Game
from patcher.core.pipeline.installers import GenericInstaller


class GoldSrcEngineInstaller(GenericInstaller):
    def install(self, game: Game, **kwargs):
        super().install(game, **kwargs)

        self.patcher.log("Installing GoldSrc Engine...")
        xash_dir = self.patcher._context.working_dir / self.target_dir_name

        sdl_src = xash_dir / "3rdparty" / "SDL2.framework"
        sdl_dest = game.path / "SDL2.framework"
        shutil.copytree(sdl_src, sdl_dest, dirs_exist_ok=True)

        hl_osx = game.path / "hl_osx"
        xash3d = game.path / "xash3d"
        if hl_osx.exists():
            hl_osx.unlink()
        if xash3d.exists():
            xash3d.rename(hl_osx)
