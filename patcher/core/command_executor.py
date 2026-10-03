import atexit
import logging
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class CommandExecutor:
    _running: set[subprocess.Popen] = set()

    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.interruptible = True
        self._stopped = False
        self._lock = threading.Lock()
        self._current_process: subprocess.Popen | None = None

    @classmethod
    def end_running_commands(cls):
        for process in list(cls._running):
            cls._end(process)

    @classmethod
    def end_running_commands_on_exit(cls):
        atexit.register(cls.end_running_commands)
        for signum in (signal.SIGHUP, signal.SIGTERM):
            signal.signal(signum, lambda received, frame: sys.exit(128 + received))

    def stop(self):
        with self._lock:
            self._stopped = True
            process = self._current_process if self.interruptible else None
        if process:
            self._end(process)

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
            env["GIT_TERMINAL_PROMPT"] = "0"

            process = subprocess.Popen(
                cmd,
                cwd=str(cwd) if cwd else None,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE if capture else None,
                stderr=subprocess.PIPE if capture else None,
                text=True,
                process_group=0,
            )
            self._current_process = process
            CommandExecutor._running.add(process)

        try:
            stdout, stderr = process.communicate()
            retcode = process.poll()
            if retcode and retcode != 0:
                raise subprocess.CalledProcessError(retcode, cmd, output=stdout, stderr=stderr)
            return subprocess.CompletedProcess(process.args, retcode, stdout, stderr)
        finally:
            CommandExecutor._running.discard(process)
            self._current_process = None

    @staticmethod
    def _end(process: subprocess.Popen):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
