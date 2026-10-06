import logging
import re
from pathlib import Path

import pytest

from patcher.core import SessionLog

LOGS = Path("Library/Application Support/HLPatcher/logs")
MESSAGE = re.compile(r"\d\d:\d\d:\d\d \[INFO\] patcher\.core\.patcher: Preparing environment\.\.\.")


@pytest.fixture
def home(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path / "home")
    return tmp_path / "home"


@pytest.fixture(autouse=True)
def root_logger(mocker):
    mocker.patch.object(SessionLog, "_path", None)
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield root
    for handler in root.handlers[:]:
        if handler not in handlers:
            root.removeHandler(handler)
            handler.close()
    root.setLevel(level)
    logging.captureWarnings(False)


def log_a_session():
    logging.getLogger("patcher.core.patcher").info("Preparing environment...")
    logging.getLogger("patcher.output").info("Checking for 'clang' : not found")
    logging.getLogger("patcher.core.patcher").debug("Debug details")


def test_saves_the_session_log_in_application_support(home):
    path = SessionLog.start(debug=False)

    log_a_session()

    assert path.parent == home / LOGS
    assert re.fullmatch(r"session-\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d\.log", path.name)
    assert SessionLog.current() == path
    first, message, output = path.read_text().splitlines()
    assert first.endswith(f"Saving this session's log to {path}")
    assert MESSAGE.fullmatch(message)
    assert output == "Checking for 'clang' : not found"


def test_prints_messages_to_stderr_and_command_output_unchanged_to_stdout(home, capfd):
    SessionLog.start(debug=False)

    log_a_session()

    out, err = capfd.readouterr()
    assert out == "Checking for 'clang' : not found\n"
    assert MESSAGE.fullmatch(err.splitlines()[-1])


def test_debug_mode_logs_debug_messages_too(home):
    path = SessionLog.start(debug=True)

    log_a_session()

    assert path.read_text().splitlines()[-1].endswith("[DEBUG] patcher.core.patcher: Debug details")


def test_keeps_the_ten_newest_session_logs(home):
    (home / LOGS).mkdir(parents=True)
    old = [home / LOGS / f"session-2026-01-{day:02d}_12-00-00.log" for day in range(1, 13)]
    for path in old:
        path.touch()

    path = SessionLog.start(debug=False)

    assert sorted((home / LOGS).glob("session-*.log")) == old[3:] + [path]


def test_keeps_logging_to_the_terminal_when_the_log_cant_be_saved(home, capfd):
    (home / LOGS).parent.mkdir(parents=True)
    (home / LOGS).touch()

    assert SessionLog.start(debug=False) is None

    log_a_session()
    out, err = capfd.readouterr()
    assert out == "Checking for 'clang' : not found\n"
    assert "Couldn't save this session's log" in err
    assert SessionLog.current() is None
