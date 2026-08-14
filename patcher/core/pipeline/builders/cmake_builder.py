from patcher.core import BuildStepConfig, Component, Game
from patcher.core.pipeline import BaseStep, step


@step("cmake-builder")
class CMakeBuilder(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: BuildStepConfig):
        target_dir_name = step_config.patch_dir_name
        self.patcher.log(f"Building {target_dir_name}...")
        mod_dir = self.patcher._context.working_dir / target_dir_name
        venv_python = str(self.patcher._context.working_dir / "venv" / "bin" / "python3")

        self.patcher.executor.run([venv_python, "build_deps.py"], cwd=mod_dir)
        self.patcher.executor.run([venv_python, "-m", "cmake", "-S", ".", "-B", "build", "-G", "Ninja"], cwd=mod_dir)
        self.patcher.executor.run([venv_python, "-m", "cmake", "--build", "build", "--config", "Release"],
                                  cwd=mod_dir)

        output_dir = mod_dir / "output"
        self.patcher.executor.run([venv_python, "-m", "cmake", "--install", "build", "--prefix", str(output_dir)],
                                  cwd=mod_dir)
