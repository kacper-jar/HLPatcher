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
        return sum(1 for g in selected_games for c in g.components if c.needs_patch)

    def run(self, selected_games: list[Game]):
        try:
            self._create_backup(selected_games)
            self._prepare_environment()

            components_by_dir = {}
            for game in selected_games:
                for comp in game.components:
                    if comp.needs_patch:
                        if comp.patch_dir_name not in components_by_dir:
                            components_by_dir[comp.patch_dir_name] = []
                        components_by_dir[comp.patch_dir_name].append((game, comp))

            from patcher.core.pipeline.fetchers import GitFetcher, GoldSrcEngineFetcher
            from patcher.core.pipeline.builders import WafBuilder, CMakeBuilder
            from patcher.core.pipeline.installers import GenericInstaller, GoldSrcEngineInstaller, SourceInstaller

            for dir_name, game_comp_list in components_by_dir.items():
                for i, (game, comp) in enumerate(game_comp_list):
                    self._notify_component(comp.name)

                    if i == 0:
                        if comp.fetcher == "goldsrc_engine":
                            fetcher = GoldSrcEngineFetcher(
                                self, comp.patch_dir_name, comp.repo_url,
                                comp.repo_branch, comp.stable_commit, comp.force_stable
                            )
                        else:
                            fetcher = GitFetcher(
                                self, comp.patch_dir_name, comp.repo_url,
                                comp.repo_branch, comp.stable_commit, comp.force_stable
                            )
                        fetcher.fetch()

                        self._patch_generic(comp.patch_dir_name)

                    args = []
                    for arg in comp.build_args:
                        args.append(arg.format(
                            working_dir=str(self._context.working_dir),
                            waf_game=comp.waf_game
                        ))

                    if comp.builder == "cmake":
                        builder = CMakeBuilder(self, comp.patch_dir_name)
                    else:
                        builder = WafBuilder(self, comp.patch_dir_name, args)

                    builder.build()

                    if comp.installer == "goldsrc_engine":
                        installer = GoldSrcEngineInstaller(self, comp.patch_dir_name)
                        installer.install(game)
                    elif comp.installer == "source":
                        installer = SourceInstaller(self)
                        installer.install(game, subfolders=[comp.subfolder])
                    else:
                        installer = GenericInstaller(self, comp.patch_dir_name)
                        installer.install(game)

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
        patch_dir = self._context.script_dir / "data" / "fixes" / "src" / component_name
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
