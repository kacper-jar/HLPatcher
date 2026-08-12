from __future__ import annotations

from patcher.core import Game, Component, BuildStepConfig
from patcher.core.pipeline import BaseStep, step


@step("waf-builder")
class WafBuilder(BaseStep):
    def execute(self, game: Game, comp: Component, step_config: BuildStepConfig):
        target_dir_name = step_config.patch_dir_name
        self.patcher.log(f"Building {target_dir_name}...")
        mod_dir = self.patcher._context.working_dir / target_dir_name
        output_dir = mod_dir / "output"

        args = []
        for arg in step_config.build_args:
            args.append(arg.format(
                working_dir=str(self.patcher._context.working_dir),
                waf_game=step_config.waf_game
            ))

        cmd = ["./waf", "configure"] + args + ["build", "install", f"--destdir={output_dir}"]
        self.patcher.executor.run(cmd, cwd=mod_dir)
