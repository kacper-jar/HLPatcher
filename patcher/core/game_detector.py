from __future__ import annotations

import logging
from pathlib import Path
from patcher.core import (
    Component, EngineType, Game, PatchStatus
)

logger = logging.getLogger(__name__)

GOLDSRC_COMPONENTS = [
    {
        "name": "GoldSrc Engine",
        "subfolder": "",
        "repo_url": "https://github.com/FWGS/xash3d-fwgs",
        "repo_branch": "",
        "stable_commit": "d03ea4c",
        "build_system": "waf",
    },
    {
        "name": "Half-Life",
        "subfolder": "valve",
        "repo_url": "https://github.com/FWGS/hlsdk-portable",
        "repo_branch": "hlfixed",
        "stable_commit": "78bc253",
        "build_system": "waf",
    },
    {
        "name": "Half-Life: Opposing Force",
        "subfolder": "gearbox",
        "repo_url": "https://github.com/FWGS/hlsdk-portable",
        "repo_branch": "opforfixed",
        "stable_commit": "654d15c",
        "build_system": "waf",
    },
    {
        "name": "Half-Life: Blue Shift",
        "subfolder": "bshift",
        "repo_url": "https://github.com/FWGS/hlsdk-portable",
        "repo_branch": "bshift",
        "stable_commit": "df5c272",
        "build_system": "waf",
    },
    {
        "name": "Deathmatch Classic",
        "subfolder": "dmc",
        "repo_url": "https://github.com/FWGS/hlsdk-portable",
        "repo_branch": "dmc",
        "stable_commit": "895b28d",
        "build_system": "waf",
    },
    {
        "name": "Counter-Strike",
        "subfolder": "cstrike",
        "repo_url": "https://github.com/Velaron/cs16-client.git",
        "repo_branch": "",
        "stable_commit": "123af8e",
        "build_system": "cmake",
        "patch_dir_name": "cs16-client",
    },
]

SOURCE_COMPONENTS = [
    {
        "name": "Half-Life 2",
        "subfolder": "hl2",
        "repo_url": "https://github.com/nillerusr/source-engine",
        "repo_branch": "",
        "stable_commit": "ed8209c",
        "build_system": "waf",
        "patch_dir_name": "source-engine",
        "waf_game": "hl2",
    },
    {
        "name": "Half-Life 2: Lost Coast",
        "subfolder": "lostcoast",
        "repo_url": "https://github.com/nillerusr/source-engine",
        "repo_branch": "",
        "stable_commit": "ed8209c",
        "build_system": "waf",
        "patch_dir_name": "source-engine",
        "waf_game": "hl2",
    },
    {
        "name": "Half-Life 2: Episodic (Episodes 1 & 2)",
        "subfolder": "episodic",
        "repo_url": "https://github.com/nillerusr/source-engine",
        "repo_branch": "",
        "stable_commit": "ed8209c",
        "build_system": "waf",
        "patch_dir_name": "source-engine",
        "waf_game": "episodic",
    },
    {
        "name": "Half-Life: Source",
        "subfolder": "hl1",
        "repo_url": "https://github.com/nillerusr/source-engine",
        "repo_branch": "",
        "stable_commit": "ed8209c",
        "build_system": "waf",
        "patch_dir_name": "source-engine",
        "waf_game": "hl1",
    },
]

GOLDSRC_FOLDER_NAME = "Half-Life"
SOURCE_FOLDER_NAME = "Half-Life 2"


