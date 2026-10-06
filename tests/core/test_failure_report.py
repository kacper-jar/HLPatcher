import logging
import re
import shlex
import subprocess
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from patcher.core import (AppConfig, BuildStepConfig, CommandExecutor, Component, EngineType, FailureReport,
                          FetchStepConfig, Game, PatchContext, PatchMode, PatchStatus, SessionLog, StepRecord)

LOGS = Path("Library/Application Support/HLPatcher/logs")
GOLDSRC = EngineType.GOLDSRC
FAILED_COMMAND = ["sh", "-c", "echo 'Checking for SDL2'; echo 'The configuration failed' >&2; exit 1"]


def make_game(home):
    engine = Component("GoldSrc Engine", "", GOLDSRC, PatchStatus.NEEDS_PATCH, id="goldsrc-engine", steps=[
        FetchStepConfig("goldsrc-engine-fetcher", url="https://github.com/FWGS/xash3d-fwgs",
                        patch_dir_name="xash3d-fwgs"),
        BuildStepConfig("waf-builder", patch_dir_name="xash3d-fwgs", build_args=["-8", "--enable-bundled-deps"]),
    ])
    half_life = Component("Half-Life", "valve", GOLDSRC, PatchStatus.ALREADY_PATCHED, id="half-life")
    return Game("Half-Life", home / "Steam" / "steamapps" / "common" / "Half-Life", GOLDSRC, [engine, half_life])


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
        monkeypatch.setattr(SessionLog, "_path", home / LOGS / "session-2026-10-06_14-00-00.log")
        (home / LOGS).mkdir(parents=True)
        SessionLog.current().write_text(f"14:00:01 [INFO] patcher.core.patcher: Preparing environment in {home}\n")
        old_reports = [home / LOGS / f"HLPatcher-failure-2026-01-{day:02d}_12-00-00.zip" for day in range(1, 11)]
        for old in old_reports:
            old.touch()

        working_dir = home / "work"
        clone = working_dir / "xash3d-fwgs"
        clone.mkdir(parents=True)
        game = make_game(home)
        engine = game.components[0]
        context = PatchContext(steam_library_path=home / "Steam", working_dir=working_dir,
                               script_dir=home / "HLPatcher", patch_mode=PatchMode.STABLE, create_backup=True,
                               games=[game], selected_components=[engine])
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
        yield {"home": home, "path": path, "files": files, "old_reports": old_reports}


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


def test_holds_the_report_and_the_session_log(report):
    assert sorted(report["files"]) == ["report.txt", "session.log"]


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
    ]))


def test_lists_the_steps_that_ran(text):
    first, second = section(text, "Timeline").splitlines()

    assert first.endswith("GoldSrc Engine, step 1 of 2 (goldsrc-engine-fetcher): done in 12.5s")
    assert second.endswith("GoldSrc Engine, step 2 of 2 (waf-builder): FAILED")


def write_without_a_patch_run(home, timeline=()):
    context = PatchContext(working_dir=home / "work")
    path = FailureReport(context, AppConfig(), list(timeline), CommandExecutor(context.working_dir)).write(
        ValueError("bad config"))
    with zipfile.ZipFile(path) as archive:
        return archive.read("report.txt").decode(), archive.read("session.log").decode()


def test_a_failure_before_any_step_still_gets_a_report(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    mocker.patch.object(SessionLog, "_path", None)

    text, session_log = write_without_a_patch_run(tmp_path)

    assert section(text, "Error").endswith("ValueError: bad config")
    assert section(text, "Failed step").startswith("No patch step was running")
    assert section(text, "Last command") == "No command was run."
    assert "Steam library: not chosen\n" in section(text, "Session")
    assert section(text, "Timeline") == "No patch step started."
    assert session_log == "This session's log wasn't saved.\n"


def test_a_failure_after_the_last_step_finished_blames_no_step(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    game = make_game(tmp_path)
    engine = game.components[0]
    started = datetime.now()

    text, _ = write_without_a_patch_run(tmp_path, [StepRecord(game, engine, 2, 2, engine.steps[1], started, started)])

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


def test_a_part_that_cant_be_collected_doesnt_lose_the_rest(tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    mocker.patch.object(FailureReport, "_session", side_effect=OSError("the context is gone"))

    text, _ = write_without_a_patch_run(tmp_path)

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
