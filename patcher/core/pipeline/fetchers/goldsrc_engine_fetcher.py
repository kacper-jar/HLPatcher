import shutil
import tempfile
from pathlib import Path

from patcher.core.models import Component, FetchStepConfig, Game
from patcher.core.pipeline.fetchers.git_fetcher import GitFetcher
from patcher.core.pipeline.fetchers.url_fetcher import download_verified
from patcher.core.pipeline.registry import step

SDL_DMG = "SDL2-2.32.10.dmg"
SDL_URL = f"https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/{SDL_DMG}"
SDL_SHA256 = "4a7ac31640d70214e848f994be8a12849c0f97918a7e6c2e27a40036166d1a7f"


@step("goldsrc-engine-fetcher", config=FetchStepConfig)
class GoldSrcEngineFetcher(GitFetcher):
    def execute(self, game: Game, comp: Component, step_config: FetchStepConfig):
        target_dir_name = step_config.patch_dir_name
        working_dir = self.context.working_dir
        xash_dir = working_dir / target_dir_name
        sdl_dest = xash_dir / "3rdparty" / "SDL2.framework"

        if sdl_dest.is_dir():
            self.context.log(f"SDL2.framework already exists in {target_dir_name}. Skipping fetch.")
            return

        super().execute(game, comp, step_config)

        with tempfile.TemporaryDirectory(dir=working_dir) as temp_dir:
            sdl_dmg = Path(temp_dir) / SDL_DMG
            self.context.log(f"Downloading from {SDL_URL}")
            download_verified(SDL_URL, sdl_dmg, SDL_SHA256, self.context.executor.raise_if_stopped)

            with tempfile.TemporaryDirectory(prefix="HLPatcher-SDL2-", ignore_cleanup_errors=True) as mount_point:
                self.context.executor.run(["hdiutil", "attach", str(sdl_dmg), "-nobrowse", "-readonly",
                                           "-mountpoint", mount_point])
                staged_framework = Path(temp_dir) / "SDL2.framework"
                try:
                    shutil.copytree(Path(mount_point) / "SDL2.framework", staged_framework)
                finally:
                    self.context.executor.run(["hdiutil", "detach", mount_point])

            sdl_dest.parent.mkdir(parents=True, exist_ok=True)
            staged_framework.replace(sdl_dest)
