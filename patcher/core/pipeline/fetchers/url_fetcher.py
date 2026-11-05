import hashlib
import re
import tempfile
import urllib.request
from pathlib import Path

from patcher.core.models import Component, FetchStepConfig, Game
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step


def download_verified(url: str, destination: Path, sha256: str, raise_if_stopped):
    if not re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
        raise ValueError(f"Expected a 64-character SHA-256 checksum for {url}")

    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    digest = hashlib.sha256()
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=destination.parent) as temp_dir:
        temporary_path = Path(temp_dir) / destination.name
        raise_if_stopped()
        with urllib.request.urlopen(request, timeout=30) as response, temporary_path.open("wb") as output:
            while chunk := response.read(64 * 1024):
                raise_if_stopped()
                digest.update(chunk)
                output.write(chunk)
        raise_if_stopped()

        actual = digest.hexdigest()
        if actual != sha256.lower():
            raise ValueError(f"SHA-256 mismatch for {url}: expected {sha256}, got {actual}")
        temporary_path.replace(destination)


@step("url-fetcher", config=FetchStepConfig)
class UrlFetcherStep(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: FetchStepConfig):
        self.context.log(f"Downloading from {step_config.url}")

        patch_dir = self.context.working_dir / step_config.patch_dir_name
        download_verified(
            step_config.url, patch_dir / "archive.tmp", step_config.sha256,
            self.context.executor.raise_if_stopped,
        )
