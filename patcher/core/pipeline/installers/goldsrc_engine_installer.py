import shutil

from patcher.core.models import Component, Game, InstallStepConfig
from patcher.core.pipeline.installers.generic_installer import GenericInstaller
from patcher.core.pipeline.registry import step


@step("goldsrc-engine-installer")
class GoldSrcEngineInstaller(GenericInstaller):
    def execute(self, game: Game, comp: Component, step_config: InstallStepConfig):
        xash_dir = self.patcher._context.working_dir / step_config.patch_dir_name
        built_launcher = xash_dir / "output" / "xash3d"
        if not built_launcher.is_file():
            raise FileNotFoundError(f"xash3d launcher not found: {built_launcher}")

        super().execute(game, comp, step_config)

        self.patcher.log("Installing GoldSrc Engine...")

        sdl_src = xash_dir / "3rdparty" / "SDL2.framework"
        sdl_dest = game.path / "SDL2.framework"
        shutil.copytree(sdl_src, sdl_dest, dirs_exist_ok=True)

        (game.path / "xash3d").replace(game.path / "hl_osx")
