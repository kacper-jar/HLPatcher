import re
from pathlib import Path

from patcher.core.models import Component, FetchStepConfig, Game, PatchMode
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step

FULL_COMMIT = re.compile(r"[0-9a-f]{40}")


@step("git-fetcher", config=FetchStepConfig)
class GitFetcher(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: FetchStepConfig):
        target_dir_name = step_config.patch_dir_name
        self.context.log(f"Preparing {target_dir_name}...")
        target_dir = self.context.working_dir / target_dir_name

        if target_dir.exists():
            self.context.log(f"Directory {target_dir_name} already exists. Skipping fetch.")
            return

        if step_config.force_stable or self.context.patch_mode == PatchMode.STABLE:
            self._fetch_commit(step_config.url, step_config.stable_commit, target_dir)
        else:
            self._clone_branch(step_config.url, step_config.branch, target_dir)

    def _clone_branch(self, url: str, branch: str, target_dir: Path):
        cmd = ["git", "clone", "--recursive", "--shallow-submodules", "--depth", "1"]
        if branch:
            cmd.extend(["-b", branch])
        self.context.executor.run([*cmd, url, str(target_dir)])

    def _fetch_commit(self, url: str, commit: str, target_dir: Path):
        if not FULL_COMMIT.fullmatch(commit):
            raise ValueError(f"Stable commit {commit!r} for {url} is not a full 40-character commit hash")

        self.context.log(f"Fetching commit {commit}...")
        run = self.context.executor.run
        run(["git", "init", "--quiet", str(target_dir)])
        run(["git", "remote", "add", "origin", url], cwd=target_dir)
        run(["git", "fetch", "--depth", "1", "origin", commit], cwd=target_dir)
        run(["git", "checkout", "--quiet", "FETCH_HEAD"], cwd=target_dir)
        self.context.log("Updating submodules...")
        run(["git", "submodule", "update", "--init", "--recursive", "--depth", "1"], cwd=target_dir)
