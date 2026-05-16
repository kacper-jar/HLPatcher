from __future__ import annotations

import shutil
from pathlib import Path

from patcher.core import EngineType, Game, PatchMode
from patcher.core.patcher import Patcher


class GoldSrcPatcher:
    def __init__(self, patcher: Patcher):
        self.patcher = patcher
        self.context = patcher._context

    def log(self, message: str):
        self.patcher.log(message)

    def _notify_component(self, name: str):
        self.patcher._notify_component(name)

    def _run_command(self, *args, **kwargs):
        return self.patcher._run_command(*args, **kwargs)

    def _get_ref(self, branch: str, stable_commit: str, force_stable: bool = False) -> str:
        if force_stable or self.context.patch_mode == PatchMode.STABLE:
            return stable_commit
        return branch

    def process(self, selected_games: list[Game]):
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
            self._prepare_engine()
            self._build_engine()
            self._install_engine(game.path)

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
            self.patcher._patch_generic("cs16-client")
            self._build_cstrike()
            self._install_generic("cs16-client", game.path)

    def _prepare_engine(self):
        self.log("Preparing GoldSrc Engine...")
        working_dir = self.context.working_dir
        xash_dir = working_dir / "xash3d-fwgs"
        self._run_command([
            "git", "clone", "--recursive",
            "https://github.com/FWGS/xash3d-fwgs",
            str(xash_dir),
        ])

        if self.context.patch_mode == PatchMode.STABLE:
            self._run_command(["git", "checkout", "d03ea4c"], cwd=xash_dir)

        sdl_dmg = working_dir / "SDL2-2.32.10.dmg"
        self._run_command([
            "curl", "-L", "-o", str(sdl_dmg),
            "https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-2.32.10.dmg",
        ])

        result = self._run_command(["hdiutil", "attach", str(sdl_dmg), "-nobrowse"], capture=True)
        mount_point = None
        for line in result.stdout.strip().split("\\n"):
            if "/Volumes/" in line:
                mount_point = line.split("\\t")[-1].strip()
                break

        if mount_point:
            sdl_dest = xash_dir / "3rdparty" / "SDL2.framework"
            shutil.copytree(Path(mount_point) / "SDL2.framework", sdl_dest, dirs_exist_ok=True)
            self._run_command(["hdiutil", "detach", mount_point])

    def _prepare_hlsdk_mod(self, suffix: str, ref: str):
        dir_name = f"hlsdk-portable-{suffix}"
        self.log(f"Preparing {dir_name}...")
        target_dir = self.context.working_dir / dir_name
        self._run_command([
            "git", "clone", "--recursive",
            "https://github.com/FWGS/hlsdk-portable",
            str(target_dir),
        ])
        self._run_command(["git", "checkout", ref], cwd=target_dir)

    def _prepare_cstrike(self):
        self.log("Preparing Counter-Strike...")
        target_dir = self.context.working_dir / "cs16-client"
        self._run_command([
            "git", "clone", "--recursive",
            "https://github.com/Velaron/cs16-client.git",
            str(target_dir),
        ])
        if self.context.patch_mode == PatchMode.STABLE:
            self._run_command(["git", "checkout", "123af8e"], cwd=target_dir)

    def _build_engine(self):
        self.log("Building GoldSrc Engine...")
        xash_dir = self.context.working_dir / "xash3d-fwgs"
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
        mod_dir = self.context.working_dir / dir_name
        output_dir = mod_dir / "output"
        self._run_command([
            "./waf", "configure", "-T", "release", "-8",
            "build", "install",
            f"--destdir={output_dir}",
        ], cwd=mod_dir)

    def _build_cstrike(self):
        self.log("Building Counter-Strike...")
        cs_dir = self.context.working_dir / "cs16-client"
        venv_python = str(self.context.working_dir / "venv" / "bin" / "python3")
        self._run_command([venv_python, "build_deps.py"], cwd=cs_dir)
        self._run_command([venv_python, "-m", "cmake", "-S", ".", "-B", "build"], cwd=cs_dir)
        self._run_command([venv_python, "-m", "cmake", "--build", "build", "--config", "Release"], cwd=cs_dir)
        output_dir = cs_dir / "output"
        self._run_command([venv_python, "-m", "cmake", "--install", "build", "--prefix", str(output_dir)], cwd=cs_dir)

    def _install_generic(self, dir_name: str, game_path: Path):
        self.log(f"Installing {dir_name}...")
        output_dir = self.context.working_dir / dir_name / "output"
        shutil.copytree(output_dir, game_path, dirs_exist_ok=True)

    def _install_engine(self, game_path: Path):
        self.log("Installing GoldSrc Engine...")
        xash_dir = self.context.working_dir / "xash3d-fwgs"
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
