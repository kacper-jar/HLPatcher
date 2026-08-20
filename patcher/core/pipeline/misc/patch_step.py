import subprocess

from patcher.core import Component, Game, PatchStepConfig
from patcher.core.pipeline import BaseStep, step


@step("patch")
class PatchStep(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: PatchStepConfig):
        target_dir_name = step_config.patch_dir_name
        patch_container = step_config.patch_container or f"{target_dir_name}-base"
        applied_key = (target_dir_name, patch_container)

        if applied_key in self.patcher.applied_containers:
            return

        self.patcher.log(f"Patching {target_dir_name} (container: {patch_container})...")
        patch_dir = self.patcher._context.script_dir / "data" / "fixes" / "src" / patch_container
        target_dir = self.patcher._context.working_dir / target_dir_name

        if not patch_dir.is_dir():
            self.patcher.log(f"No patch directory found for container {patch_container}")
            self.patcher.applied_containers.add(applied_key)
            return

        patch_files = sorted(patch_dir.glob("*.patch"))
        if not patch_files:
            self.patcher.log(f"No patches found in {patch_dir}")
            self.patcher.applied_containers.add(applied_key)
            return

        for patch_file in patch_files:
            self.patcher.log(f"Applying patch: {patch_file.name}")
            try:
                self.patcher.executor.run(["patch", "-p1", "--forward", "-i", str(patch_file)], cwd=target_dir)
            except subprocess.CalledProcessError:
                self.patcher.log(f"Warning: Patch {patch_file.name} failed to apply cleanly or was already applied.")

        self.patcher.applied_containers.add(applied_key)
