import shutil

from patcher.core import Component, Game, InstallStepConfig
from patcher.core.pipeline import BaseStep, step


@step("generic-installer")
class GenericInstaller(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: InstallStepConfig):
        target_dir_name = step_config.patch_dir_name
        self.patcher.log(f"Installing {target_dir_name}...")
        output_dir = self.patcher._context.working_dir / target_dir_name / "output"
        shutil.copytree(output_dir, game.path, dirs_exist_ok=True)
