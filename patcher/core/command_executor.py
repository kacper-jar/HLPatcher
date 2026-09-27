import logging
import os
import subprocess
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class CommandExecutor:
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.interruptible = True
        self._stopped = False
        self._lock = threading.Lock()
        self._current_process: subprocess.Popen | None = None

    def stop(self):
        with self._lock:
            self._stopped = True
            process = self._current_process if self.interruptible else None
        if process:
            process.terminate()

    def raise_if_stopped(self):
        if self._stopped:
            raise RuntimeError("Execution stopped by user")

    def run(self, cmd: list[str], cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess:
        with self._lock:
            if self.interruptible:
                self.raise_if_stopped()

            logger.info(f"Running: {' '.join(cmd)}")
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
