import shutil
import urllib.request
from pathlib import Path

from patcher.core import Component, FetchStepConfig, Game
from patcher.core.pipeline import BaseStep, step


@step("url-fetcher")
class UrlFetcherStep(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: FetchStepConfig):
        self.patcher.log(f"Downloading from {step_config.url}")

        patch_dir = self.patcher._context.working_dir / step_config.patch_dir_name
        patch_dir.mkdir(parents=True, exist_ok=True)

        archive_path = patch_dir / "archive.tmp"

        (patch_dir / "url.txt").write_text(step_config.url)

        req = urllib.request.Request(
            step_config.url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req) as response, open(archive_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
