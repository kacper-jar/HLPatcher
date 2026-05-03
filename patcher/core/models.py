from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EngineType(Enum):
    GOLDSRC = "GoldSrc"
    SOURCE = "Source"


class PatchMode(Enum):
    LATEST = "Latest"
    STABLE = "Stable"


class PatchStatus(Enum):
    NEEDS_PATCH = "Needs patching"
    ALREADY_PATCHED = "Already patched"


@dataclass
class Component:
    name: str
    subfolder: str
    engine_type: EngineType
    status: PatchStatus
    repo_url: str
    repo_branch: str = ""
    stable_commit: str = ""
    build_system: str = "waf"
    patch_dir_name: str = ""

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
