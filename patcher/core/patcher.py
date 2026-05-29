from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from patcher.core import AppConfig, CommandExecutor, EngineType, Game, PatchContext, PatchMode

logger = logging.getLogger(__name__)


class Patcher:
    def __init__(self, context: PatchContext, config: AppConfig, log_callback: Callable[[str], None] | None = None,
                 component_callback: Callable[[str], None] | None = None):
        self._context = context
        self._config = config
        self._log_callback = log_callback
        self._component_callback = component_callback
        self.executor = CommandExecutor(self._context.working_dir, self._log_callback)

    def stop(self):
        self.executor.stop()

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

        games_to_backup = [g for g in selected_games if g.needs_patch]
        if not games_to_backup:
            return

        self.log("Creating backup...")
        date_str = datetime.now().strftime("%Y-%m-%d")
        for game in games_to_backup:
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
        self.executor.run(["python3", "-m", "venv", str(working_dir / "venv")])
        venv_pip = str(working_dir / "venv" / "bin" / "pip")
        self.executor.run([venv_pip, "install", "cmake", "ninja", "meson"])

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
            self.executor.run(["patch", "-p1", "-i", str(patch_file)], cwd=target_dir)

    def _cleanup(self):
        if self._config.debug:
            self.log("Debug mode: skipping cleanup")
            return
        self.log("Cleaning up...")
        working_dir = self._context.working_dir
        if working_dir.exists():
            shutil.rmtree(working_dir)
