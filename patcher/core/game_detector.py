from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from patcher.core import (
    Component, EngineType, Game, PatchStatus
)
from patcher.core.config_loader import load_components_config

logger = logging.getLogger(__name__)

GOLDSRC_FOLDER_NAME = "Half-Life"
HL2_FOLDER_NAME = "Half-Life 2"
PORTAL_FOLDER_NAME = "Portal"


class GameDetector:
    def __init__(self, steam_library_path: Path):
        self._steam_library_path = steam_library_path
        self._components_config = load_components_config()

    def scan(self) -> list[Game]:
        games = []

        goldsrc_comps = [c for c in self._components_config if c.get("engine_type") == "GoldSrc"]
        goldsrc_game = self._scan_game(
            GOLDSRC_FOLDER_NAME,
            "hl_osx",
            EngineType.GOLDSRC,
            goldsrc_comps,
            self._check_goldsrc_component
        )
        if goldsrc_game:
            games.append(goldsrc_game)

        hl2_comps = [c for c in self._components_config if
                     c.get("engine_type") == "Source" and c.get("waf_game") != "portal"]
        hl2_game = self._scan_game(
            HL2_FOLDER_NAME,
            "hl2_osx",
            EngineType.SOURCE,
            hl2_comps,
            self._check_source_component
        )
        if hl2_game:
            games.append(hl2_game)

        portal_comps = [c for c in self._components_config if
                        c.get("engine_type") == "Source" and c.get("waf_game") == "portal"]
        portal_game = self._scan_game(
            PORTAL_FOLDER_NAME,
            "hl2_osx",
            EngineType.SOURCE,
            portal_comps,
            self._check_source_component
        )
        if portal_game:
            games.append(portal_game)

        return games

    def _scan_game(
            self,
            folder_name: str,
            executable_name: str,
            engine_type: EngineType,
            component_defs: list[dict],
            check_component_fn: Callable[[Path, dict], Component | None]
    ) -> Game | None:
        game_path = self._steam_library_path / folder_name
        if not game_path.is_dir():
            logger.info(f"{folder_name} folder not found at {game_path}")
            return None

        if not (game_path / executable_name).is_file():
            logger.info(f"{executable_name} not found in {game_path}")
            return None

        logger.info(f"Found {engine_type.value} installation at {game_path}")
        components = []

        for comp_def in component_defs:
            component = check_component_fn(game_path, comp_def)
            if component:
                components.append(component)

        if not components:
            return None

        engine_name = "GoldSrc" if engine_type == EngineType.GOLDSRC else "Source"
        return Game(
            name=f"{engine_name} ({folder_name})",
            path=game_path,
            engine_type=engine_type,
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
            patch_dir_name=comp_def.get("patch_dir_name", ""),
            waf_game=comp_def.get("waf_game", ""),
            fetcher=comp_def.get("fetcher", "git"),
            builder=comp_def.get("builder", "waf"),
            installer=comp_def.get("installer", "generic"),
            build_args=comp_def.get("build_args", []),
            force_stable=comp_def.get("force_stable", False),
            estimated_patch_time=comp_def.get("estimated_time", 0),
            estimated_free_space_required=comp_def.get("estimated_space", 0),
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
            patch_dir_name=comp_def.get("patch_dir_name", ""),
            waf_game=comp_def.get("waf_game", ""),
            fetcher=comp_def.get("fetcher", "git"),
            builder=comp_def.get("builder", "waf"),
            installer=comp_def.get("installer", "generic"),
            build_args=comp_def.get("build_args", []),
            force_stable=comp_def.get("force_stable", False),
            estimated_patch_time=comp_def.get("estimated_time", 0),
            estimated_free_space_required=comp_def.get("estimated_space", 0),
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
