import shutil
from pathlib import Path

from patcher.core.models import Component, FetchStepConfig, Game
from patcher.core.pipeline.fetchers.git_fetcher import GitFetcher
from patcher.core.pipeline.registry import step


@step("goldsrc-engine-fetcher", config=FetchStepConfig)
class GoldSrcEngineFetcher(GitFetcher):
    def execute(self, game: Game, comp: Component, step_config: FetchStepConfig):
        target_dir_name = step_config.patch_dir_name
        working_dir = self.context.working_dir
        xash_dir = working_dir / target_dir_name

        if xash_dir.exists():
            self.context.log(f"Directory {target_dir_name} already exists. Skipping fetch.")
            return

        super().execute(game, comp, step_config)

        sdl_dmg = working_dir / "SDL2-2.32.10.dmg"
        self.context.executor.run([
            "curl", "-L", "-o", str(sdl_dmg),
            "https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-2.32.10.dmg",
        ])

        info_result = self.context.executor.run(["hdiutil", "info"], capture=True)
        for line in info_result.stdout.replace("\\n", "\n").splitlines():
            if "/Volumes/SDL2" in line:
                stale_mount = line.split("\t")[-1].strip()
                self.context.executor.run(["hdiutil", "detach", stale_mount])

        result = self.context.executor.run(["hdiutil", "attach", str(sdl_dmg), "-nobrowse"], capture=True)
        mount_point = None
        for line in result.stdout.replace("\\n", "\n").splitlines():
            if "/Volumes/" in line:
                mount_point = line.split("\t")[-1].strip()
                break

        if mount_point:
            try:
                sdl_dest = xash_dir / "3rdparty" / "SDL2.framework"
                shutil.copytree(Path(mount_point) / "SDL2.framework", sdl_dest, dirs_exist_ok=True)
            finally:
                self.context.executor.run(["hdiutil", "detach", mount_point])
