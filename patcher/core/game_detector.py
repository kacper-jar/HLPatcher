import logging
from collections.abc import Callable
from pathlib import Path

from patcher.core.config_loader import load_components_config, load_games_config
from patcher.core.models import (
    BuildStepConfig,
    Component,
    EngineType,
    FetchStepConfig,
    Game,
    InstallStepConfig,
    PatchStatus,
    PatchStepConfig,
    ArchiveInstallStepConfig,
    VpkExtractStepConfig,
)

logger = logging.getLogger(__name__)


class GameDetector:
    def __init__(self, steam_library_path: Path):
        self._steam_library_path = steam_library_path
        self._games_config = load_games_config()
        self._components_config = load_components_config()
        self._validate_config()

    def _validate_config(self):
        game_ids = {g.id for g in self._games_config}
        unknown = [c["name"] for c in self._components_config if c.get("game") not in game_ids]
        if unknown:
            raise ValueError(f"Components with an unknown game: {', '.join(unknown)}")

        component_ids = [c["id"] for c in self._components_config]
        duplicates = sorted({i for i in component_ids if component_ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"Duplicate component ids: {', '.join(duplicates)}")

        broken = [c["name"] for c in self._components_config
                  if any(dep not in component_ids for dep in c.get("depends_on", []))]
        if broken:
            raise ValueError(f"Components depending on unknown components: {', '.join(broken)}")

    def scan(self) -> list[Game]:
        games = []
        for game_config in self._games_config:
            engine_type = game_config.engine_type
            game = self._scan_game(
                game_config.folder,
                game_config.executable,
                engine_type,
                [c for c in self._components_config if c["game"] == game_config.id],
                self._check_goldsrc_component if engine_type == EngineType.GOLDSRC else self._check_source_component,
                fallback_marker=game_config.fallback_marker,
            )
            if game:
                games.append(game)
        return games

    def _scan_game(
            self,
            folder_name: str,
            executable_name: str,
            engine_type: EngineType,
            component_defs: list[dict],
            check_component_fn: Callable[[Path, dict], Component | None],
            fallback_marker: str | None = None
    ) -> Game | None:
        game_path = self._steam_library_path / folder_name
        if not game_path.is_dir():
            logger.info(f"{folder_name} folder not found at {game_path}")
            return None

        if not (game_path / executable_name).is_file():
            if not fallback_marker:
                logger.info(f"{executable_name} not found in {game_path}")
                return None

            fallback_found = False
            for comp_def in component_defs:
                subfolder = comp_def.get("subfolder", "")
                if subfolder and (game_path / subfolder / fallback_marker).is_file():
                    fallback_found = True
                    break

            if not fallback_found:
                logger.info(f"{executable_name} and {fallback_marker} not found in {game_path}")
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
            id=comp_def["id"],
            name=comp_def["name"],
            subfolder=subfolder,
            engine_type=EngineType.GOLDSRC,
            status=status,
            downgrade_group=comp_def.get("downgrade_group", ""),
            steps=self._parse_steps(comp_def.get("steps", [])),
            downgrade_requires=comp_def.get("downgrade_requires", {}),
            depends_on=comp_def.get("depends_on", []),
            auto_select=comp_def.get("auto_select", False),
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
            id=comp_def["id"],
            name=comp_def["name"],
            subfolder=subfolder,
            engine_type=EngineType.SOURCE,
            status=status,
            downgrade_group=comp_def.get("downgrade_group", ""),
            steps=self._parse_steps(comp_def.get("steps", [])),
            downgrade_requires=comp_def.get("downgrade_requires", {}),
            depends_on=comp_def.get("depends_on", []),
            auto_select=comp_def.get("auto_select", False),
            estimated_patch_time=comp_def.get("estimated_time", 0),
            estimated_free_space_required=comp_def.get("estimated_space", 0),
        )

    def _parse_steps(self, steps_def: list[dict]) -> list:
        parsed_steps = []
        for step in steps_def:
            step_type = step.get("type", "")
            if step_type.endswith("-fetcher"):
                parsed_steps.append(FetchStepConfig(
                    type=step_type,
                    url=step.get("url", ""),
                    patch_dir_name=step.get("patch_dir_name", ""),
                    branch=step.get("branch", ""),
                    stable_commit=step.get("stable_commit", ""),
                    force_stable=step.get("force_stable", False)
                ))
            elif step_type == "patch":
                parsed_steps.append(PatchStepConfig(
                    type=step_type,
                    patch_dir_name=step.get("patch_dir_name", "")
                ))
            elif step_type.endswith("-builder"):
                parsed_steps.append(BuildStepConfig(
                    type=step_type,
                    patch_dir_name=step.get("patch_dir_name", ""),
                    build_args=step.get("build_args", []),
                    waf_game=step.get("waf_game", "")
                ))
            elif step_type == "vpk-extractor":
                parsed_steps.append(VpkExtractStepConfig(
                    type=step_type,
                    vpk_path=step.get("vpk_path", ""),
                    files=step.get("files", []),
                    output_dir=step.get("output_dir", "")
                ))
            elif step_type == "archive-installer":
                parsed_steps.append(ArchiveInstallStepConfig(
                    type=step_type,
                    patch_dir_name=step.get("patch_dir_name", ""),
                    output_dir=step.get("output_dir", ""),
                    file_pattern=step.get("file_pattern", "")
                ))
            else:
                parsed_steps.append(InstallStepConfig(
                    type=step_type,
                    patch_dir_name=step.get("patch_dir_name", "")
                ))
        return parsed_steps

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
