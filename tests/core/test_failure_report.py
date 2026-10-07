import logging
import re
import shlex
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from patcher.core import (AppConfig, BuildStepConfig, CommandExecutor, Component, EngineType, FailureReport,
                          FetchStepConfig, Game, PatchContext, PatchMode, PatchStatus, SessionLog, StepRecord)

LOGS = Path("Library/Application Support/HLPatcher/logs")
GOLDSRC = EngineType.GOLDSRC
SOURCE = EngineType.SOURCE
FAILED_COMMAND = ["sh", "-c", "echo 'Checking for SDL2'; echo 'The configuration failed' >&2; exit 1"]
CONFIG_LOG = "Checking for 'SDL2' : not found\n"
LONG_LOG = "start of a long build\n" + "[ 1/9000] Compiling cl_main.c\n" * 9000 + "end of a long build\n"
BAD_CPU_TYPE = "arch: posix_spawnp: /usr/bin/true: Bad CPU type in executable\n"
SYSTEM = {
    ("sw_vers", "-productVersion"): (0, "27.0.1\n"),
    ("sw_vers", "-buildVersion"): (1, "sw_vers: unknown option\n"),
    ("sysctl", "-n", "hw.model"): (0, "Mac15,12\n"),
    ("sysctl", "-n", "machdep.cpu.brand_string"): (0, "Apple M3\n"),
    ("sysctl", "-n", "hw.memsize"): (0, "17179869184\n"),
    ("sysctl", "-n", "sysctl.proc_translated"): (0, "0\n"),
}


def make_game(home):
    game_dir = home / "Steam" / "steamapps" / "common" / "Half-Life"
    engine = Component("GoldSrc Engine", "", GOLDSRC, PatchStatus.NEEDS_PATCH, id="goldsrc-engine", steps=[
        FetchStepConfig("goldsrc-engine-fetcher", url="https://github.com/FWGS/xash3d-fwgs",
                        patch_dir_name="xash3d-fwgs"),
        BuildStepConfig("waf-builder", patch_dir_name="xash3d-fwgs", build_args=["-8", "--enable-bundled-deps"]),
    ])
    half_life = Component("Half-Life", "valve", GOLDSRC, PatchStatus.ALREADY_PATCHED, id="half-life")
    return Game("Half-Life", game_dir, GOLDSRC, [engine, half_life])


def install_game(game, home):
    (game.path / "valve").mkdir(parents=True)
    shutil.copy("/usr/bin/true", game.path / "hl_osx")
    (game.path / "launch.sh").write_text("#!/bin/sh\n")
    (game.path / "launch.sh").chmod(0o755)
    (game.path / "valve" / "libnotreally.dylib").write_text("not a library")
    (game.path / "unreadable_osx").write_bytes(b"\xcf\xfa\xed\xfe")
    (game.path / "unreadable_osx").chmod(0o100)
    (home / "Documents" / "Half-Life backup (2026-10-01)").mkdir(parents=True)


