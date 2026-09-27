import difflib

import pytest

from patcher.core import EngineType, Game, PatchStepConfig
from patcher.core.pipeline.misc import PatchStep

ORIGINAL = "".join(f"{n}\n" for n in range(1, 11))
AFTER_FIRST = ORIGINAL.replace("\n5\n", "\nfive\n")
AFTER_SECOND = AFTER_FIRST.replace("\nfive\n", "\nfive!\n")


def make_patch(before, after):
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), "base/a.txt", "work/a.txt"))


@pytest.fixture
def project(step_context):
    target = step_context.working_dir / "proj"
    target.mkdir()
    (target / "a.txt").write_text(ORIGINAL)
    return target


@pytest.fixture
def container(step_context):
    path = step_context.script_dir / "data" / "fixes" / "src" / "proj-base"
    path.mkdir()
    return path


@pytest.fixture
def patches(container):
    (container / "01_first.patch").write_text(make_patch(ORIGINAL, AFTER_FIRST))
    (container / "02_second.patch").write_text(make_patch(AFTER_FIRST, AFTER_SECOND))
    return container


@pytest.fixture
def run_patch_step(step_context, make_component):
    comp = make_component()
    game = Game("Test", step_context.working_dir, EngineType.SOURCE, [comp])
    step = PatchStep(step_context)
    return lambda: step.execute(game, comp, PatchStepConfig("patch", patch_dir_name="proj"))


def test_applies_patches_in_file_name_order(project, patches, run_patch_step):
    run_patch_step()

    assert (project / "a.txt").read_text() == AFTER_SECOND


def test_skips_a_patch_that_is_already_applied(project, patches, run_patch_step, step_context):
    (project / "a.txt").write_text(AFTER_FIRST)

    run_patch_step()

    assert (project / "a.txt").read_text() == AFTER_SECOND
    step_context.log.assert_any_call("Patch 01_first.patch is already applied, skipping")


def test_conflicting_patch_stops_the_build(project, patches, run_patch_step):
    conflicting = ORIGINAL.replace("\n5\n", "\nFIVE-UPSTREAM\n")
    (project / "a.txt").write_text(conflicting)

    with pytest.raises(RuntimeError, match="Patch 01_first.patch failed to apply to proj"):
        run_patch_step()

    assert "five!" not in (project / "a.txt").read_text()


def test_missing_file_to_patch_stops_the_build(project, patches, run_patch_step):
    (project / "a.txt").unlink()

    with pytest.raises(RuntimeError, match="Patch 01_first.patch failed to apply to proj"):
        run_patch_step()


def test_missing_patch_folder_is_skipped(project, run_patch_step, step_context):
    run_patch_step()

    assert (project / "a.txt").read_text() == ORIGINAL
    step_context.log.assert_any_call("No patch directory found for container proj-base")
    assert ("proj", "proj-base") in step_context.applied_patch_containers


def test_empty_patch_folder_is_skipped(project, container, run_patch_step, step_context):
    run_patch_step()

    assert (project / "a.txt").read_text() == ORIGINAL
    step_context.log.assert_any_call(f"No patches found in {container}")


def test_patch_folder_is_applied_once_per_run(project, patches, run_patch_step, step_context):
    run_patch_step()
    run_patch_step()

    assert (project / "a.txt").read_text() == AFTER_SECOND
    patching_messages = [c for c in step_context.log.call_args_list if c.args[0].startswith("Patching proj")]
    assert len(patching_messages) == 1
