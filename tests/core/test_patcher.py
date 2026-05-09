from pathlib import Path

from patcher.core.models import AppConfig, Component, EngineType, Game, PatchMode, PatchStatus
from patcher.core.patcher import Patcher


def test_get_total_steps(mock_patch_context):
    patcher = Patcher(mock_patch_context, AppConfig())

    comp1 = Component("GoldSrc Engine", "", EngineType.GOLDSRC, PatchStatus.NEEDS_PATCH, "")
    comp2 = Component("Half-Life", "valve", EngineType.GOLDSRC, PatchStatus.NEEDS_PATCH, "")
    game1 = Game("GoldSrc", Path("/fake"), EngineType.GOLDSRC, [comp1, comp2])

    comp3 = Component("Half-Life 2", "hl2", EngineType.SOURCE, PatchStatus.NEEDS_PATCH, "", waf_game="hl2")
    comp4 = Component("Portal", "portal", EngineType.SOURCE, PatchStatus.NEEDS_PATCH, "", waf_game="portal")
    game2 = Game("HL2", Path("/fake2"), EngineType.SOURCE, [comp3, comp4])

    steps = patcher.get_total_steps([game1, game2])
    assert steps == 5


def test_create_backup(mock_patch_context, mocker):
    mock_patch_context.create_backup = True
    patcher = Patcher(mock_patch_context, AppConfig())

    mock_copytree = mocker.patch("shutil.copytree")

    game = Game("GoldSrc", Path("/fake/GoldSrc"), EngineType.GOLDSRC)
    patcher._create_backup([game])

    mock_copytree.assert_called_once()
    args, kwargs = mock_copytree.call_args
    assert args[0] == Path("/fake/GoldSrc")
    assert "Documents" in str(args[1])


def test_prepare_goldsrc_engine(mock_patch_context, mock_run_command, mocker):
    patcher = Patcher(mock_patch_context, AppConfig())
    mocker.patch("shutil.copytree")
    patcher._prepare_goldsrc_engine()

    assert len(mock_run_command.commands) == 4
    assert mock_run_command.commands[0][0][0] == "git"
    assert mock_run_command.commands[1][0][0] == "curl"
    assert mock_run_command.commands[2][0][0] == "hdiutil"
    assert mock_run_command.commands[3][0][0] == "hdiutil"


def test_prepare_hlsdk_mod(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    patcher._prepare_hlsdk_mod("hlfixed", "78bc253")

    assert len(mock_run_command.commands) == 2
    assert mock_run_command.commands[0][0][0] == "git"
    assert mock_run_command.commands[0][0][1] == "clone"
    assert mock_run_command.commands[1][0][0] == "git"
    assert mock_run_command.commands[1][0][1] == "checkout"


def test_prepare_cstrike(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    patcher._prepare_cstrike()

    assert len(mock_run_command.commands) == 1
    assert mock_run_command.commands[0][0][0] == "git"
    assert mock_run_command.commands[0][0][1] == "clone"


def test_build_goldsrc_engine(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    patcher._build_goldsrc_engine()

    assert len(mock_run_command.commands) == 1
    cmd = mock_run_command.commands[0][0]
    assert cmd[0] == "./waf"
    assert cmd[1] == "configure"


def test_build_hlsdk_mod(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    patcher._build_hlsdk_mod("hlfixed")

    assert len(mock_run_command.commands) == 1
    cmd = mock_run_command.commands[0][0]
    assert cmd[0] == "./waf"
    assert cmd[1] == "configure"


def test_build_cstrike(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    patcher._build_cstrike()

    assert len(mock_run_command.commands) == 4
    assert mock_run_command.commands[0][0][1] == "build_deps.py"
    assert mock_run_command.commands[1][0][1] == "-m"
    assert mock_run_command.commands[1][0][2] == "cmake"


def test_prepare_source_engine(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    patcher._prepare_source_engine()

    assert len(mock_run_command.commands) == 1
    cmd1, _ = mock_run_command.commands[0]
    assert cmd1[0] == "git"
    assert cmd1[1] == "clone"
    assert "source-engine" in cmd1[4]


def test_prepare_source_engine_stable(mock_patch_context, mock_run_command):
    mock_patch_context.patch_mode = PatchMode.STABLE
    patcher = Patcher(mock_patch_context, AppConfig())
    patcher._prepare_source_engine()

    assert len(mock_run_command.commands) == 2
    cmd2, cwd2 = mock_run_command.commands[1]
    assert cmd2[0] == "git"
    assert cmd2[1] == "checkout"
    assert cmd2[2] == "ed8209c"


def test_build_source(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    patcher._build_source("hl2")

    assert len(mock_run_command.commands) == 1
    cmd, cwd = mock_run_command.commands[0]
    assert cmd[0] == "./waf"
    assert cmd[1] == "configure"
    assert "--build-games=hl2" in cmd
    assert "source-engine" in str(cwd)


def test_fix_source_links(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())

    bin_dir = mock_patch_context.working_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "libtier0.dylib").touch()

    game_path = mock_patch_context.working_dir
    patcher._fix_source_links(game_path)

    assert len(mock_run_command.commands) >= 1
    cmd, cwd = mock_run_command.commands[0]
    assert cmd[0] == "install_name_tool"
    assert cmd[1] == "-id"
    assert cmd[2] == "@loader_path/libtier0.dylib"
    assert cmd[3] == "libtier0.dylib"
    assert cwd == str(bin_dir)
