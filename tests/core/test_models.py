from pathlib import Path

from patcher.core.models import Component, EngineType, Game, PatchStatus


def test_component_needs_patch():
    comp = Component("Test", "test", EngineType.SOURCE, PatchStatus.NEEDS_PATCH, "")
    assert comp.needs_patch is True

    comp.status = PatchStatus.ALREADY_PATCHED
    assert comp.needs_patch is False


def test_game_needs_patch():
    comp1 = Component("Test1", "test1", EngineType.SOURCE, PatchStatus.ALREADY_PATCHED, "")
    comp2 = Component("Test2", "test2", EngineType.SOURCE, PatchStatus.NEEDS_PATCH, "")
    game = Game("TestGame", Path("/fake"), EngineType.SOURCE, [comp1, comp2])

    assert game.needs_patch is True

    comp2.status = PatchStatus.ALREADY_PATCHED
    assert game.needs_patch is False


def test_game_all_patched():
    comp1 = Component("Test1", "test1", EngineType.SOURCE, PatchStatus.ALREADY_PATCHED, "")
    comp2 = Component("Test2", "test2", EngineType.SOURCE, PatchStatus.NEEDS_PATCH, "")
    game = Game("TestGame", Path("/fake"), EngineType.SOURCE, [comp1, comp2])

    assert game.all_patched is False

    comp2.status = PatchStatus.ALREADY_PATCHED
    assert game.all_patched is True


def test_game_has_source_components():
    comp1 = Component("Test1", "test1", EngineType.GOLDSRC, PatchStatus.NEEDS_PATCH, "")
    game = Game("TestGame", Path("/fake"), EngineType.GOLDSRC, [comp1])

    assert game.has_source_components is False

    comp2 = Component("Test2", "test2", EngineType.SOURCE, PatchStatus.NEEDS_PATCH, "")
    game.components.append(comp2)

    assert game.has_source_components is True
