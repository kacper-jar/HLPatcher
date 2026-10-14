import shutil

from patcher.core.models import Component, Game, InstallStepConfig
from patcher.core.pipeline.installers.generic_installer import GenericInstaller
from patcher.core.pipeline.registry import step


@step("goldsrc-engine-installer", config=InstallStepConfig)
class GoldSrcEngineInstaller(GenericInstaller):
    def execute(self, game: Game, comp: Component, step_config: InstallStepConfig):
        xash_dir = self.context.working_dir / step_config.patch_dir_name
        built_launcher = xash_dir / "output" / "xash3d"
        if not built_launcher.is_file():
            raise FileNotFoundError(f"xash3d launcher not found: {built_launcher}")
        steam_launcher = xash_dir / "output" / "steam_launcher"
        if not steam_launcher.is_file():
            raise FileNotFoundError(f"Steam launcher not found: {steam_launcher}")

        super().execute(game, comp, step_config)

        self.context.log("Installing GoldSrc Engine...")

        sdl_src = xash_dir / "3rdparty" / "SDL2.framework"
        sdl_dest = game.path / "SDL2.framework"
        shutil.copytree(sdl_src, sdl_dest, dirs_exist_ok=True)

        (game.path / "xash3d").replace(game.path / "hl_osx")

        valve_script = game.path / "hl.sh"
        if valve_script.is_file() and valve_script.read_bytes().startswith(b"#!"):
            self.context.log("Keeping Valve's hl.sh as hl_launcher.sh...")
            valve_script.replace(game.path / "hl_launcher.sh")
        self.context.log("Installing Steam launcher as hl.sh...")
        (game.path / "steam_launcher").replace(valve_script)
        valve_script.chmod(0o755)
