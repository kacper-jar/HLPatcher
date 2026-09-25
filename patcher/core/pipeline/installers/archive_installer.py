import shutil
import tarfile
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from patcher.core.models import ArchiveInstallStepConfig, Component, Game
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step


@step("archive-installer")
class ArchiveInstallerStep(BaseStep):
    interruptible = False

    def execute(self, game: Game, comp: Component, step_config: ArchiveInstallStepConfig):
        self.patcher.log(f"Extracting archive from {step_config.patch_dir_name}")

        patch_dir = self.patcher._context.working_dir / step_config.patch_dir_name
        archive_path = patch_dir / "archive.tmp"

        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        url_file = patch_dir / "url.txt"
        original_url = url_file.read_text().strip() if url_file.exists() else ""

        with TemporaryDirectory() as temp_dir_name:
            extract_dir = Path(temp_dir_name) / "extracted"
            extract_dir.mkdir()

            if original_url.endswith(".zip") or "zip" in original_url:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(extract_dir)
            elif ".tar" in original_url or "tgz" in original_url:
                with tarfile.open(archive_path, "r") as tf:
                    tf.extractall(extract_dir)
            else:
                self.patcher.log("Unknown archive type, attempting zip and tar...")
                try:
                    with zipfile.ZipFile(archive_path, "r") as zf:
                        zf.extractall(extract_dir)
                except zipfile.BadZipFile:
                    with tarfile.open(archive_path, "r") as tf:
                        tf.extractall(extract_dir)

            output_base = game.path / step_config.output_dir
            output_base.mkdir(parents=True, exist_ok=True)

            pattern = step_config.file_pattern or "*"
            matched_files = list(extract_dir.rglob(pattern))

            if not matched_files:
                self.patcher.log(f"Warning: No files matched pattern '{pattern}' in the extracted archive.")

            for file_path in matched_files:
                if file_path.is_file():
                    self.patcher.log(f"Copying {file_path.name} to {output_base}")
                    shutil.copy2(file_path, output_base / file_path.name)
