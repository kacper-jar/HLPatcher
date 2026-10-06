import logging
import shutil
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from patcher.core import AppConfig, EngineType, Game, PatchMode, PatchStatus, Patcher, StepConfig
from patcher.core.pipeline import STEP_REGISTRY, BaseStep, step

HLSDK_URL = "https://github.com/FWGS/hlsdk-portable"


def steps(*step_types):
    return [StepConfig(step_type) for step_type in step_types]


def ran(events):
    return [event[1:] for event in events if event[0] == "run"]


@pytest.fixture
def events():
    return []


@pytest.fixture
def actions():
    return {}


@pytest.fixture(autouse=True)
def fake_steps(mocker, events, actions):
    mocker.patch.dict(STEP_REGISTRY)
    for type_name, can_interrupt in [("fetch", True), ("build", True), ("install", False)]:
        @step(type_name, config=StepConfig)
        class FakeStep(BaseStep):
            interruptible = can_interrupt

            def execute(self, game, comp, step_config):
                events.append(("run", comp.name, step_config.type))
                if step_config.type in actions:
                    actions[step_config.type](self.context, game, comp)


@pytest.fixture
def make_patcher(mock_patch_context, mock_run_command, events):
    def factory(debug=False):
        return Patcher(mock_patch_context, AppConfig(debug=debug),
                       component_callback=lambda name: events.append(("component", name)),
                       step_callback=lambda current, total: events.append(("step", current, total)))

    return factory


@pytest.fixture
def games(mock_steam_library, make_component):
    return [
        Game("Half-Life", mock_steam_library / "Half-Life", EngineType.GOLDSRC, [
            make_component("GoldSrc Engine", "", EngineType.GOLDSRC, steps=steps("fetch", "build", "install")),
            make_component("Half-Life", "valve", EngineType.GOLDSRC, PatchStatus.ALREADY_PATCHED, steps=steps("fetch")),
            make_component("Opposing Force", "gearbox", EngineType.GOLDSRC, steps=steps("fetch", "install")),
        ]),
        Game("Portal", mock_steam_library / "Portal", EngineType.SOURCE, [
            make_component("Portal", "portal", EngineType.SOURCE, PatchStatus.ALREADY_PATCHED, steps=steps("install")),
        ]),
        Game("Half-Life 2", mock_steam_library / "Half-Life 2", EngineType.SOURCE, [
            make_component("Half-Life 2", "hl2", EngineType.SOURCE, steps=steps("build", "install")),
        ]),
    ]


def test_runs_every_step_of_the_components_that_need_patching_in_order(games, make_patcher, events):
    make_patcher().run(games)

    assert events == [
        ("component", "GoldSrc Engine"),
        ("step", 1, 3), ("run", "GoldSrc Engine", "fetch"),
        ("step", 2, 3), ("run", "GoldSrc Engine", "build"),
        ("step", 3, 3), ("run", "GoldSrc Engine", "install"),
        ("component", "Opposing Force"),
        ("step", 1, 2), ("run", "Opposing Force", "fetch"),
        ("step", 2, 2), ("run", "Opposing Force", "install"),
        ("component", "Half-Life 2"),
        ("step", 1, 2), ("run", "Half-Life 2", "build"),
        ("step", 2, 2), ("run", "Half-Life 2", "install"),
    ]


def test_total_steps_matches_the_components_announced_during_the_run(games, make_patcher, events):
    patcher = make_patcher()

    total = patcher.get_total_steps(games)
    patcher.run(games)

    assert total == [event[0] for event in events].count("component") == 3


def test_all_steps_of_a_run_share_one_context(mock_patch_context, games, actions, mock_run_command):
    mock_patch_context.patch_mode = PatchMode.STABLE
    contexts = []
    actions["install"] = lambda context, game, comp: contexts.append(context)
    patcher = Patcher(mock_patch_context, AppConfig())

    patcher.run(games)

    context = contexts[0]
    assert len(contexts) == 3
    assert all(other is context for other in contexts)
    assert context.executor is patcher.executor
    assert (context.working_dir, context.script_dir, context.steam_library_path, context.patch_mode) == (
        mock_patch_context.working_dir, mock_patch_context.script_dir, mock_patch_context.steam_library_path,
        PatchMode.STABLE,
    )


