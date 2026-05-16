from __future__ import annotations

import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable

from patcher.core import AppConfig, EngineType, Game, PatchContext, PatchMode

logger = logging.getLogger(__name__)


class Patcher:
    def __init__(self, context: PatchContext, config: AppConfig, log_callback: Callable[[str], None] | None = None,
                 component_callback: Callable[[str], None] | None = None):
        self._context = context
        self._config = config
        self._log_callback = log_callback
        self._component_callback = component_callback
        self._stopped = False
        self._current_process: subprocess.Popen | None = None

    def stop(self):
        self._stopped = True
        if self._current_process:
            self._current_process.terminate()

    def log(self, message: str):
        logger.info(message)
        if self._log_callback:
            self._log_callback(message)

    def _notify_component(self, name: str):
        if self._component_callback:
            self._component_callback(name)

    def get_total_steps(self, selected_games: list[Game]) -> int:
        steps = 0
        goldsrc_games = [g for g in selected_games if g.engine_type == EngineType.GOLDSRC]
        if goldsrc_games:
            game = goldsrc_games[0]
            selected_comps = [c for c in game.components if c.needs_patch]
            unique_subfolders = {c.subfolder for c in selected_comps}
            steps += len(unique_subfolders)

        source_games = [g for g in selected_games if g.engine_type == EngineType.SOURCE]
        if source_games:
            waf_games = set()
            has_any_source_patch = False
            for game in source_games:
                selected_comps = [c for c in game.components if c.needs_patch]
                if selected_comps:
                    has_any_source_patch = True
                    for comp in selected_comps:
                        if comp.waf_game:
                            waf_games.add(comp.waf_game)

            if has_any_source_patch:
                steps += 1
                steps += len(waf_games)

        return steps

    def run(self, selected_games: list[Game]):
        try:
            self._create_backup(selected_games)
            self._prepare_environment()

            from patcher.core import GoldSrcPatcher, SourcePatcher

            GoldSrcPatcher(self).process(selected_games)
            SourcePatcher(self).process(selected_games)

            self._cleanup()
        except Exception as e:
            logger.error(f"Patching failed: {e}")
            raise

    def _create_backup(self, selected_games: list[Game]):
        if not self._context.create_backup:
            self.log("Skipping backup creation")
            return

        self.log("Creating backup...")
        date_str = datetime.now().strftime("%Y-%m-%d")
        for game in selected_games:
            backup_dest = Path.home() / "Documents" / f"{game.name} backup ({date_str})"
            self.log(f"Backing up {game.path} to {backup_dest}")
            shutil.copytree(game.path, backup_dest, dirs_exist_ok=True)
        self.log("Backup complete")

    def _prepare_environment(self):
        self.log("Preparing environment...")
        working_dir = self._context.working_dir
        if working_dir.exists():
            shutil.rmtree(working_dir)
        working_dir.mkdir(parents=True)

        self.log("Setting up Python venv for build tools...")
        self._run_command(["python3", "-m", "venv", str(working_dir / "venv")])
        venv_pip = str(working_dir / "venv" / "bin" / "pip")
        self._run_command([venv_pip, "install", "cmake", "ninja", "meson"])

    def _patch_generic(self, component_name: str):
        self.log(f"Patching {component_name}...")
        patch_dir = self._context.script_dir / "fixes" / "src" / component_name
        target_dir = self._context.working_dir / component_name

        if not patch_dir.is_dir():
            self.log(f"No patch directory found for {component_name}")
            return

        patch_files = sorted(patch_dir.glob("*.patch"))
        for patch_file in patch_files:
            self.log(f"Applying patch: {patch_file.name}")
            self._run_command(["patch", "-p1", "-i", str(patch_file)], cwd=target_dir)

    def _cleanup(self):
        if self._config.debug:
            self.log("Debug mode: skipping cleanup")
            return
        self.log("Cleaning up...")
        working_dir = self._context.working_dir
        if working_dir.exists():
            shutil.rmtree(working_dir)

    def _run_command(self, cmd: list[str], cwd: Path | None = None,
                     capture: bool = False) -> subprocess.CompletedProcess:
        if self._stopped:
            raise RuntimeError("Patching stopped by user")

        self.log(f"Running: {' '.join(cmd)}")
        env = os.environ.copy()
        venv_bin = str(self._context.working_dir / "venv" / "bin")
        env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

        self._current_process = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
        )

        try:
            stdout, stderr = self._current_process.communicate()
            retcode = self._current_process.poll()
            if retcode and retcode != 0:
                raise subprocess.CalledProcessError(retcode, cmd, output=stdout, stderr=stderr)
            return subprocess.CompletedProcess(self._current_process.args, retcode, stdout, stderr)
        finally:
            self._current_process = None
