from pathlib import Path

from patcher.core.models import AppConfig, Component, EngineType, Game, PatchMode, PatchStatus
from patcher.core import Patcher
from patcher.core.pipeline.fetchers import GitFetcher, GoldSrcEngineFetcher
from patcher.core.pipeline.builders import WafBuilder, CMakeBuilder
from patcher.core.pipeline.installers import GenericInstaller, GoldSrcEngineInstaller, SourceInstaller


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

    comp = Component("GoldSrc Engine", "", EngineType.GOLDSRC, PatchStatus.NEEDS_PATCH, "")
    game = Game("GoldSrc", Path("/fake/GoldSrc"), EngineType.GOLDSRC, [comp])
    patcher._create_backup([game])

    mock_copytree.assert_called_once()
    args, kwargs = mock_copytree.call_args
    assert args[0] == Path("/fake/GoldSrc")
    assert "Documents" in str(args[1])


def test_create_backup_skips_unpatched(mock_patch_context, mocker):
    mock_patch_context.create_backup = True
    patcher = Patcher(mock_patch_context, AppConfig())

    mock_copytree = mocker.patch("shutil.copytree")

    comp = Component("GoldSrc Engine", "", EngineType.GOLDSRC, PatchStatus.ALREADY_PATCHED, "")
    game1 = Game("GoldSrc", Path("/fake/GoldSrc"), EngineType.GOLDSRC, [comp])

    comp_needs_patch = Component("Portal", "portal", EngineType.SOURCE, PatchStatus.NEEDS_PATCH, "", waf_game="portal")
    game2 = Game("Portal", Path("/fake/Portal"), EngineType.SOURCE, [comp_needs_patch])

    patcher._create_backup([game1, game2])

    mock_copytree.assert_called_once()
    args, kwargs = mock_copytree.call_args
    assert args[0] == Path("/fake/Portal")
    assert "Documents" in str(args[1])


def test_git_fetcher(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    fetcher = GitFetcher(patcher, "target_dir", "http://repo", "branch", "commit", force_stable=False)
    fetcher.fetch()

    assert len(mock_run_command.commands) >= 1
    assert mock_run_command.commands[0][0][0] == "git"
    assert mock_run_command.commands[0][0][1] == "clone"


def test_git_fetcher_stable(mock_patch_context, mock_run_command):
    mock_patch_context.patch_mode = PatchMode.STABLE
    patcher = Patcher(mock_patch_context, AppConfig())
    fetcher = GitFetcher(patcher, "target_dir", "http://repo", "branch", "1234567", force_stable=False)
    fetcher.fetch()

    assert len(mock_run_command.commands) == 3
    assert mock_run_command.commands[1][0][0] == "git"
    assert mock_run_command.commands[1][0][1] == "checkout"
    assert mock_run_command.commands[1][0][2] == "1234567"


def test_goldsrc_engine_fetcher(mock_patch_context, mock_run_command, mocker):
    patcher = Patcher(mock_patch_context, AppConfig())
    fetcher = GoldSrcEngineFetcher(patcher, "target_dir", "http://repo", "branch", "commit", force_stable=False)
    mocker.patch("shutil.copytree")

    fetcher.fetch()

    assert len(mock_run_command.commands) == 5


def test_goldsrc_engine_fetcher_stable(mock_patch_context, mock_run_command, mocker):
    mock_patch_context.patch_mode = PatchMode.STABLE
    patcher = Patcher(mock_patch_context, AppConfig())
    fetcher = GoldSrcEngineFetcher(patcher, "target_dir", "http://repo", "branch", "1234567", force_stable=False)
    mocker.patch("shutil.copytree")

    fetcher.fetch()

    assert len(mock_run_command.commands) == 7


def test_waf_builder(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    builder = WafBuilder(patcher, "target_dir", ["-8"])
    builder.build()

    assert len(mock_run_command.commands) == 1
    assert mock_run_command.commands[0][0][0] == "./waf"
    assert mock_run_command.commands[0][0][1] == "configure"


def test_cmake_builder(mock_patch_context, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    builder = CMakeBuilder(patcher, "target_dir")
    builder.build()

    assert len(mock_run_command.commands) == 4
    assert mock_run_command.commands[0][0][1] == "build_deps.py"
    assert mock_run_command.commands[1][0][1] == "-m"
    assert mock_run_command.commands[1][0][2] == "cmake"


def test_generic_installer(mock_patch_context, mocker):
    patcher = Patcher(mock_patch_context, AppConfig())
    installer = GenericInstaller(patcher, "target_dir")
    game = Game("Test", Path("/fake"), EngineType.GOLDSRC, [])

    mock_copytree = mocker.patch("shutil.copytree")
    installer.install(game)

    mock_copytree.assert_called_once()
    assert "target_dir/output" in str(mock_copytree.call_args[0][0])


def test_goldsrc_engine_installer(mock_patch_context, mocker):
    patcher = Patcher(mock_patch_context, AppConfig())
    installer = GoldSrcEngineInstaller(patcher, "target_dir")
    game = Game("Test", mock_patch_context.working_dir, EngineType.GOLDSRC, [])

    mock_copytree = mocker.patch("shutil.copytree")
    installer.install(game)

    assert mock_copytree.call_count == 2
    assert "SDL2.framework" in str(mock_copytree.call_args_list[1][0][0])


def test_source_installer(mock_patch_context, mocker, mock_run_command):
    patcher = Patcher(mock_patch_context, AppConfig())
    installer = SourceInstaller(patcher)
    game = Game("Test", mock_patch_context.working_dir, EngineType.SOURCE, [])

    bin_dir = mock_patch_context.working_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "libtier0.dylib").touch()

    output_dir = mock_patch_context.working_dir / "source-engine" / "output"
    (output_dir / "bin").mkdir(parents=True, exist_ok=True)
    (output_dir / "hl2").mkdir(parents=True, exist_ok=True)

    mock_copytree = mocker.patch("shutil.copytree")
    mock_copy2 = mocker.patch("shutil.copy2")

    installer.install(game, subfolders=["hl2"])

    assert mock_copytree.call_count >= 1
    assert len(mock_run_command.commands) >= 1
