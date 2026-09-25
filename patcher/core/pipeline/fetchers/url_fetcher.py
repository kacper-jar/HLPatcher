import urllib.request

from patcher.core.models import Component, FetchStepConfig, Game
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step


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

        with urllib.request.urlopen(req, timeout=30) as response, open(archive_path, "wb") as out_file:
            while chunk := response.read(64 * 1024):
                self.patcher.executor.raise_if_stopped()
                out_file.write(chunk)
