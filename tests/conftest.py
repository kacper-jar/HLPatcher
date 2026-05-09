import subprocess
from pathlib import Path

import pytest

from patcher.core import AppConfig, Component, EngineType, Game, PatchContext, PatchStatus


@pytest.fixture
def mock_steam_library(tmp_path):
    steam_lib = tmp_path / "SteamLibrary"
    steam_lib.mkdir()

    goldsrc_dir = steam_lib / "Half-Life"
    goldsrc_dir.mkdir()
    (goldsrc_dir / "hl_osx").touch()

    hl2_dir = steam_lib / "Half-Life 2"
    hl2_dir.mkdir()
    (hl2_dir / "hl2_osx").touch()

    portal_dir = steam_lib / "Portal"
    portal_dir.mkdir()
    (portal_dir / "hl2_osx").touch()

    return steam_lib


@pytest.fixture
def mock_patch_context(mock_steam_library, tmp_path):
    working_dir = tmp_path / "working_dir"
    working_dir.mkdir()

    context = PatchContext(
        steam_library_path=mock_steam_library,
        working_dir=working_dir,
        script_dir=tmp_path / "script_dir",
    )
    (context.script_dir / "fixes" / "src" / "source-engine").mkdir(parents=True)
    return context


@pytest.fixture
def mock_run_command(mocker):
    class MockProcess:
        def __init__(self, args, returncode=0, stdout="mock_stdout", stderr="mock_stderr"):
            self.args = args
            self.returncode = returncode
            self._stdout = stdout
            self._stderr = stderr

        def communicate(self):
            return self._stdout, self._stderr

        def poll(self):
            return self.returncode

        def terminate(self):
            pass

    def mock_popen(cmd, *args, **kwargs):
        mock_popen.commands.append((cmd, kwargs.get("cwd")))
        return MockProcess(cmd)

    mock_popen.commands = []
    mocker.patch("subprocess.Popen", side_effect=mock_popen)
    return mock_popen
