import customtkinter as ctk
import pytest

from patcher.core import CommandExecutor, Component, EngineType, PatchContext, PatchStatus, StepContext


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

    hl2dm_dir = steam_lib / "Half-Life 2 Deathmatch" / "hl2mp"
    hl2dm_dir.mkdir(parents=True)
    (hl2dm_dir / "gameinfo.txt").touch()

    dods_dir = steam_lib / "Day of Defeat Source" / "dod"
    dods_dir.mkdir(parents=True)
    (dods_dir / "gameinfo.txt").touch()

    css_dir = steam_lib / "Counter-Strike Source" / "cstrike"
    css_dir.mkdir(parents=True)
    (css_dir / "gameinfo.txt").touch()

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
    (context.script_dir / "data" / "fixes" / "src").mkdir(parents=True)
    return context


@pytest.fixture
def step_context(mock_patch_context, mocker):
    return StepContext(
        working_dir=mock_patch_context.working_dir,
        script_dir=mock_patch_context.script_dir,
        steam_library_path=mock_patch_context.steam_library_path,
        patch_mode=mock_patch_context.patch_mode,
        executor=CommandExecutor(mock_patch_context.working_dir),
        log=mocker.Mock(),
    )


@pytest.fixture
def make_component():
    def factory(name="Test", subfolder="test", engine_type=EngineType.SOURCE, status=PatchStatus.NEEDS_PATCH,
                **fields):
        fields.setdefault("id", name.lower().replace(" ", "-"))
        return Component(name=name, subfolder=subfolder, engine_type=engine_type, status=status, **fields)

    return factory


@pytest.fixture
def tk_root():
    root = ctk.CTk()
    root.withdraw()
    yield root
    root.update()
    root.destroy()


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