def git(clone, *args):
    settings = ["-c", "user.name=HLPatcher", "-c", "user.email=tests@hlpatcher", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", *settings, *args], cwd=clone, check=True, capture_output=True)


def make_clone(working_dir):
    clone = working_dir / "xash3d-fwgs"
    clone.mkdir(parents=True)
    git(clone, "init", "--quiet")
    (clone / "wscript").write_text("conf.check_cfg(package='sdl2')\n")
    git(clone, "add", "wscript")
    git(clone, "commit", "--quiet", "-m", "Initial commit")
    (clone / "wscript").write_text("conf.check_cfg(package='sdl2', mandatory=False)\n")
    (clone / "build" / "CMakeFiles").mkdir(parents=True)
    (clone / "build" / "config.log").write_text(CONFIG_LOG)
    (clone / "build" / "build.log").write_text(LONG_LOG)
    (clone / "build" / "CMakeFiles" / "CMakeConfigureLog.yaml").write_text("events:\n")
    return clone


def half_life_2(home):
    return Game("Half-Life 2", home / "Steam" / "steamapps" / "common" / "Half-Life 2", SOURCE, [
        Component("Half-Life 2", "hl2", SOURCE, PatchStatus.NEEDS_PATCH, id="half-life-2"),
    ])


def fake_system(rosetta):
    def run(cmd, **kwargs):
        if cmd[:2] == ("arch", "-x86_64"):
            code, output = (0, "") if rosetta else (1, BAD_CPU_TYPE)
        elif Path(cmd[0]).name == "perl":
            code, output = 0, "\nThis is perl 5, version 34, subversion 1 (v5.34.1)\n"
        else:
            code, output = SYSTEM.get(cmd, (0, ""))
        return subprocess.CompletedProcess(cmd, code, output, "")

    return run


def failed_build(executor, folder):
    try:
        try:
            executor.run(FAILED_COMMAND, cwd=folder)
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Building xash3d-fwgs failed") from e
    except RuntimeError as e:
        return e


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    home = tmp_path_factory.mktemp("home")
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(Path, "home", lambda: home)
        monkeypatch.setenv("CC", "clang")
        monkeypatch.setenv("DYLD_LIBRARY_PATH", str(home / "lib"))
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret")
        monkeypatch.setattr(SessionLog, "_path", home / LOGS / "session-2026-10-06_14-00-00.log")
        (home / LOGS).mkdir(parents=True)
        SessionLog.current().write_text(f"14:00:01 [INFO] patcher.core.patcher: Preparing environment in {home}\n")
        old_reports = [home / LOGS / f"HLPatcher-failure-2026-01-{day:02d}_12-00-00.zip" for day in range(1, 11)]
        for old in old_reports:
            old.touch()

        working_dir = home / "work"
        clone = make_clone(working_dir)
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(working_dir / "venv")], check=True)
        (working_dir / "venv" / "pip.log").write_text("Collecting cmake\n")
        game = make_game(home)
        install_game(game, home)
        engine = game.components[0]
        context = PatchContext(steam_library_path=home / "Steam", working_dir=working_dir,
                               script_dir=home / "HLPatcher", patch_mode=PatchMode.STABLE, create_backup=True,
                               games=[game, half_life_2(home)], selected_components=[engine])
        started = datetime.now() - timedelta(seconds=30)
        timeline = [
            StepRecord(game, engine, 1, 2, engine.steps[0], started, started + timedelta(seconds=12.5)),
            StepRecord(game, engine, 2, 2, engine.steps[1], started + timedelta(seconds=13)),
        ]
        executor = CommandExecutor(working_dir)
        error = failed_build(executor, clone)

        path = FailureReport(context, AppConfig(debug=True), timeline, executor).write(error)

        with zipfile.ZipFile(path) as archive:
            files = {name: archive.read(name).decode() for name in archive.namelist()}
        yield {"home": home, "path": path, "files": files, "old_reports": old_reports, "clone": clone}


@pytest.fixture(scope="module")
def text(report):
    return report["files"]["report.txt"]


def section(text, title):
    return re.search(rf"== {title}\n(.*?)(?=\n\n== |\n\Z)", text, re.S).group(1)


def test_saves_one_zip_next_to_the_session_logs_and_keeps_the_ten_newest(report):
    path, home = report["path"], report["home"]

    assert path.parent == home / LOGS
    assert re.fullmatch(r"HLPatcher-failure-\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d\.zip", path.name)
    assert sorted((home / LOGS).glob("HLPatcher-failure-*")) == report["old_reports"][1:] + [path]


def test_holds_the_report_session_log_folder_listing_git_state_and_build_logs(report):
    assert sorted(report["files"]) == [
        "build-logs/xash3d-fwgs/build/CMakeFiles/CMakeConfigureLog.yaml",
        "build-logs/xash3d-fwgs/build/build.log",
        "build-logs/xash3d-fwgs/build/config.log",
        "git/xash3d-fwgs.txt",
        "report.txt",
        "session.log",
        "working-folder.txt",
    ]


def test_never_mentions_the_home_folder(report):
    home = str(report["home"])

    assert not [name for name, content in report["files"].items() if home in content]
    assert "Steam library: ~/Steam" in report["files"]["report.txt"]
    assert report["files"]["session.log"] == "14:00:01 [INFO] patcher.core.patcher: Preparing environment in ~\n"


