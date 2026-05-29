from __future__ import annotations

from patcher.core.pipeline import BaseBuilder


class CMakeBuilder(BaseBuilder):
    def __init__(self, patcher, target_dir_name: str):
        super().__init__(patcher)
        self.target_dir_name = target_dir_name

    def build(self):
        self.patcher.log(f"Building {self.target_dir_name}...")
        mod_dir = self.patcher._context.working_dir / self.target_dir_name
        venv_python = str(self.patcher._context.working_dir / "venv" / "bin" / "python3")

        self.patcher.executor.run([venv_python, "build_deps.py"], cwd=mod_dir)
        self.patcher.executor.run([venv_python, "-m", "cmake", "-S", ".", "-B", "build"], cwd=mod_dir)
        self.patcher.executor.run([venv_python, "-m", "cmake", "--build", "build", "--config", "Release"],
                                  cwd=mod_dir)

        output_dir = mod_dir / "output"
        self.patcher.executor.run([venv_python, "-m", "cmake", "--install", "build", "--prefix", str(output_dir)],
                                  cwd=mod_dir)
