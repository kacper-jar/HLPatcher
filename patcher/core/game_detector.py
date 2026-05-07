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
        "estimated_time": 1,
    },
    {
        "name": "Half-Life",
        "subfolder": "valve",
        "repo_url": "https://github.com/FWGS/hlsdk-portable",
        "repo_branch": "hlfixed",
        "stable_commit": "78bc253",
        "build_system": "waf",
        "estimated_time": 1,
    },
    {
        "name": "Half-Life: Opposing Force",
        "subfolder": "gearbox",
        "repo_url": "https://github.com/FWGS/hlsdk-portable",
        "repo_branch": "opforfixed",
        "stable_commit": "654d15c",
        "build_system": "waf",
        "estimated_time": 1,
    },
    {
        "name": "Half-Life: Blue Shift",
        "subfolder": "bshift",
        "repo_url": "https://github.com/FWGS/hlsdk-portable",
        "repo_branch": "bshift",
        "stable_commit": "df5c272",
        "build_system": "waf",
        "estimated_time": 1,
    },
    {
        "name": "Deathmatch Classic",
        "subfolder": "dmc",
        "repo_url": "https://github.com/FWGS/hlsdk-portable",
        "repo_branch": "dmc",
        "stable_commit": "895b28d",
        "build_system": "waf",
        "estimated_time": 1,
    },
    {
        "name": "Counter-Strike",
        "subfolder": "cstrike",
        "repo_url": "https://github.com/Velaron/cs16-client.git",
        "repo_branch": "",
        "stable_commit": "123af8e",
        "build_system": "cmake",
        "patch_dir_name": "cs16-client",
        "estimated_time": 3,
    },
]

HL2_SOURCE_COMPONENTS = [
    {
        "name": "Half-Life 2",
        "subfolder": "hl2",
        "repo_url": "https://github.com/nillerusr/source-engine",
        "repo_branch": "",
        "stable_commit": "ed8209c",
        "build_system": "waf",
        "patch_dir_name": "source-engine",
        "waf_game": "hl2",
        "estimated_time": 3,
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
        "estimated_time": 3,
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
        "estimated_time": 3,
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
        "estimated_time": 3,
    },
]

PORTAL_SOURCE_COMPONENTS = [
    {
        "name": "Portal",
        "subfolder": "portal",
        "repo_url": "https://github.com/nillerusr/source-engine",
        "repo_branch": "",
        "stable_commit": "ed8209c",
        "build_system": "waf",
        "patch_dir_name": "source-engine",
        "waf_game": "portal",
        "estimated_time": 3,
    },
]

GOLDSRC_FOLDER_NAME = "Half-Life"
HL2_FOLDER_NAME = "Half-Life 2"
PORTAL_FOLDER_NAME = "Portal"


class GameDetector:
    def __init__(self, steam_library_path: Path):
        self._steam_library_path = steam_library_path

    def scan(self) -> list[Game]:
        games = []
        goldsrc_game = self._scan_goldsrc()
        if goldsrc_game:
            games.append(goldsrc_game)
        hl2_game = self._scan_hl2()
        if hl2_game:
            games.append(hl2_game)
        portal_game = self._scan_portal()
        if portal_game:
            games.append(portal_game)
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

    def _scan_hl2(self) -> Game | None:
        hl2_path = self._steam_library_path / HL2_FOLDER_NAME
        if not hl2_path.is_dir():
            logger.info(f"HL2 folder not found at {hl2_path}")
            return None

        if not (hl2_path / "hl2_osx").is_file():
            logger.info(f"hl2_osx not found in {hl2_path}")
            return None

        logger.info(f"Found HL2 installation at {hl2_path}")
        components = []

        for comp_def in HL2_SOURCE_COMPONENTS:
            component = self._check_source_component(hl2_path, comp_def)
            if component:
                components.append(component)

        if not components:
            return None

        return Game(
            name=f"Source ({HL2_FOLDER_NAME})",
            path=hl2_path,
            engine_type=EngineType.SOURCE,
            components=components,
        )

    def _scan_portal(self) -> Game | None:
        portal_path = self._steam_library_path / PORTAL_FOLDER_NAME
        if not portal_path.is_dir():
            logger.info(f"Portal folder not found at {portal_path}")
            return None

        if not (portal_path / "hl2_osx").is_file():
            logger.info(f"hl2_osx not found in {portal_path}")
            return None

        logger.info(f"Found Portal installation at {portal_path}")
        components = []

        for comp_def in PORTAL_SOURCE_COMPONENTS:
            component = self._check_source_component(portal_path, comp_def)
            if component:
                components.append(component)

        if not components:
            return None

        return Game(
            name=f"Source ({PORTAL_FOLDER_NAME})",
            path=portal_path,
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
            waf_game=comp_def.get("waf_game", ""),
            estimated_patch_time=comp_def.get("estimated_time", 0),
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
            waf_game=comp_def.get("waf_game", ""),
            estimated_patch_time=comp_def.get("estimated_time", 0),
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
