from __future__ import annotations

import shutil
from pathlib import Path

from patcher.core import Component, EngineType, Game, PatchMode, SOURCE_LINK_FIXES
from patcher.core.patcher import Patcher


class SourcePatcher:
    def __init__(self, patcher: Patcher):
        self.patcher = patcher
        self.context = patcher._context

    def log(self, message: str):
        self.patcher.log(message)

    def _notify_component(self, name: str):
        self.patcher._notify_component(name)

    def _run_command(self, *args, **kwargs):
        return self.patcher._run_command(*args, **kwargs)

    def process(self, selected_games: list[Game]):
        source_games = [g for g in selected_games if g.engine_type == EngineType.SOURCE]
        if not source_games:
            return

        waf_games = set()
        all_selected_comps = []
        for game in source_games:
            selected_comps = [c for c in game.components if c.needs_patch]
            if selected_comps:
                all_selected_comps.extend([(game, c) for c in selected_comps])
                for comp in selected_comps:
                    if comp.waf_game:
                        waf_games.add(comp.waf_game)

        if not all_selected_comps:
            return

        source_comp = all_selected_comps[0][1] if all_selected_comps else None

        self._notify_component("Source Engine")
        self._prepare_engine(source_comp)
        self.patcher._patch_generic("source-engine")

        waf_game_names = {
            "hl2": "Half-Life 2",
            "episodic": "Half-Life 2: Episodes",
            "hl1": "Half-Life: Source",
            "portal": "Portal",
        }

        for waf_game in waf_game_names:
            if waf_game in waf_games:
                game_title = waf_game_names[waf_game]
                self._notify_component(game_title)
                self._build_source(waf_game)

        for game in source_games:
            game_selected_comps = [c for g, c in all_selected_comps if g == game]
            if not game_selected_comps:
                continue

            self.log(f"Installing to {game.name}...")
            self._install_source_all(game.path, [c.subfolder for c in game_selected_comps])

            self._fix_source_links(game.path)

            for comp in game_selected_comps:
                self._fix_source_game_links(game.path, comp.subfolder)

    def _prepare_engine(self, comp: Component):
        self.log("Preparing Source Engine...")
        target_dir = self.context.working_dir / "source-engine"
        self._run_command([
            "git", "clone", "--recursive",
            "https://github.com/nillerusr/source-engine",
            str(target_dir),
        ])
        if self.context.patch_mode == PatchMode.STABLE:
            self._run_command(["git", "checkout", comp.stable_commit], cwd=target_dir)
            self._run_command(["git", "submodule", "update", "--init", "--recursive"], cwd=target_dir)

    def _build_source(self, game: str):
        self.log(f"Building Source Engine ({game})...")
        source_dir = self.context.working_dir / "source-engine"
        output_dir = source_dir / "output"
        self._run_command([
            "./waf", "configure", "-T", "release",
            "--prefix=",
            f"--build-games={game}",
            "build", "install",
            f"--destdir={output_dir}",
        ], cwd=source_dir)

    def _install_source_all(self, game_path: Path, subfolders: list[str]):
        self.log("Installing Source Engine binaries...")
        source_dir = self.context.working_dir / "source-engine"
        output_dir = source_dir / "output"

        bin_src = output_dir / "bin"
        if bin_src.is_dir():
            shutil.copytree(bin_src, game_path / "bin", dirs_exist_ok=True)

        for sub in subfolders:
            if sub == "lostcoast":
                mod_src = output_dir / "hl2"
            else:
                mod_src = output_dir / sub

            if mod_src.is_dir():
                shutil.copytree(mod_src, game_path / sub, dirs_exist_ok=True)

        thirdparty_libs = source_dir / "thirdparty" / "install" / "lib"
        bin_dir = game_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        for dylib in thirdparty_libs.glob("*.dylib"):
            shutil.copy2(dylib, bin_dir / dylib.name)

        hl2_launcher = output_dir / "hl2_launcher"
        hl2_osx = game_path / "hl2_osx"
        if hl2_launcher.exists():
            if hl2_osx.exists():
                hl2_osx.unlink()
            shutil.copy2(hl2_launcher, hl2_osx)
            hl2_osx.chmod(0o755)

    def _fix_source_links(self, game_path: Path):
        self.log("Fixing Source Engine links...")
        bin_dir = game_path / "bin"
        working_dir = self.context.working_dir
        build_prefix = str(working_dir / "source-engine" / "build")
        thirdparty_prefix = str(working_dir / "source-engine" / "thirdparty" / "install" / "lib")

        for lib_name, changes in SOURCE_LINK_FIXES.items():
            lib_path = bin_dir / lib_name
            if not lib_path.exists():
                continue
            self._run_command([
                "install_name_tool", "-id", f"@loader_path/{lib_name}", lib_name
            ], cwd=bin_dir)

            for old_path_template, new_path in changes:
                old_path = old_path_template.format(
                    build_prefix=build_prefix,
                    thirdparty_prefix=thirdparty_prefix
                )
                self._run_command([
                    "install_name_tool", "-change", old_path, new_path, lib_name
                ], cwd=bin_dir)

    def _fix_source_game_links(self, game_path: Path, game_name: str):
        self.log(f"Fixing source game links for {game_name}...")
        bin_dir = game_path / game_name / "bin"
        if not bin_dir.exists():
            return

        working_dir = self.context.working_dir
        build_prefix = str(working_dir / "source-engine" / "build")
        thirdparty_prefix = str(working_dir / "source-engine" / "thirdparty" / "install" / "lib")

        for lib_name, loader_prefix in [("libclient.dylib", "../../bin"), ("libserver.dylib", "../../bin")]:
            lib_path = bin_dir / lib_name
            if not lib_path.exists():
                continue
            self._run_command([
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
                self._run_command([
                    "install_name_tool", "-change", old_path, new_path, lib_name
                ], cwd=bin_dir)