class GameDetector:
    def __init__(self, steam_library_path: Path):
        self._steam_library_path = steam_library_path

    def scan(self) -> list[Game]:
        games = []
        goldsrc_game = self._scan_goldsrc()
        if goldsrc_game:
            games.append(goldsrc_game)
        source_game = self._scan_source()
        if source_game:
            games.append(source_game)
        return games

    def _scan_goldsrc(self) -> Game | None:
        goldsrc_path = self._steam_library_path / GOLDSRC_FOLDER_NAME
        if not goldsrc_path.is_dir():
            logger.info(f"GoldSrc folder not found at {goldsrc_path}")
            return None

        if not (goldsrc_path / "hl_osx").is_file():
            logger.info(f"hl_osx not found in {goldsrc_path}")
            return None

        logger.info(f"Found GoldSrc installation at {goldsrc_path}")
        components = []

        for comp_def in GOLDSRC_COMPONENTS:
            component = self._check_goldsrc_component(goldsrc_path, comp_def)
            if component:
                components.append(component)

        if not components:
            return None

        return Game(
            name=f"GoldSrc ({GOLDSRC_FOLDER_NAME})",
            path=goldsrc_path,
            engine_type=EngineType.GOLDSRC,
            components=components,
        )

    def _scan_source(self) -> Game | None:
        source_path = self._steam_library_path / SOURCE_FOLDER_NAME
        if not source_path.is_dir():
            logger.info(f"Source folder not found at {source_path}")
            return None

        if not (source_path / "hl2_osx").is_file():
            logger.info(f"hl2_osx not found in {source_path}")
            return None

        logger.info(f"Found Source installation at {source_path}")
        components = []

        for comp_def in SOURCE_COMPONENTS:
            component = self._check_source_component(source_path, comp_def)
            if component:
                components.append(component)

        if not components:
            return None

        return Game(
            name=f"Source ({SOURCE_FOLDER_NAME})",
            path=source_path,
            engine_type=EngineType.SOURCE,
            components=components,
        )

    def _check_goldsrc_component(self, game_path: Path, comp_def: dict) -> Component | None:
        subfolder = comp_def["subfolder"]

        if subfolder == "":
            status = self._detect_goldsrc_engine_status(game_path)
        else:
            component_path = game_path / subfolder
            if not component_path.is_dir():
                return None
            status = self._detect_goldsrc_mod_status(component_path)

        logger.info(f"{comp_def['name']} - {status.value}")
        return Component(
            name=comp_def["name"],
            subfolder=subfolder,
            engine_type=EngineType.GOLDSRC,
            status=status,
            repo_url=comp_def["repo_url"],
            repo_branch=comp_def.get("repo_branch", ""),
            stable_commit=comp_def.get("stable_commit", ""),
            build_system=comp_def.get("build_system", "waf"),
            patch_dir_name=comp_def.get("patch_dir_name", ""),
        )

    def _check_source_component(self, game_path: Path, comp_def: dict) -> Component | None:
        subfolder = comp_def["subfolder"]
        component_path = game_path / subfolder

        if not component_path.is_dir():
            return None

        status = self._detect_source_mod_status(component_path)
        logger.info(f"{comp_def['name']} - {status.value}")
        return Component(
            name=comp_def["name"],
            subfolder=subfolder,
            engine_type=EngineType.SOURCE,
            status=status,
            repo_url=comp_def["repo_url"],
            repo_branch=comp_def.get("repo_branch", ""),
            stable_commit=comp_def.get("stable_commit", ""),
            build_system=comp_def.get("build_system", "waf"),
            patch_dir_name=comp_def.get("patch_dir_name", ""),
        )

    def _detect_goldsrc_engine_status(self, game_path: Path) -> PatchStatus:
        required_files = [
            game_path / "libxash.dylib",
            game_path / "libmenu.dylib",
        ]
        required_dirs = [
            game_path / "SDL2.framework",
        ]
        if all(f.is_file() for f in required_files) and all(d.is_dir() for d in required_dirs):
            return PatchStatus.ALREADY_PATCHED
        return PatchStatus.NEEDS_PATCH

    def _detect_goldsrc_mod_status(self, component_path: Path) -> PatchStatus:
        dlls_path = component_path / "dlls"
        cl_dlls_path = component_path / "cl_dlls"

        for search_path in [dlls_path, cl_dlls_path]:
            if search_path.is_dir():
                for f in search_path.iterdir():
                    if f.name.endswith("_arm64.dylib") or f.name.endswith("_x86_64.dylib"):
                        return PatchStatus.ALREADY_PATCHED

        return PatchStatus.NEEDS_PATCH

    def _detect_source_mod_status(self, component_path: Path) -> PatchStatus:
        bin_path = component_path / "bin"
        if (bin_path / "libclient.dylib").is_file() and (bin_path / "libserver.dylib").is_file():
            return PatchStatus.ALREADY_PATCHED
        return PatchStatus.NEEDS_PATCH