def test_step_messages_reach_the_log(games, make_patcher, actions, caplog):
    actions["fetch"] = lambda context, game, comp: context.log(f"Cloning {comp.name}...")

    with caplog.at_level(logging.INFO):
        make_patcher().run(games)

    assert "Cloning Opposing Force..." in caplog.messages


def test_starts_from_an_empty_working_dir_with_a_venv_for_the_build_tools(mock_patch_context, make_patcher,
                                                                          mock_run_command):
    working_dir = mock_patch_context.working_dir
    (working_dir / "hlsdk-portable-hlfixed").mkdir()

    make_patcher(debug=True).run([])

    assert list(working_dir.iterdir()) == []
    assert mock_run_command.commands == [
        (["python3", "-m", "venv", str(working_dir / "venv")], None),
        ([str(working_dir / "venv" / "bin" / "pip"), "install", "cmake", "ninja", "meson"], None),
    ]


@pytest.mark.parametrize("debug", [False, True], ids=["normal", "debug"])
def test_removes_the_working_dir_afterwards_unless_debugging(mock_patch_context, games, make_patcher, debug):
    make_patcher(debug=debug).run(games)

    assert mock_patch_context.working_dir.exists() is debug


def test_a_failing_step_ends_the_run(games, make_patcher, actions, events):
    def fail(context, game, comp):
        raise subprocess.CalledProcessError(1, ["./waf", "build"])

    actions["build"] = fail

    with pytest.raises(subprocess.CalledProcessError):
        make_patcher().run(games)

    assert ran(events) == [("GoldSrc Engine", "fetch"), ("GoldSrc Engine", "build")]


def test_keeps_a_timeline_of_the_steps_up_to_the_one_that_failed(games, make_patcher, actions):
    def fail_on_half_life_2(context, game, comp):
        if comp.name == "Half-Life 2":
            raise subprocess.CalledProcessError(1, ["./waf", "build"])

    actions["build"] = fail_on_half_life_2
    patcher = make_patcher()

    with pytest.raises(subprocess.CalledProcessError):
        patcher.run(games)

    assert [(r.game.name, r.component.name, r.number, r.total, r.config.type) for r in patcher.timeline] == [
        ("Half-Life", "GoldSrc Engine", 1, 3, "fetch"),
        ("Half-Life", "GoldSrc Engine", 2, 3, "build"),
        ("Half-Life", "GoldSrc Engine", 3, 3, "install"),
        ("Half-Life", "Opposing Force", 1, 2, "fetch"),
        ("Half-Life", "Opposing Force", 2, 2, "install"),
        ("Half-Life 2", "Half-Life 2", 1, 2, "build"),
    ]
    *finished, failed = patcher.timeline
    assert all(r.started <= r.finished <= after.started for r, after in zip(finished, patcher.timeline[1:]))
    assert failed.finished is None


def test_rejects_a_step_type_that_is_not_registered(mock_steam_library, make_component, make_patcher):
    game = Game("Half-Life", mock_steam_library / "Half-Life", EngineType.GOLDSRC, [
        make_component("Half-Life", "valve", EngineType.GOLDSRC, steps=steps("svn-fetcher")),
    ])

    with pytest.raises(ValueError, match="Unknown step type: svn-fetcher"):
        make_patcher().run([game])


def stop_then_run(patcher, component, cmd):
    def action(context, game, comp):
        if comp.name == component:
            patcher.stop()
            context.executor.run(cmd)

    return action


def test_stop_lets_a_non_interruptible_step_finish_and_starts_no_other(games, make_patcher, actions, events,
                                                                       mock_run_command):
    patcher = make_patcher()
    relink = ["install_name_tool", "-change", "@rpath/libSDL2.dylib", "@loader_path/libSDL2.dylib", "xash3d"]
    actions["install"] = stop_then_run(patcher, "GoldSrc Engine", relink)

    with pytest.raises(RuntimeError, match="Execution stopped by user"):
        patcher.run(games)

    assert mock_run_command.commands[-1] == (relink, None)
    assert ran(events)[-1] == ("GoldSrc Engine", "install")


