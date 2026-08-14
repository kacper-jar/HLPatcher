import subprocess

from patcher.core import Component, Game, PatchStepConfig
from patcher.core.pipeline import BaseStep, step


@step("patch")
class PatchStep(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: PatchStepConfig):
        target_dir_name = step_config.patch_dir_name

        if target_dir_name in self.patcher._patched_dirs:
            return

        self.patcher.log(f"Patching {target_dir_name}...")
        patch_dir = self.patcher._context.script_dir / "data" / "fixes" / "src" / target_dir_name
        target_dir = self.patcher._context.working_dir / target_dir_name

        if not patch_dir.is_dir():
            self.patcher.log(f"No patch directory found for {target_dir_name}")
            self.patcher._patched_dirs.add(target_dir_name)
            return

        patch_files = sorted(patch_dir.glob("*.patch"))
        if not patch_files:
            self.patcher.log(f"No patches found in {patch_dir}")
            self.patcher._patched_dirs.add(target_dir_name)
            return

        for patch_file in patch_files:
            self.patcher.log(f"Applying patch: {patch_file.name}")
            try:
                self.patcher.executor.run(["patch", "-p1", "--forward", "-i", str(patch_file)], cwd=target_dir)
            except subprocess.CalledProcessError:
                self.patcher.log(f"Warning: Patch {patch_file.name} failed to apply cleanly or was already applied.")

        self.patcher._patched_dirs.add(target_dir_name)
