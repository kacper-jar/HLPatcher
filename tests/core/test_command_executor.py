import contextlib
import logging
import os
import signal
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from patcher.core import CommandExecutor


def eventually(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return bool(condition())


def running(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


@pytest.fixture
def executor(tmp_path):
    return CommandExecutor(tmp_path / "working_dir")


@pytest.fixture
def background(executor):
    with ThreadPoolExecutor(max_workers=1) as pool:
        yield pool
        executor.interruptible = True
        executor.stop()


def test_runs_a_command_and_returns_its_output(executor):
    result = executor.run(["echo", "Building hlsdk-portable"], capture=True)

    assert (result.args, result.returncode, result.stdout, result.stderr) == (
        ["echo", "Building hlsdk-portable"], 0, "Building hlsdk-portable\n", "",
    )


def test_prints_output_straight_to_the_terminal_unless_captured(executor, capfd):
    result = executor.run(["echo", "Building hlsdk-portable"])

    assert result.stdout is None
    assert capfd.readouterr().out == "Building hlsdk-portable\n"


def test_runs_in_the_given_folder(executor, tmp_path):
    result = executor.run(["pwd", "-P"], cwd=tmp_path, capture=True)

    assert Path(result.stdout.strip()) == tmp_path.resolve()


def test_finds_build_tools_in_the_venv_first(executor, tmp_path):
    cmake = tmp_path / "working_dir" / "venv" / "bin" / "cmake"
    cmake.parent.mkdir(parents=True)
    cmake.write_text("#!/bin/sh\necho cmake from the venv\n")
    cmake.chmod(0o755)

    result = executor.run(["cmake", "--version"], capture=True)

    assert result.stdout == "cmake from the venv\n"


def test_a_failing_command_raises_with_its_exit_code_and_error_output(executor):
    with pytest.raises(subprocess.CalledProcessError) as error:
        executor.run(["sh", "-c", "echo 'waf: build failed' >&2; exit 3"], capture=True)

    assert (error.value.returncode, error.value.stderr) == (3, "waf: build failed\n")


def test_logs_every_command(executor, caplog):
    with caplog.at_level(logging.INFO):
        executor.run(["echo", "Building hlsdk-portable"], capture=True)

    assert "Running: echo Building hlsdk-portable" in caplog.messages


def test_stop_terminates_the_running_command(executor, tmp_path, background):
    started = tmp_path / "started"
    future = background.submit(executor.run, ["sh", "-c", f"touch '{started}'; exec sleep 30"])
    assert eventually(started.exists)

    executor.stop()

    with pytest.raises(subprocess.CalledProcessError) as error:
        future.result(timeout=5)
    assert error.value.returncode == -signal.SIGTERM


def test_stop_lets_a_non_interruptible_command_finish(executor, tmp_path, background):
    started, finished = tmp_path / "started", tmp_path / "finished"
    executor.interruptible = False
    future = background.submit(executor.run, ["sh", "-c", f"touch '{started}'; sleep 0.3; touch '{finished}'"])
    assert eventually(started.exists)

    executor.stop()

    assert future.result(timeout=5).returncode == 0
    assert finished.exists()


def test_after_stop_only_non_interruptible_steps_start_commands(executor, tmp_path):
    executor.stop()

    executor.interruptible = False
    executor.run(["touch", str(tmp_path / "relinked")])
    executor.interruptible = True
    with pytest.raises(RuntimeError, match="Execution stopped by user"):
        executor.run(["touch", str(tmp_path / "cloned")])

    assert (tmp_path / "relinked").exists()
    assert not (tmp_path / "cloned").exists()


def test_raise_if_stopped_raises_only_after_a_stop(executor):
    executor.raise_if_stopped()

    executor.stop()

    with pytest.raises(RuntimeError, match="Execution stopped by user"):
        executor.raise_if_stopped()


@pytest.mark.xfail(raises=AssertionError, strict=True,
                   reason="Stop terminates only the command itself, so the processes it started keep running")
def test_stop_also_ends_the_processes_a_command_started(executor, tmp_path, background):
    pid_file = tmp_path / "compiler.pid"
    future = background.submit(executor.run, ["sh", "-c", f"sleep 30 & echo $! > '{pid_file}'; wait"])
    assert eventually(lambda: pid_file.exists() and pid_file.read_text().strip())
    compiler = int(pid_file.read_text())

    try:
        executor.stop()
        with pytest.raises(subprocess.CalledProcessError):
            future.result(timeout=5)
        assert eventually(lambda: not running(compiler), timeout=0.5)
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.kill(compiler, signal.SIGKILL)
