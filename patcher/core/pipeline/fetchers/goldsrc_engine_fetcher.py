import shutil
from pathlib import Path

from patcher.core import Component, FetchStepConfig, Game
from patcher.core.pipeline import step
from patcher.core.pipeline.fetchers import GitFetcher


@step("goldsrc-engine-fetcher")
class GoldSrcEngineFetcher(GitFetcher):
    def execute(self, game: Game, comp: Component, step_config: FetchStepConfig):
        target_dir_name = step_config.patch_dir_name
        working_dir = self.patcher._context.working_dir
        xash_dir = working_dir / target_dir_name

        if xash_dir.exists():
            self.patcher.log(f"Directory {target_dir_name} already exists. Skipping fetch.")
            return

        super().execute(game, comp, step_config)

        sdl_dmg = working_dir / "SDL2-2.32.10.dmg"
        self.patcher.executor.run([
            "curl", "-L", "-o", str(sdl_dmg),
            "https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-2.32.10.dmg",
        ])

        info_result = self.patcher.executor.run(["hdiutil", "info"], capture=True)
        for line in info_result.stdout.replace("\\n", "\n").splitlines():
            if "/Volumes/SDL2" in line:
                stale_mount = line.split("\t")[-1].strip()
                self.patcher.executor.run(["hdiutil", "detach", stale_mount])

        result = self.patcher.executor.run(["hdiutil", "attach", str(sdl_dmg), "-nobrowse"], capture=True)
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
                self.patcher.executor.run(["hdiutil", "detach", mount_point])
