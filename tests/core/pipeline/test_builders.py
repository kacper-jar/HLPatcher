import subprocess

import pytest

from patcher.core import BuildStepConfig, EngineType, Game
from patcher.core.pipeline.builders import CMakeBuilder, WafBuilder


@pytest.fixture
def build(step_context, make_component):
    comp = make_component("Half-Life", "valve", engine_type=EngineType.GOLDSRC)
    game = Game("Half-Life", step_context.steam_library_path / "Half-Life", EngineType.GOLDSRC, [comp])
    return lambda step_class, config: step_class(step_context).execute(game, comp, config)


def test_waf_builder_configures_builds_and_installs_in_one_command(step_context, build, mock_run_command):
    build(WafBuilder, BuildStepConfig("waf-builder", patch_dir_name="hlsdk-portable-hlfixed",
                                      build_args=["-T", "release", "-8"]))

    mod_dir = step_context.working_dir / "hlsdk-portable-hlfixed"
    assert mock_run_command.commands == [
        (["./waf", "configure", "-T", "release", "-8", "build", "install", f"--destdir={mod_dir / 'output'}"],
         str(mod_dir)),
    ]
    step_context.log.assert_any_call("Building hlsdk-portable-hlfixed...")


def test_waf_builder_fills_in_the_working_dir(step_context, build, mock_run_command):
    build(WafBuilder, BuildStepConfig("waf-builder", patch_dir_name="xash3d-fwgs", build_args=[
        "-8", "--enable-bundled-deps", "--sdl2={working_dir}/xash3d-fwgs/3rdparty/SDL2.framework",
    ]))

    cmd, _ = mock_run_command.commands[0]
    assert cmd[2:5] == ["-8", "--enable-bundled-deps",
                        f"--sdl2={step_context.working_dir}/xash3d-fwgs/3rdparty/SDL2.framework"]


def test_waf_builder_passes_source_engine_arguments_through(step_context, build, mock_run_command):
    build(WafBuilder, BuildStepConfig("waf-builder", patch_dir_name="source-engine", waf_game="dod",
                                      build_args=["-T", "release", "--prefix=", "--build-games=dod"]))

    cmd, cwd = mock_run_command.commands[0]
    assert cmd[:6] == ["./waf", "configure", "-T", "release", "--prefix=", "--build-games=dod"]
    assert cwd == str(step_context.working_dir / "source-engine")


def test_cmake_builder_runs_the_full_sequence_with_the_venv_python(step_context, build, mock_run_command):
    build(CMakeBuilder, BuildStepConfig("cmake-builder", patch_dir_name="cs16-client"))

    python = str(step_context.working_dir / "venv" / "bin" / "python3")
    mod_dir = step_context.working_dir / "cs16-client"
    assert mock_run_command.commands == [
        ([python, "build_deps.py"], str(mod_dir)),
        ([python, "-m", "cmake", "-S", ".", "-B", "build", "-G", "Ninja"], str(mod_dir)),
        ([python, "-m", "cmake", "--build", "build", "--config", "Release"], str(mod_dir)),
        ([python, "-m", "cmake", "--install", "build", "--prefix", str(mod_dir / "output")], str(mod_dir)),
    ]


def test_cmake_builder_stops_at_the_first_failing_command(build, mocker):
    commands = []

    def popen(cmd, *args, **kwargs):
        commands.append(cmd)
        process = mocker.Mock(args=cmd)
        process.communicate.return_value = ("", "fetching dependencies failed")
        process.poll.return_value = 1
        return process

    mocker.patch("subprocess.Popen", side_effect=popen)

    with pytest.raises(subprocess.CalledProcessError):
        build(CMakeBuilder, BuildStepConfig("cmake-builder", patch_dir_name="cs16-client"))

    assert len(commands) == 1
    assert commands[0][1] == "build_deps.py"
