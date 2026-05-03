from __future__ import annotations

import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable

from patcher.core import EngineType, Game, PatchContext, PatchMode

logger = logging.getLogger(__name__)


class Patcher:
    def __init__(self, context: PatchContext, log_callback: Callable[[str], None] | None = None,
                 component_callback: Callable[[str], None] | None = None):
        self._context = context
        self._log_callback = log_callback
        self._component_callback = component_callback
        self._stopped = False
        self._current_process: subprocess.Popen | None = None

    def stop(self):
        self._stopped = True
        if self._current_process:
            self._current_process.terminate()

    def log(self, message: str):
        logger.info(message)
        if self._log_callback:
            self._log_callback(message)

    def _notify_component(self, name: str):
        if self._component_callback:
            self._component_callback(name)

    def get_total_steps(self, selected_games: list[Game]) -> int:
        steps = 0
        goldsrc_games = [g for g in selected_games if g.engine_type == EngineType.GOLDSRC]
        if goldsrc_games:
            game = goldsrc_games[0]
            selected_comps = [c for c in game.components if c.needs_patch]
            if any(c.subfolder == "" for c in selected_comps): steps += 1
            if any(c.subfolder == "valve" for c in selected_comps): steps += 1
            if any(c.subfolder == "gearbox" for c in selected_comps): steps += 1
            if any(c.subfolder == "bshift" for c in selected_comps): steps += 1
            if any(c.subfolder == "dmc" for c in selected_comps): steps += 1
            if any(c.subfolder == "cstrike" for c in selected_comps): steps += 1

        source_games = [g for g in selected_games if g.engine_type == EngineType.SOURCE]
        if source_games:
            game = source_games[0]
            selected_comps = [c for c in game.components if c.needs_patch]
            if selected_comps:
                steps += 1
                waf_games = set()
                for comp in selected_comps:
                    if comp.subfolder == "hl2" or comp.subfolder == "lostcoast":
                        waf_games.add("hl2")
                    elif comp.subfolder == "episodic":
                        waf_games.add("episodic")
                    elif comp.subfolder == "hl1":
                        waf_games.add("hl1")
                steps += len(waf_games)

        return steps

    def run(self, selected_games: list[Game]):
        try:
            self._create_backup(selected_games)
            self._prepare_environment()
            self._process_goldsrc_games(selected_games)
            self._process_source_games(selected_games)
            self._cleanup()
        except Exception as e:
            logger.error(f"Patching failed: {e}")
            raise

    def _create_backup(self, selected_games: list[Game]):
        if not self._context.create_backup:
            self.log("Skipping backup creation")
            return

        self.log("Creating backup...")
        date_str = datetime.now().strftime("%Y-%m-%d")
        for game in selected_games:
            backup_dest = Path.home() / "Documents" / f"{game.name} backup ({date_str})"
            self.log(f"Backing up {game.path} to {backup_dest}")
            shutil.copytree(game.path, backup_dest, dirs_exist_ok=True)
        self.log("Backup complete")

    def _prepare_environment(self):
        self.log("Preparing environment...")
        working_dir = self._context.working_dir
        if working_dir.exists():
            shutil.rmtree(working_dir)
        working_dir.mkdir(parents=True)

        self.log("Setting up Python venv for build tools...")
        self._run_command(["python3", "-m", "venv", str(working_dir / "venv")])
        venv_pip = str(working_dir / "venv" / "bin" / "pip")
        self._run_command([venv_pip, "install", "cmake", "ninja", "meson"])

    def _process_goldsrc_games(self, selected_games: list[Game]):
        goldsrc_games = [g for g in selected_games if g.engine_type == EngineType.GOLDSRC]
        if not goldsrc_games:
            return

        game = goldsrc_games[0]
        selected_components = [c for c in game.components if c.needs_patch]

        needs_engine = any(c.subfolder == "" for c in selected_components)
        needs_hl = any(c.subfolder == "valve" for c in selected_components)
        needs_opfor = any(c.subfolder == "gearbox" for c in selected_components)
        needs_bshift = any(c.subfolder == "bshift" for c in selected_components)
        needs_dmc = any(c.subfolder == "dmc" for c in selected_components)
        needs_cstrike = any(c.subfolder == "cstrike" for c in selected_components)

        if needs_engine:
            self._notify_component("GoldSrc Engine")
            self._prepare_goldsrc_engine()
            self._build_goldsrc_engine()
            self._install_goldsrc_engine(game.path)

        hlsdk_mods = []
        if needs_hl:
            hlsdk_mods.append(("hlfixed", self._get_ref("hlfixed", "78bc253"), "Half-Life"))
        if needs_opfor:
            hlsdk_mods.append(("opforfixed", self._get_ref("opforfixed", "654d15c"), "Opposing Force"))
        if needs_bshift:
            hlsdk_mods.append(("bshift", self._get_ref("bshift", "df5c272"), "Blue Shift"))
        if needs_dmc:
            hlsdk_mods.append(("dmc", self._get_ref("dmc", "895b28d", force_stable=True), "Deathmatch Classic"))

        for suffix, ref, mod_name in hlsdk_mods:
            self._notify_component(mod_name)
            self._prepare_hlsdk_mod(suffix, ref)
            self._build_hlsdk_mod(suffix)
            self._install_generic(f"hlsdk-portable-{suffix}", game.path)

        if needs_cstrike:
            self._notify_component("Counter-Strike")
            self._prepare_cstrike()
            self._patch_generic("cs16-client")
            self._build_cstrike()
            self._install_generic("cs16-client", game.path)

    def _process_source_games(self, selected_games: list[Game]):
        source_games = [g for g in selected_games if g.engine_type == EngineType.SOURCE]
        if not source_games:
            return

        game = source_games[0]
        selected_components = [c for c in game.components if c.needs_patch]
        if not selected_components:
            return

        self._notify_component("Source Engine")
        self._prepare_source_engine()
        self._patch_generic("source-engine")

        waf_games = set()
        for comp in selected_components:
            if comp.subfolder == "hl2" or comp.subfolder == "lostcoast":
                waf_games.add("hl2")
            elif comp.subfolder == "episodic":
                waf_games.add("episodic")
            elif comp.subfolder == "hl1":
                waf_games.add("hl1")

        waf_game_names = {
            "hl2": "Half-Life 2",
            "episodic": "Half-Life 2: Episodes",
            "hl1": "Half-Life: Source",
        }

        for waf_game in waf_games:
            game_title = waf_game_names.get(waf_game, f"Source Engine ({waf_game})")
            self._notify_component(game_title)
            self._build_source(waf_game)

        self._install_source_all(game.path)

        has_lost_coast = any(c.subfolder == "lostcoast" for c in selected_components)
        if has_lost_coast:
            self._install_lost_coast(game.path)

        self._fix_source_links(game.path)

        for comp in selected_components:
            game_name = comp.subfolder
            if game_name == "lostcoast":
                game_name = "lostcoast"
            self._fix_source_game_links(game.path, game_name)

    def _get_ref(self, branch: str, stable_commit: str, force_stable: bool = False) -> str:
        if force_stable or self._context.patch_mode == PatchMode.STABLE:
            return stable_commit
        return branch

    def _prepare_goldsrc_engine(self):
        self.log("Preparing GoldSrc Engine...")
        working_dir = self._context.working_dir
        xash_dir = working_dir / "xash3d-fwgs"
        self._run_command([
            "git", "clone", "--recursive",
            "https://github.com/FWGS/xash3d-fwgs",
            str(xash_dir),
        ])

        if self._context.patch_mode == PatchMode.STABLE:
            self._run_command(["git", "checkout", "d03ea4c"], cwd=xash_dir)

        sdl_dmg = working_dir / "SDL2-2.32.10.dmg"
        self._run_command([
            "curl", "-L", "-o", str(sdl_dmg),
            "https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-2.32.10.dmg",
        ])

        result = self._run_command(["hdiutil", "attach", str(sdl_dmg), "-nobrowse"], capture=True)
        mount_point = None
        for line in result.stdout.strip().split("\n"):
            if "/Volumes/" in line:
                mount_point = line.split("\t")[-1].strip()
                break

        if mount_point:
            sdl_dest = xash_dir / "3rdparty" / "SDL2.framework"
            shutil.copytree(Path(mount_point) / "SDL2.framework", sdl_dest, dirs_exist_ok=True)
            self._run_command(["hdiutil", "detach", mount_point])

    def _prepare_hlsdk_mod(self, suffix: str, ref: str):
        dir_name = f"hlsdk-portable-{suffix}"
        self.log(f"Preparing {dir_name}...")
        target_dir = self._context.working_dir / dir_name
        self._run_command([
            "git", "clone", "--recursive",
            "https://github.com/FWGS/hlsdk-portable",
            str(target_dir),
        ])
        self._run_command(["git", "checkout", ref], cwd=target_dir)

    def _prepare_cstrike(self):
        self.log("Preparing Counter-Strike...")
        target_dir = self._context.working_dir / "cs16-client"
        self._run_command([
            "git", "clone", "--recursive",
            "https://github.com/Velaron/cs16-client.git",
            str(target_dir),
        ])
        if self._context.patch_mode == PatchMode.STABLE:
            self._run_command(["git", "checkout", "123af8e"], cwd=target_dir)

    def _prepare_source_engine(self):
        self.log("Preparing Source Engine...")
        target_dir = self._context.working_dir / "source-engine"
        self._run_command([
            "git", "clone", "--recursive",
            "https://github.com/nillerusr/source-engine",
            str(target_dir),
        ])
        if self._context.patch_mode == PatchMode.STABLE:
            self._run_command(["git", "checkout", "ed8209c"], cwd=target_dir)

    def _patch_generic(self, component_name: str):
        self.log(f"Patching {component_name}...")
        patch_dir = self._context.script_dir / "fixes" / "src" / component_name
        target_dir = self._context.working_dir / component_name

        if not patch_dir.is_dir():
            self.log(f"No patch directory found for {component_name}")
            return

        patch_files = sorted(patch_dir.glob("*.patch"))
        for patch_file in patch_files:
            self.log(f"Applying patch: {patch_file.name}")
            self._run_command(["patch", "-p1", "-i", str(patch_file)], cwd=target_dir)

    def _build_goldsrc_engine(self):
        self.log("Building GoldSrc Engine...")
        xash_dir = self._context.working_dir / "xash3d-fwgs"
        sdl_path = xash_dir / "3rdparty" / "SDL2.framework"
        output_dir = xash_dir / "output"
        self._run_command([
            "./waf", "configure", "-8",
            "--enable-bundled-deps",
            f"--sdl2={sdl_path}",
            "build", "install",
            f"--destdir={output_dir}",
        ], cwd=xash_dir)

    def _build_hlsdk_mod(self, suffix: str):
        dir_name = f"hlsdk-portable-{suffix}"
        self.log(f"Building {dir_name}...")
        mod_dir = self._context.working_dir / dir_name
        output_dir = mod_dir / "output"
        self._run_command([
            "./waf", "configure", "-T", "release", "-8",
            "build", "install",
            f"--destdir={output_dir}",
        ], cwd=mod_dir)

    def _build_cstrike(self):
        self.log("Building Counter-Strike...")
        cs_dir = self._context.working_dir / "cs16-client"
        venv_python = str(self._context.working_dir / "venv" / "bin" / "python3")
        self._run_command([venv_python, "build_deps.py"], cwd=cs_dir)
        self._run_command([venv_python, "-m", "cmake", "-S", ".", "-B", "build"], cwd=cs_dir)
        self._run_command([venv_python, "-m", "cmake", "--build", "build", "--config", "Release"], cwd=cs_dir)
        output_dir = cs_dir / "output"
        self._run_command([venv_python, "-m", "cmake", "--install", "build", "--prefix", str(output_dir)], cwd=cs_dir)

    def _build_source(self, game: str):
        self.log(f"Building Source Engine ({game})...")
        source_dir = self._context.working_dir / "source-engine"
        output_dir = source_dir / "output"
        self._run_command([
            "./waf", "configure", "-T", "release",
            "--prefix=",
            f"--build-games={game}",
            "build", "install",
            f"--destdir={output_dir}",
        ], cwd=source_dir)

    def _install_generic(self, dir_name: str, game_path: Path):
        self.log(f"Installing {dir_name}...")
        output_dir = self._context.working_dir / dir_name / "output"
        shutil.copytree(output_dir, game_path, dirs_exist_ok=True)

    def _install_goldsrc_engine(self, game_path: Path):
        self.log("Installing GoldSrc Engine...")
        xash_dir = self._context.working_dir / "xash3d-fwgs"
        output_dir = xash_dir / "output"
        shutil.copytree(output_dir, game_path, dirs_exist_ok=True)

        sdl_src = xash_dir / "3rdparty" / "SDL2.framework"
        sdl_dest = game_path / "SDL2.framework"
        shutil.copytree(sdl_src, sdl_dest, dirs_exist_ok=True)

        hl_osx = game_path / "hl_osx"
        xash3d = game_path / "xash3d"
        if hl_osx.exists():
            hl_osx.unlink()
        if xash3d.exists():
            xash3d.rename(hl_osx)

    def _install_source_all(self, game_path: Path):
        self.log("Installing Source Engine...")
        source_dir = self._context.working_dir / "source-engine"
        output_dir = source_dir / "output"
        shutil.copytree(output_dir, game_path, dirs_exist_ok=True)

        thirdparty_libs = source_dir / "thirdparty" / "install" / "lib"
        bin_dir = game_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        for dylib in thirdparty_libs.glob("*.dylib"):
            shutil.copy2(dylib, bin_dir / dylib.name)

        hl2_osx = game_path / "hl2_osx"
        hl2_launcher = game_path / "hl2_launcher"
        if hl2_osx.exists():
            hl2_osx.unlink()
        if hl2_launcher.exists():
            hl2_launcher.rename(hl2_osx)

    def _install_lost_coast(self, game_path: Path):
        self.log("Installing Lost Coast...")
        source_output = self._context.working_dir / "source-engine" / "output" / "hl2"
        lostcoast_dest = game_path / "lostcoast"
        shutil.copytree(source_output, lostcoast_dest, dirs_exist_ok=True)

    def _fix_source_links(self, game_path: Path):
        self.log("Fixing Source Engine links...")
        bin_dir = game_path / "bin"
        working_dir = self._context.working_dir
        build_prefix = str(working_dir / "source-engine" / "build")
        thirdparty_prefix = str(working_dir / "source-engine" / "thirdparty" / "install" / "lib")

        link_fixes = {
            "libvphysics.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libtogl.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libdatacache.dylib": [
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libvaudio_minimp3.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libmaterialsystem.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libvguimatsurface.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
                (f"{thirdparty_prefix}/libfreetype.6.dylib", "@loader_path/libfreetype.6.dylib"),
                (f"{thirdparty_prefix}/libfontconfig.1.dylib", "@loader_path/libfontconfig.1.dylib"),
                (f"{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
            ],
            "libscenefilecache.dylib": [
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libsteam_api.dylib": [],
            "libServerBrowser.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
                (f"{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
            ],
            "libinputsystem.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
                (f"{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
                (f"{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
            ],
            "libvideo_services.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libvgui2.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
                (f"{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
            ],
            "libvtex_dll.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
                (f"{thirdparty_prefix}/libjpeg.9.dylib", "@loader_path/libjpeg.9.dylib"),
                (f"{thirdparty_prefix}/libpng16.16.dylib", "@loader_path/libpng16.16.dylib"),
                (f"{thirdparty_prefix}/libz.1.dylib", "@loader_path/libz.1.3.1.dylib"),
            ],
            "libtier0.dylib": [],
            "libshaderapidx9.dylib": [
                (f"{build_prefix}/togl/libtogl.dylib", "@loader_path/libtogl.dylib"),
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libGameUI.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
                (f"{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
                (f"{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
                (f"{thirdparty_prefix}/libjpeg.9.dylib", "@loader_path/libjpeg.9.dylib"),
                (f"{thirdparty_prefix}/libpng16.16.dylib", "@loader_path/libpng16.16.dylib"),
                (f"{thirdparty_prefix}/libz.1.dylib", "@loader_path/libz.1.3.1.dylib"),
            ],
            "libstudiorender.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "liblauncher.dylib": [
                (f"{build_prefix}/togl/libtogl.dylib", "@loader_path/libtogl.dylib"),
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
                (f"{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
                (f"{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
            ],
            "libfilesystem_stdio.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libstdshader_dx9.dylib": [
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libengine.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
                (f"{build_prefix}/stub_steam/libsteam_api.dylib", "@loader_path/libsteam_api.dylib"),
                (f"{thirdparty_prefix}/libSDL2-2.0.0.dylib", "@loader_path/libSDL2-2.0.0.dylib"),
                (f"{thirdparty_prefix}/libjpeg.9.dylib", "@loader_path/libjpeg.9.dylib"),
                (f"{thirdparty_prefix}/libz.1.dylib", "@loader_path/libz.1.3.1.dylib"),
                (f"{thirdparty_prefix}/libcurl.4.dylib", "@loader_path/libcurl.4.dylib"),
            ],
            "libsoundemittersystem.dylib": [
                (f"{build_prefix}/vstdlib/libvstdlib.dylib", "@loader_path/libvstdlib.dylib"),
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libpkgconf.7.dylib": [],
            "libpng16.16.dylib": [],
            "libfreetype.6.dylib": [
                (f"{thirdparty_prefix}/libpng16.16.dylib", "@loader_path/libpng16.16.dylib"),
                (f"{thirdparty_prefix}/libz.1.dylib", "@loader_path/libz.1.3.1.dylib"),
            ],
            "libz.1.3.1.dylib": [],
            "libjpeg.9.dylib": [],
            "libfontconfig.1.dylib": [
                (f"{thirdparty_prefix}/libfreetype.6.dylib", "@loader_path/libfreetype.6.dylib"),
            ],
            "libcurl.4.dylib": [],
            "libedit.0.dylib": [],
            "libvstdlib.dylib": [
                (f"{build_prefix}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib"),
            ],
            "libopus.0.dylib": [],
        }

        for lib_name, changes in link_fixes.items():
            lib_path = bin_dir / lib_name
            if not lib_path.exists():
                continue
            self._run_command([
                "install_name_tool", "-id", f"@loader_path/{lib_name}", lib_name
            ], cwd=bin_dir)
            for old_path, new_path in changes:
                self._run_command([
                    "install_name_tool", "-change", old_path, new_path, lib_name
                ], cwd=bin_dir)

    def _fix_source_game_links(self, game_path: Path, game_name: str):
        self.log(f"Fixing source game links for {game_name}...")
        bin_dir = game_path / game_name / "bin"
        if not bin_dir.exists():
            return

        working_dir = self._context.working_dir
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

    def _cleanup(self):
        self.log("Cleaning up...")
        working_dir = self._context.working_dir
        if working_dir.exists():
            shutil.rmtree(working_dir)

    def _run_command(self, cmd: list[str], cwd: Path | None = None,
                     capture: bool = False) -> subprocess.CompletedProcess:
        if self._stopped:
            raise RuntimeError("Patching stopped by user")

        self.log(f"Running: {' '.join(cmd)}")
        env = os.environ.copy()
        venv_bin = str(self._context.working_dir / "venv" / "bin")
        env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

        self._current_process = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
        )

        try:
            stdout, stderr = self._current_process.communicate()
            retcode = self._current_process.poll()
            if retcode and retcode != 0:
                raise subprocess.CalledProcessError(retcode, cmd, output=stdout, stderr=stderr)
            return subprocess.CompletedProcess(self._current_process.args, retcode, stdout, stderr)
        finally:
            self._current_process = None
