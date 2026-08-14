from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


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


@dataclass
class BuildStepConfig(StepConfig):
    patch_dir_name: str = ""
    build_args: list[str] = field(default_factory=list)
    waf_game: str = ""


@dataclass
class InstallStepConfig(StepConfig):
    patch_dir_name: str = ""


@dataclass
class Component:
    name: str
    subfolder: str
    engine_type: EngineType
    status: PatchStatus
    steps: list[StepConfig] = field(default_factory=list)
    estimated_patch_time: int = 0
    estimated_free_space_required: int = 0

    @property
    def needs_patch(self) -> bool:
        return self.status == PatchStatus.NEEDS_PATCH


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
class UpdateInfo:
    latest_version: str
    update_available: bool
    release_url: str
