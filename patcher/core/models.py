from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from patcher.core.command_executor import CommandExecutor


class EngineType(Enum):
    GOLDSRC = "GoldSrc"
    SOURCE = "Source"


class PatchMode(Enum):
    LATEST = "Latest"
    STABLE = "Stable"


@dataclass
class AppConfig:
    debug: bool = False


class PatchStatus(Enum):
    NEEDS_PATCH = "Needs patching"
    ALREADY_PATCHED = "Already patched"


@dataclass
class StepConfig:
    type: str


@dataclass
class FetchStepConfig(StepConfig):
    url: str = ""
    patch_dir_name: str = ""
    branch: str = ""
    stable_commit: str = ""
    force_stable: bool = False


@dataclass
class PatchStepConfig(StepConfig):
    patch_dir_name: str = ""
    patch_container: str = ""


@dataclass
class BuildStepConfig(StepConfig):
    patch_dir_name: str = ""
    build_args: list[str] = field(default_factory=list)
    waf_game: str = ""


@dataclass
class InstallStepConfig(StepConfig):
    patch_dir_name: str = ""


@dataclass
class VpkExtractStepConfig(StepConfig):
    vpk_path: str = ""
    files: list[str] = field(default_factory=list)
    output_dir: str = ""


@dataclass
class ArchiveInstallStepConfig(InstallStepConfig):
    output_dir: str = ""
    file_pattern: str = ""


@dataclass
class Component:
    name: str
    subfolder: str
    engine_type: EngineType
    status: PatchStatus
    downgrade_group: str = ""
    downgrade_requires: dict[str, str] = field(default_factory=dict)
    steps: list[StepConfig] = field(default_factory=list)
    estimated_patch_time: int = 0
    estimated_free_space_required: int = 0
    id: str = ""
    depends_on: list[str] = field(default_factory=list)
    auto_select: bool = False

    @property
    def needs_patch(self) -> bool:
        return self.status == PatchStatus.NEEDS_PATCH


@dataclass
class GameConfig:
    id: str
    folder: str
    executable: str
    engine_type: EngineType
    fallback_marker: str = ""


@dataclass
class Game:
    name: str
    path: Path
    engine_type: EngineType
    components: list[Component] = field(default_factory=list)

    @property
    def needs_patch(self) -> bool:
        return any(c.needs_patch for c in self.components)

    @property
    def all_patched(self) -> bool:
        return all(not c.needs_patch for c in self.components)

    @property
    def has_source_components(self) -> bool:
        return any(c.engine_type == EngineType.SOURCE for c in self.components)


@dataclass
class PatchContext:
    steam_library_path: Path = field(default_factory=Path)
    working_dir: Path = field(default_factory=lambda: Path("/tmp/HLPatcher"))
    script_dir: Path = field(default_factory=Path)
    patch_mode: PatchMode = PatchMode.LATEST
    create_backup: bool = False
    games: list[Game] = field(default_factory=list)
    selected_components: list[Component] = field(default_factory=list)


@dataclass
class StepContext:
    working_dir: Path
    script_dir: Path
    steam_library_path: Path
    patch_mode: PatchMode
    executor: CommandExecutor
    log: Callable[[str], None]
    applied_patch_containers: set[tuple[str, str]] = field(default_factory=set)


@dataclass
class UpdateInfo:
    latest_version: str
    update_available: bool
    release_url: str


@dataclass
class GuideStepConfig:
    step_title: str
    step_description: str
    step_command: str = ""
    step_button_text: str = ""
    step_button_url: str = ""


@dataclass
class GuideConfig:
    title: str
    steps: list[GuideStepConfig] = field(default_factory=list)
