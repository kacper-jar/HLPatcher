from __future__ import annotations

import shutil
from pathlib import Path

from patcher.core import Game, SOURCE_LINK_FIXES
from patcher.core.pipeline import BaseInstaller


class SourceInstaller(BaseInstaller):
    def install(self, game: Game, **kwargs):
        subfolders = kwargs.get("subfolders", [])
        self.patcher.log(f"Installing to {game.name}...")

        source_dir = self.patcher._context.working_dir / "source-engine"
        output_dir = source_dir / "output"

        bin_src = output_dir / "bin"
        if bin_src.is_dir():
            shutil.copytree(bin_src, game.path / "bin", dirs_exist_ok=True)

        for sub in subfolders:
            if sub == "lostcoast":
                mod_src = output_dir / "hl2"
            else:
                mod_src = output_dir / sub

            if mod_src.is_dir():
                shutil.copytree(mod_src, game.path / sub, dirs_exist_ok=True)

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

        self._fix_source_links(game.path)
        for sub in subfolders:
            self._fix_source_game_links(game.path, sub)

    def _fix_source_links(self, game_path: Path):
        self.patcher.log("Fixing Source Engine links...")
        bin_dir = game_path / "bin"
        working_dir = self.patcher._context.working_dir
        build_prefix = str(working_dir / "source-engine" / "build")
        thirdparty_prefix = str(working_dir / "source-engine" / "thirdparty" / "install" / "lib")

        for lib_name, changes in SOURCE_LINK_FIXES.items():
            lib_path = bin_dir / lib_name
            if not lib_path.exists():
                continue
            self.patcher.executor.run([
                "install_name_tool", "-id", f"@loader_path/{lib_name}", lib_name
            ], cwd=bin_dir)

            for old_path_template, new_path in changes:
                old_path = old_path_template.format(
                    build_prefix=build_prefix,
                    thirdparty_prefix=thirdparty_prefix
                )
                self.patcher.executor.run([
                    "install_name_tool", "-change", old_path, new_path, lib_name
                ], cwd=bin_dir)

    def _fix_source_game_links(self, game_path: Path, game_name: str):
        self.patcher.log(f"Fixing source game links for {game_name}...")
        bin_dir = game_path / game_name / "bin"
        if not bin_dir.exists():
            return

        working_dir = self.patcher._context.working_dir
        build_prefix = str(working_dir / "source-engine" / "build")
        thirdparty_prefix = str(working_dir / "source-engine" / "thirdparty" / "install" / "lib")

        for lib_name, loader_prefix in [("libclient.dylib", "../../bin"), ("libserver.dylib", "../../bin")]:
            lib_path = bin_dir / lib_name
            if not lib_path.exists():
                continue
            self.patcher.executor.run([
                "install_name_tool", "-id", f"@loader_path/{lib_name}", lib_name
            ], cwd=bin_dir)

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
                self.patcher.executor.run([
                    "install_name_tool", "-change", old_path, new_path, lib_name
                ], cwd=bin_dir)
