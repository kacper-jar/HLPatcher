from __future__ import annotations

from patcher.core import PatchMode
from patcher.core.pipeline import BaseFetcher


class GitFetcher(BaseFetcher):
    def __init__(
            self,
            patcher,
            target_dir_name: str,
            repo_url: str,
            ref: str,
            stable_commit: str,
            force_stable: bool = False,
    ):
        super().__init__(patcher)
        self.target_dir_name = target_dir_name
        self.repo_url = repo_url
        self.ref = ref
        self.stable_commit = stable_commit
        self.force_stable = force_stable

    def fetch(self):
        self.patcher.log(f"Preparing {self.target_dir_name}...")
        target_dir = self.patcher._context.working_dir / self.target_dir_name

        ref_to_checkout = self.ref
        if self.force_stable or self.patcher._context.patch_mode == PatchMode.STABLE:
            ref_to_checkout = self.stable_commit

        cmd = ["git", "clone", "--recursive"]

        is_hash = False
        if ref_to_checkout and len(ref_to_checkout) in (7, 40) and all(
                c in "0123456789abcdefABCDEF" for c in ref_to_checkout):
            is_hash = True

        if not is_hash:
            cmd.extend(["--shallow-submodules", "--depth", "1"])
            if ref_to_checkout:
                cmd.extend(["-b", ref_to_checkout])

        cmd.extend([self.repo_url, str(target_dir)])
        self.patcher.executor.run(cmd)

        if ref_to_checkout and is_hash:
            self.patcher.log(f"Checking out {ref_to_checkout}...")
            self.patcher.executor.run(["git", "checkout", ref_to_checkout], cwd=target_dir)
            self.patcher.log("Updating submodules...")
            self.patcher.executor.run(["git", "submodule", "update", "--init", "--recursive"], cwd=target_dir)
