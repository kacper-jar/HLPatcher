from __future__ import annotations

from patcher.core.pipeline import BaseBuilder


class WafBuilder(BaseBuilder):
    def __init__(self, patcher, target_dir_name: str, configure_args: list[str]):
        super().__init__(patcher)
        self.target_dir_name = target_dir_name
        self.configure_args = configure_args

    def build(self):
        self.patcher.log(f"Building {self.target_dir_name}...")
        mod_dir = self.patcher._context.working_dir / self.target_dir_name
        output_dir = mod_dir / "output"

        cmd = ["./waf", "configure"] + self.configure_args + ["build", "install", f"--destdir={output_dir}"]
        self.patcher.executor.run(cmd, cwd=mod_dir)
