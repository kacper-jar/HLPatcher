import atexit
import logging
import os
import signal
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUT_LOGGER = "patcher.output"
OUTPUT_TAIL_LINES = 200
OUTPUT_GRACE_SECONDS = 2

output_logger = logging.getLogger(OUTPUT_LOGGER)


class CommandExecutor:
    _running: set[subprocess.Popen] = set()

    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.interruptible = True
        self.last_command: list[str] = []
        self.last_cwd: Path | None = None
        self.recent_output: deque[str] = deque(maxlen=OUTPUT_TAIL_LINES)
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

            self.last_command = cmd
            self.last_cwd = cwd
            self.recent_output.clear()
            process = subprocess.Popen(
                cmd,
                cwd=str(cwd) if cwd else None,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if capture else subprocess.STDOUT,
                text=True,
                errors="replace",
                process_group=0,
            )
            self._current_process = process
            CommandExecutor._running.add(process)

        try:
            if capture:
                stdout, stderr = process.communicate()
            else:
                stdout = stderr = None
                self._forward_output(process)
            retcode = process.poll()
            if retcode and retcode != 0:
                output = stdout if capture else "\n".join(self.recent_output.copy())
                raise subprocess.CalledProcessError(retcode, cmd, output=output, stderr=stderr)
            return subprocess.CompletedProcess(process.args, retcode, stdout, stderr)
        finally:
            CommandExecutor._running.discard(process)
            self._current_process = None

    def _forward_output(self, process: subprocess.Popen):
        def forward():
            for line in process.stdout:
                line = line.rstrip("\n")
                self.recent_output.append(line)
                output_logger.info(line)

        reader = threading.Thread(target=forward, daemon=True)
        reader.start()
        process.wait()
        reader.join(OUTPUT_GRACE_SECONDS)

    @staticmethod
    def _end(process: subprocess.Popen):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
