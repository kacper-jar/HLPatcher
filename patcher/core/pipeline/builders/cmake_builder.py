from patcher.core.models import BuildStepConfig, Component, Game
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step


@step("cmake-builder", config=BuildStepConfig)
class CMakeBuilder(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: BuildStepConfig):
        target_dir_name = step_config.patch_dir_name
        self.context.log(f"Building {target_dir_name}...")
        mod_dir = self.context.working_dir / target_dir_name
        venv_python = str(self.context.working_dir / "venv" / "bin" / "python3")

        self.context.executor.run([venv_python, "build_deps.py"], cwd=mod_dir)
        self.context.executor.run([venv_python, "-m", "cmake", "-S", ".", "-B", "build", "-G", "Ninja"], cwd=mod_dir)
        self.context.executor.run([venv_python, "-m", "cmake", "--build", "build", "--config", "Release"],
                                  cwd=mod_dir)

        output_dir = mod_dir / "output"
        self.context.executor.run([venv_python, "-m", "cmake", "--install", "build", "--prefix", str(output_dir)],
                                  cwd=mod_dir)
