import subprocess
from pathlib import Path

from patcher.core.models import Component, Game, PatchStepConfig
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step


@step("patch")
class PatchStep(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: PatchStepConfig):
        target_dir_name = step_config.patch_dir_name
        patch_container = step_config.patch_container or f"{target_dir_name}-base"
        applied_key = (target_dir_name, patch_container)

        if applied_key in self.context.applied_patch_containers:
            return

        self.context.log(f"Patching {target_dir_name} (container: {patch_container})...")
        patch_dir = self.context.script_dir / "data" / "fixes" / "src" / patch_container
        target_dir = self.context.working_dir / target_dir_name

        if not patch_dir.is_dir():
            self.context.log(f"No patch directory found for container {patch_container}")
            self.context.applied_patch_containers.add(applied_key)
            return

        patch_files = sorted(patch_dir.glob("*.patch"))
        if not patch_files:
            self.context.log(f"No patches found in {patch_dir}")
            self.context.applied_patch_containers.add(applied_key)
            return

        for patch_file in patch_files:
            if self._is_already_applied(patch_file, target_dir):
                self.context.log(f"Patch {patch_file.name} is already applied, skipping")
                continue

            self.context.log(f"Applying patch: {patch_file.name}")
            try:
                self.context.executor.run(["patch", "-p1", "--forward", "--batch", "-i", str(patch_file)],
                                          cwd=target_dir)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Patch {patch_file.name} failed to apply to {target_dir_name}") from e

        self.context.applied_patch_containers.add(applied_key)

    def _is_already_applied(self, patch_file: Path, target_dir: Path) -> bool:
        try:
            self.context.executor.run(["patch", "-p1", "--reverse", "--dry-run", "--force", "-i", str(patch_file)],
                                      cwd=target_dir, capture=True)
        except subprocess.CalledProcessError:
            return False
        return True
