import subprocess

import pytest

from patcher.core import CommandExecutor


def test_executor_run(tmp_path, mocker):
    mock_popen = mocker.patch("subprocess.Popen")
    mock_process = mocker.Mock()
    mock_process.communicate.return_value = ("stdout", "stderr")
    mock_process.poll.return_value = 0
    mock_process.args = ["echo", "test"]
    mock_popen.return_value = mock_process

    executor = CommandExecutor(tmp_path)
    result = executor.run(["echo", "test"])

    assert result.stdout == "stdout"
    assert result.stderr == "stderr"
    assert result.returncode == 0

    call_kwargs = mock_popen.call_args[1]
    assert "venv/bin" in call_kwargs["env"]["PATH"]


def test_executor_run_error(tmp_path, mocker):
    mock_popen = mocker.patch("subprocess.Popen")
    mock_process = mocker.Mock()
    mock_process.communicate.return_value = ("error_out", "error_err")
    mock_process.poll.return_value = 1
    mock_process.args = ["false"]
    mock_popen.return_value = mock_process

    executor = CommandExecutor(tmp_path)
    with pytest.raises(subprocess.CalledProcessError):
        executor.run(["false"])


def test_executor_stop(tmp_path):
    executor = CommandExecutor(tmp_path)
    executor.stop()
    with pytest.raises(RuntimeError, match="Execution stopped"):
        executor.run(["echo", "test"])


def test_executor_stop_running_process(tmp_path, mocker):
    executor = CommandExecutor(tmp_path)
    mock_process = mocker.Mock()
    executor._current_process = mock_process

    executor.stop()
    mock_process.terminate.assert_called_once()
