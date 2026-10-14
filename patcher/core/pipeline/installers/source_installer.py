import shutil
from pathlib import Path

from patcher.core.constants import SOURCE_LINK_FIXES
from patcher.core.models import Component, Game, SourceInstallStepConfig
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step


@step("source-installer", config=SourceInstallStepConfig)
class SourceInstaller(BaseStep):
    interruptible = False

    def execute(self, game: Game, comp: Component, step_config: SourceInstallStepConfig):
        subfolder = comp.subfolder
        self.context.log(f"Installing to {game.name}...")

        source_dir = self.context.working_dir / step_config.patch_dir_name
        output_dir = source_dir / "output"

        steam_launcher = output_dir / "steam_launcher"
        if not steam_launcher.is_file():
            raise FileNotFoundError(f"Steam launcher not found: {steam_launcher}")

        bin_src = output_dir / "bin"
        if bin_src.is_dir():
            shutil.copytree(bin_src, game.path / "bin", dirs_exist_ok=True)

        if subfolder == "lostcoast":
            mod_src = output_dir / "hl2"
        else:
            mod_src = output_dir / subfolder

        if mod_src.is_dir():
            shutil.copytree(mod_src, game.path / subfolder, dirs_exist_ok=True)

        thirdparty_libs = source_dir / "thirdparty" / "install" / "lib"
        bin_dir = game.path / "bin"
        bin_dir.mkdir(exist_ok=True)
        for dylib in thirdparty_libs.glob("*.dylib"):
            shutil.copy2(dylib, bin_dir / dylib.name)

        hl2_launcher = output_dir / "hl2_launcher"
        hl2_osx = game.path / "hl2_osx"
        if hl2_launcher.exists():
            if hl2_osx.exists():
                hl2_osx.unlink()
            shutil.copy2(hl2_launcher, hl2_osx)
            hl2_osx.chmod(0o755)

        valve_script = game.path / "hl2.sh"
        if valve_script.is_file() and valve_script.read_bytes().startswith(b"#!"):
            self.context.log("Keeping Valve's hl2.sh as hl2_launcher.sh...")
            valve_script.replace(game.path / "hl2_launcher.sh")
        self._install_steam_launcher(steam_launcher, game.path / "hl2.sh")
        if step_config.steam_executable:
            self._install_steam_launcher(steam_launcher, game.path / step_config.steam_executable)

        self._fix_source_links(game.path, step_config.patch_dir_name)
        self._fix_source_game_links(game.path, subfolder, step_config.patch_dir_name)

    def _install_steam_launcher(self, steam_launcher: Path, destination: Path):
        self.context.log(f"Installing Steam launcher as {destination.name}...")
        destination.unlink(missing_ok=True)
        shutil.copy2(steam_launcher, destination)
        destination.chmod(0o755)

    def _fix_source_links(self, game_path: Path, patch_dir_name: str):
        self.context.log("Fixing Source Engine links...")
        bin_dir = game_path / "bin"
        working_dir = self.context.working_dir
        build_prefix = str(working_dir / patch_dir_name / "build")
        thirdparty_prefix = str(working_dir / patch_dir_name / "thirdparty" / "install" / "lib")

        for lib_name, changes in SOURCE_LINK_FIXES.items():
            lib_path = bin_dir / lib_name
            if not lib_path.exists():
                continue

            cmd = ["install_name_tool", "-id", f"@loader_path/{lib_name}"]
            for old_path_template, new_path in changes:
                old_path = old_path_template.format(
                    build_prefix=build_prefix,
                    thirdparty_prefix=thirdparty_prefix
                )
                cmd.extend(["-change", old_path, new_path])
            cmd.append(lib_name)

            self.context.executor.run(cmd, cwd=bin_dir)

    def _fix_source_game_links(self, game_path: Path, game_name: str, patch_dir_name: str):
        self.context.log(f"Fixing source game links for {game_name}...")
        bin_dir = game_path / game_name / "bin"
        if not bin_dir.exists():
            return

        working_dir = self.context.working_dir
        build_prefix = str(working_dir / patch_dir_name / "build")
        thirdparty_prefix = str(working_dir / patch_dir_name / "thirdparty" / "install" / "lib")

        for lib_name, loader_prefix in [("libclient.dylib", "../../bin"), ("libserver.dylib", "../../bin")]:
            lib_path = bin_dir / lib_name
            if not lib_path.exists():
                continue

            cmd = ["install_name_tool", "-id", f"@loader_path/{lib_name}"]

            changes = [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", f"@loader_path/{loader_prefix}/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", f"@loader_path/{loader_prefix}/libtier0.dylib"),
                (f"{build_prefix}/stub_steam/libsteam_api.dylib", f"@loader_path/{loader_prefix}/libsteam_api.dylib"),
            ]

            if lib_name == "libclient.dylib":
                changes.append(
                    (f"{thirdparty_prefix}/libz.1.dylib", "@loader_path/../../lib/libz.1.3.1.dylib")
                )

            for old_path, new_path in changes:
                cmd.extend(["-change", old_path, new_path])
            cmd.append(lib_name)

            self.context.executor.run(cmd, cwd=bin_dir)