def test_shows_the_error_with_its_cause(text):
    error = section(text, "Error")

    assert "subprocess.CalledProcessError: Command '['sh', '-c'" in error
    assert error.endswith("RuntimeError: Building xash3d-fwgs failed")


def test_names_the_failed_step_with_its_config(text):
    failed = section(text, "Failed step")

    assert failed.startswith("Game: Half-Life\nComponent: GoldSrc Engine (goldsrc-engine)\nStep: 2 of 2, waf-builder\n")
    assert '"build_args": [\n    "-8",\n    "--enable-bundled-deps"\n  ]' in failed


def test_shows_the_last_command_its_exit_code_and_output(text):
    assert section(text, "Last command") == "\n".join([
        f"Command: {shlex.join(FAILED_COMMAND)}",
        "Folder: ~/work/xash3d-fwgs",
        "Exit code: 1",
        "Last lines of its output:",
        "Checking for SDL2",
        "The configuration failed",
    ])


def test_describes_the_session_and_every_detected_game(text):
    session = section(text, "Session")

    assert "Debug mode: True\nLaunched from: ~/HLPatcher\nSteam library: ~/Steam\n" in session
    assert "Patch mode: Stable\nBack up games: True\nWorking folder: ~/work\n" in session
    assert "Selected components: GoldSrc Engine (goldsrc-engine)\n" in session
    assert session.endswith("\n".join([
        "Detected games:",
        "  Half-Life (GoldSrc) at ~/Steam/steamapps/common/Half-Life",
        "    GoldSrc Engine (goldsrc-engine): Needs patching",
        "    Half-Life (half-life): Already patched",
        "  Half-Life 2 (Source) at ~/Steam/steamapps/common/Half-Life 2",
        "    Half-Life 2 (half-life-2): Needs patching",
    ]))


def test_lists_the_steps_that_ran(text):
    first, second = section(text, "Timeline").splitlines()

    assert first.endswith("GoldSrc Engine, step 1 of 2 (goldsrc-engine-fetcher): done in 12.5s")
    assert second.endswith("GoldSrc Engine, step 2 of 2 (waf-builder): FAILED")


def test_lists_the_binaries_and_backups_of_the_failed_game(text):
    lines = section(text, "Game folders").splitlines()

    assert lines[:3] == [
        "Half-Life at ~/Steam/steamapps/common/Half-Life",
        "Backups: Half-Life backup (2026-10-01)",
        "Binaries (1):",
    ]
    assert re.fullmatch(r"  hl_osx  \d+ bytes  \d{4}-\d\d-\d\d \d\d:\d\d  .*arm64.*", lines[3])
    assert len(lines) == 4


def test_describes_the_mac_and_its_build_tools(text):
    machine, toolchain = section(text, "Machine"), section(text, "Toolchain")

    assert re.search(r"^macOS: \d+\.\d+.* \(\w+\)$", machine, re.M)
    assert re.search(r"^Chip: Apple ", machine, re.M)
    assert re.search(r"^Memory: \d+ GB$", machine, re.M)
    assert re.search(r"^Running under Rosetta: (True|False)$", machine, re.M)
    assert re.search(r"^Rosetta installed: (True|False)$", machine, re.M)
    assert re.search(r"^System disk: [\d.]+ GB free of [\d.]+ GB \(/\)$", machine, re.M)
    assert re.search(r"^Working folder disk: .* \(~/work\)$", machine, re.M)
    assert re.search(r"^Steam library disk: .* \(~/Steam\)$", machine, re.M)
    assert re.search(r"^clang: .*clang version", toolchain, re.M)
    assert re.search(r"^  git: /\S+/git, git version", toolchain, re.M)
    assert "In the build venv (~/work/venv/bin):\n  python3: ~/work/venv/bin/python3, Python 3." in toolchain
    assert "  cmake: not found\n" in toolchain


