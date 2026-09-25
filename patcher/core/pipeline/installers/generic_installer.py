import shutil

from patcher.core.models import Component, Game, InstallStepConfig
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step


@step("generic-installer")
class GenericInstaller(BaseStep):
    interruptible = False

    def execute(self, game: Game, comp: Component, step_config: InstallStepConfig):
        target_dir_name = step_config.patch_dir_name
        self.patcher.log(f"Installing {target_dir_name}...")
        output_dir = self.patcher._context.working_dir / target_dir_name / "output"
        shutil.copytree(output_dir, game.path, dirs_exist_ok=True)
