from patcher.core import Component, FetchStepConfig, Game, PatchMode
from patcher.core.pipeline import BaseStep, step


@step("git-fetcher")
class GitFetcher(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: FetchStepConfig):
        target_dir_name = step_config.patch_dir_name
        self.patcher.log(f"Preparing {target_dir_name}...")
        target_dir = self.patcher._context.working_dir / target_dir_name

        if target_dir.exists():
            self.patcher.log(f"Directory {target_dir_name} already exists. Skipping fetch.")
            return

        ref_to_checkout = step_config.branch
        if step_config.force_stable or self.patcher._context.patch_mode == PatchMode.STABLE:
            ref_to_checkout = step_config.stable_commit

        cmd = ["git", "clone", "--recursive"]

        is_hash = False
        if ref_to_checkout and len(ref_to_checkout) in (7, 40) and all(
                c in "0123456789abcdefABCDEF" for c in ref_to_checkout):
            is_hash = True

        if not is_hash:
            cmd.extend(["--shallow-submodules", "--depth", "1"])
            if ref_to_checkout:
                cmd.extend(["-b", ref_to_checkout])

        cmd.extend([step_config.url, str(target_dir)])
        self.patcher.executor.run(cmd)

        if ref_to_checkout and is_hash:
            self.patcher.log(f"Checking out {ref_to_checkout}...")
            self.patcher.executor.run(["git", "checkout", ref_to_checkout], cwd=target_dir)
            self.patcher.log("Updating submodules...")
            self.patcher.executor.run(["git", "submodule", "update", "--init", "--recursive"], cwd=target_dir)
