import tarfile
import zipfile
from collections.abc import Iterator
from pathlib import Path, PurePosixPath

from patcher.core.models import ArchiveInstallStepConfig, Component, Game
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step


@step("archive-installer", config=ArchiveInstallStepConfig)
class ArchiveInstallerStep(BaseStep):
    interruptible = False

    def execute(self, game: Game, comp: Component, step_config: ArchiveInstallStepConfig):
        self.context.log(f"Extracting archive from {step_config.patch_dir_name}")

        archive_path = self.context.working_dir / step_config.patch_dir_name / "archive.tmp"
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        pattern = step_config.file_pattern or "*"
        files = {}
        for name, data in self._matching_files(archive_path, pattern):
            if name in files:
                raise ValueError(f"Archive {archive_path} has more than one file named {name}")
            files[name] = data
        if not files:
            raise ValueError(f"No files matching '{pattern}' in archive {archive_path}")

        output_base = game.path / step_config.output_dir
        output_base.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            self.context.log(f"Copying {name} to {output_base}")
            (output_base / name).write_bytes(data)

    def _matching_files(self, archive_path: Path, pattern: str) -> Iterator[tuple[str, bytes]]:
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path) as archive:
                for info in archive.infolist():
                    path = PurePosixPath(info.filename)
                    if not info.is_dir() and path.match(pattern):
                        yield path.name, archive.read(info)
        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as archive:
                for member in archive.getmembers():
                    path = PurePosixPath(member.name)
                    if member.isfile() and path.match(pattern):
                        yield path.name, archive.extractfile(member).read()
        else:
            raise ValueError(f"Unsupported archive format: {archive_path}")