@pytest.mark.parametrize("rosetta", [True, False], ids=["with-rosetta", "without-rosetta"])
def test_reads_the_mac_from_its_system_tools(tmp_path, mocker, rosetta):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    mocker.patch("patcher.core.failure_report.subprocess.run", side_effect=fake_system(rosetta))

    text = write_without_a_patch_run(tmp_path)["report.txt"]

    assert section(text, "Machine").splitlines()[:6] == [
        "macOS: 27.0.1 (sw_vers: unknown option <exit code 1>)",
        "Model: Mac15,12",
        "Chip: Apple M3",
        "Memory: 16 GB",
        "Running under Rosetta: False",
        f"Rosetta installed: {rosetta}",
    ]
    assert re.search(r"^  perl: \S+, This is perl 5, version 34", section(text, "Toolchain"), re.M)


def test_shares_only_build_related_environment_variables(report, text):
    environment = section(text, "Environment").splitlines()

    assert "CC=clang" in environment
    assert "DYLD_LIBRARY_PATH=~/lib" in environment
    assert "CFLAGS=(not set)" in environment
    assert not [name for name, content in report["files"].items() if "ghp_secret" in content]


def test_describes_the_app_python_and_the_build_venv_with_their_packages(text):
    python = section(text, "Python")

    assert re.search(r"^customtkinter: \d", python, re.M)
    assert re.search(r"^  customtkinter==\d", python, re.M)
    assert "Build venv (~/work/venv):\n  Python 3." in python
    assert re.search(r"^  home = /", python, re.M)
    assert re.search(r"^Build venv packages:\n  .*No module named pip", python, re.M)


def entries(listing):
    return [re.fullmatch(r" *\d+  \S+ \S+  (.*)", line).group(1) for line in listing.splitlines()[1:]]


def test_lists_the_working_folder_without_git_or_venv_internals(report):
    listing = report["files"]["working-folder.txt"]

    assert listing.startswith("~/work\n")
    assert entries(listing) == [
        "venv/  (contents not listed)",
        "xash3d-fwgs/",
        "xash3d-fwgs/.git/  (contents not listed)",
        "xash3d-fwgs/build/",
        "xash3d-fwgs/wscript",
        "xash3d-fwgs/build/CMakeFiles/",
        "xash3d-fwgs/build/build.log",
        "xash3d-fwgs/build/config.log",
        "xash3d-fwgs/build/CMakeFiles/CMakeConfigureLog.yaml",
    ]


def test_records_the_commit_and_local_changes_of_every_clone(report):
    clone = report["files"]["git/xash3d-fwgs.txt"]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=report["clone"], capture_output=True,
                            text=True).stdout.strip()

    assert f"Commit: {commit}\n" in clone
    assert "== Status\n M wscript\n?? build/\n" in clone
    assert "+conf.check_cfg(package='sdl2', mandatory=False)" in clone


def test_includes_every_build_log_whole(report):
    files = report["files"]

    assert files["build-logs/xash3d-fwgs/build/config.log"] == CONFIG_LOG
    assert files["build-logs/xash3d-fwgs/build/build.log"] == LONG_LOG
    assert files["build-logs/xash3d-fwgs/build/CMakeFiles/CMakeConfigureLog.yaml"] == "events:\n"


def test_stops_listing_a_huge_working_folder(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    mocker.patch("patcher.core.failure_report.MAX_TREE_ENTRIES", 3)
    for name in "abcde":
        (tmp_path / "work" / name).mkdir(parents=True)

    listing = write_without_a_patch_run(tmp_path)["working-folder.txt"]

    assert entries(listing.removesuffix("... stopped after 3 entries\n")) == ["a/", "b/", "c/"]


def test_lists_an_entry_it_cant_look_at_without_details(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    locked = tmp_path / "work" / "locked"
    locked.mkdir(parents=True)
    (locked / "config.log").write_text(CONFIG_LOG)
    locked.chmod(0o444)
    try:
        files = write_without_a_patch_run(tmp_path)
    finally:
        locked.chmod(0o755)

    root, folder, log = files["working-folder.txt"].splitlines()
    assert entries(f"{root}\n{folder}") == ["locked/"]
    assert log == "           ?  ?                 locked/config.log  (Permission denied)"
    assert files["build-logs/locked/config.log"].startswith("Couldn't collect this: PermissionError(")


def write_without_a_patch_run(home, timeline=(), games=()):
    context = PatchContext(working_dir=home / "work", games=list(games),
                           selected_components=[game.components[0] for game in games])
    path = FailureReport(context, AppConfig(), list(timeline), CommandExecutor(context.working_dir)).write(
        ValueError("bad config"))
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name).decode() for name in archive.namelist()}