def test_stop_cuts_off_an_interruptible_step_even_after_a_non_interruptible_one(games, make_patcher, actions, events,
                                                                                mock_run_command):
    patcher = make_patcher()
    clone = ["git", "clone", HLSDK_URL]
    actions["fetch"] = stop_then_run(patcher, "Opposing Force", clone)

    with pytest.raises(RuntimeError, match="Execution stopped by user"):
        patcher.run(games)

    assert clone not in [cmd for cmd, _ in mock_run_command.commands]
    assert ran(events)[-1] == ("Opposing Force", "fetch")


@pytest.fixture
def documents(mocker, tmp_path):
    mocker.patch("pathlib.Path.home", return_value=tmp_path / "home")
    clock = mocker.patch("patcher.core.patcher.datetime")
    clock.now.return_value = datetime(2026, 9, 27, 18, 30, tzinfo=timezone.utc)
    return tmp_path / "home" / "Documents"


@pytest.fixture
def patched_launcher(games, actions):
    launcher = games[0].path / "hl_osx"
    launcher.write_bytes(b"valve launcher")
    actions["install"] = lambda context, game, comp: (game.path / "hl_osx").write_bytes(b"xash3d launcher")
    return launcher


def test_backs_up_the_games_being_patched_before_any_step_runs(mock_patch_context, games, make_patcher, documents,
                                                               patched_launcher):
    mock_patch_context.create_backup = True

    make_patcher().run(games)

    assert sorted(backup.name for backup in documents.iterdir()) == [
        "Half-Life 2 backup (2026-09-27)", "Half-Life backup (2026-09-27)",
    ]
    assert (documents / "Half-Life backup (2026-09-27)" / "hl_osx").read_bytes() == b"valve launcher"
    assert patched_launcher.read_bytes() == b"xash3d launcher"


@pytest.mark.parametrize(("create_backup", "names"), [
    (False, ["Half-Life", "Portal", "Half-Life 2"]),
    (True, ["Portal"]),
], ids=["turned-off", "nothing-to-patch"])
def test_makes_no_backup_when_turned_off_or_nothing_needs_patching(mock_patch_context, games, make_patcher, documents,
                                                                   caplog, create_backup, names):
    mock_patch_context.create_backup = create_backup

    with caplog.at_level(logging.INFO):
        make_patcher().run([game for game in games if game.name in names])

    assert not documents.exists()
    assert "Creating backup..." not in caplog.messages


def test_patching_another_component_the_same_day_keeps_the_first_backup(mock_patch_context, games, make_component,
                                                                        make_patcher, documents, patched_launcher):
    mock_patch_context.create_backup = True
    half_life = games[0]
    make_patcher().run([half_life])

    blue_shift = make_component("Blue Shift", "bshift", EngineType.GOLDSRC, steps=steps("fetch"))
    make_patcher().run([replace(half_life, components=[blue_shift])])

    assert (documents / "Half-Life backup (2026-09-27)" / "hl_osx").read_bytes() == b"valve launcher"


def test_a_backup_cut_short_is_made_again_on_the_next_run(mock_patch_context, games, make_patcher, documents,
                                                          patched_launcher, mocker):
    mock_patch_context.create_backup = True
    copytree = shutil.copytree

    def run_out_of_space(source, destination, **kwargs):
        copytree(source, destination, **kwargs)
        (Path(destination) / "hl_osx").write_bytes(b"half copied")
        raise OSError(28, "No space left on device")

    mocker.patch("shutil.copytree", side_effect=run_out_of_space)
    with pytest.raises(OSError, match="No space left on device"):
        make_patcher().run([games[0]])

    mocker.patch("shutil.copytree", side_effect=copytree)
    make_patcher().run([games[0]])

    assert sorted(backup.name for backup in documents.iterdir()) == ["Half-Life backup (2026-09-27)"]
    assert (documents / "Half-Life backup (2026-09-27)" / "hl_osx").read_bytes() == b"valve launcher"
