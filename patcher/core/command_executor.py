from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class CommandExecutor:
    def __init__(self, working_dir: Path, log_callback: Callable[[str], None] | None = None):
        self.working_dir = working_dir
        self.log_callback = log_callback
        self._stopped = False
        self._current_process: subprocess.Popen | None = None

    def stop(self):
        self._stopped = True
        if self._current_process:
            self._current_process.terminate()

    def log(self, message: str):
        logger.info(message)
        if self.log_callback:
            self.log_callback(message)

    def run(self, cmd: list[str], cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess:
        if self._stopped:
            raise RuntimeError("Execution stopped by user")

        self.log(f"Running: {' '.join(cmd)}")
        env = os.environ.copy()
        venv_bin = str(self.working_dir / "venv" / "bin")
        env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

        self._current_process = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
        )

        try:
            stdout, stderr = self._current_process.communicate()
            retcode = self._current_process.poll()
            if retcode and retcode != 0:
                raise subprocess.CalledProcessError(retcode, cmd, output=stdout, stderr=stderr)
            return subprocess.CompletedProcess(self._current_process.args, retcode, stdout, stderr)
        finally:
            self._current_process = None
