from __future__ import annotations

import shutil
from pathlib import Path

from patcher.core.pipeline.fetchers import GitFetcher


class GoldSrcEngineFetcher(GitFetcher):
    def fetch(self):
        super().fetch()

        working_dir = self.patcher._context.working_dir
        xash_dir = working_dir / self.target_dir_name

        sdl_dmg = working_dir / "SDL2-2.32.10.dmg"
        self.patcher._run_command([
            "curl", "-L", "-o", str(sdl_dmg),
            "https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-2.32.10.dmg",
        ])

        info_result = self.patcher._run_command(["hdiutil", "info"], capture=True)
        for line in info_result.stdout.replace("\\n", "\n").splitlines():
            if "/Volumes/SDL2" in line:
                stale_mount = line.split("\t")[-1].strip()
                self.patcher._run_command(["hdiutil", "detach", stale_mount])

        result = self.patcher._run_command(["hdiutil", "attach", str(sdl_dmg), "-nobrowse"], capture=True)
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
                self.patcher._run_command(["hdiutil", "detach", mount_point])