def test_a_failure_before_any_step_still_gets_a_report(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    mocker.patch.object(SessionLog, "_path", None)

    files = write_without_a_patch_run(tmp_path)
    text, session_log = files["report.txt"], files["session.log"]

    assert sorted(files) == ["report.txt", "session.log", "working-folder.txt"]
    assert files["working-folder.txt"] == "The working folder ~/work doesn't exist.\n"

    assert section(text, "Error").endswith("ValueError: bad config")
    assert section(text, "Failed step").startswith("No patch step was running")
    assert section(text, "Last command") == "No command was run."
    assert "Steam library: not chosen\n" in section(text, "Session")
    assert section(text, "Timeline") == "No patch step started."
    assert section(text, "Game folders") == "No game was being patched."
    assert section(text, "Python").endswith("Build venv (~/work/venv):\n  not created")
    assert session_log == "This session's log wasn't saved.\n"


def test_a_failure_after_the_last_step_finished_blames_no_step(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    game = make_game(tmp_path)
    engine = game.components[0]
    started = datetime.now()
    finished = StepRecord(game, engine, 2, 2, engine.steps[1], started, started)

    text = write_without_a_patch_run(tmp_path, [finished])["report.txt"]

    assert section(text, "Failed step") == ("No patch step was running, so it failed while backing up, preparing the "
                                            "build environment or cleaning up.")
    assert section(text, "Timeline").endswith("GoldSrc Engine, step 2 of 2 (waf-builder): done in 0.0s")


def test_a_failure_after_a_successful_command_shows_that_command_without_an_exit_code(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    executor = CommandExecutor(tmp_path / "work")
    executor.run(["echo", "Installing xash3d-fwgs..."])
    report = FailureReport(PatchContext(working_dir=tmp_path / "work"), AppConfig(), [], executor)

    path = report.write(FileNotFoundError("xash3d launcher not found"))

    with zipfile.ZipFile(path) as archive:
        text = archive.read("report.txt").decode()
    assert section(text, "Last command") == "\n".join([
        "Command: echo 'Installing xash3d-fwgs...'",
        "Folder: the app folder",
        "Last lines of its output:",
        "Installing xash3d-fwgs...",
    ])


def test_without_a_failed_step_describes_the_selected_games(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    text = write_without_a_patch_run(tmp_path, games=[make_game(tmp_path)])["report.txt"]

    assert section(text, "Game folders") == ("Half-Life at ~/Steam/steamapps/common/Half-Life: "
                                             "the folder doesn't exist.")


def test_a_tool_that_hangs_doesnt_stop_the_report(tmp_path, mocker):
    def hang(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, 60)

    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    mocker.patch("patcher.core.failure_report.subprocess.run", side_effect=hang)

    text = write_without_a_patch_run(tmp_path)["report.txt"]

    assert "macOS: <Command '('sw_vers', '-productVersion')' timed out after 60 seconds>" in section(text, "Machine")
    assert section(text, "Error").endswith("ValueError: bad config")


def test_a_part_that_cant_be_collected_doesnt_lose_the_rest(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    mocker.patch.object(FailureReport, "_session", side_effect=OSError("the context is gone"))

    text = write_without_a_patch_run(tmp_path)["report.txt"]

    assert section(text, "Session") == "Couldn't collect this: OSError('the context is gone')"
    assert section(text, "Error").endswith("ValueError: bad config")
    assert section(text, "Timeline") == "No patch step started."


def test_returns_nothing_when_the_report_cant_be_saved(tmp_path, mocker, caplog):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    (tmp_path / LOGS).parent.mkdir(parents=True)
    (tmp_path / LOGS).touch()
    report = FailureReport(PatchContext(), AppConfig(), [], CommandExecutor(Path("work")))

    with caplog.at_level(logging.ERROR):
        assert report.write(ValueError("bad config")) is None

    assert "Couldn't write the failure report" in caplog.messages
