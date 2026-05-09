from pathlib import Path

from patcher.core.game_detector import GameDetector
from patcher.core.models import EngineType, PatchStatus


def test_scan_empty_library(tmp_path):
    detector = GameDetector(tmp_path)
    games = detector.scan()
    assert len(games) == 0


def test_detect_goldsrc_unpatched(mock_steam_library):
    detector = GameDetector(mock_steam_library)
    games = detector.scan()

    goldsrc = next((g for g in games if g.engine_type == EngineType.GOLDSRC), None)
    assert goldsrc is not None
    assert goldsrc.name == "GoldSrc (Half-Life)"

    engine_comp = next((c for c in goldsrc.components if c.name == "GoldSrc Engine"), None)
    assert engine_comp is not None
    assert engine_comp.status == PatchStatus.NEEDS_PATCH


def test_detect_goldsrc_patched(mock_steam_library):
    goldsrc_dir = mock_steam_library / "Half-Life"
    (goldsrc_dir / "libxash.dylib").touch()
    (goldsrc_dir / "libmenu.dylib").touch()
    (goldsrc_dir / "SDL2.framework").mkdir()

    valve_dir = goldsrc_dir / "valve"
    valve_dir.mkdir()
    (valve_dir / "dlls").mkdir()
    (valve_dir / "dlls" / "hl_arm64.dylib").touch()

    detector = GameDetector(mock_steam_library)
    games = detector.scan()

    goldsrc = next((g for g in games if g.engine_type == EngineType.GOLDSRC), None)
    engine_comp = next((c for c in goldsrc.components if c.name == "GoldSrc Engine"), None)
    assert engine_comp.status == PatchStatus.ALREADY_PATCHED

    hl_comp = next((c for c in goldsrc.components if c.name == "Half-Life"), None)
    assert hl_comp is not None
    assert hl_comp.status == PatchStatus.ALREADY_PATCHED


def test_detect_source_unpatched(mock_steam_library):
    hl2_dir = mock_steam_library / "Half-Life 2"
    (hl2_dir / "hl2").mkdir()

    detector = GameDetector(mock_steam_library)
    games = detector.scan()

    hl2 = next((g for g in games if g.name == "Source (Half-Life 2)"), None)
    assert hl2 is not None

    hl2_comp = next((c for c in hl2.components if c.subfolder == "hl2"), None)
    assert hl2_comp is not None
    assert hl2_comp.status == PatchStatus.NEEDS_PATCH


def test_detect_source_patched(mock_steam_library):
    hl2_dir = mock_steam_library / "Half-Life 2"
    hl2_mod_dir = hl2_dir / "hl2"
    hl2_mod_dir.mkdir()
    (hl2_mod_dir / "bin").mkdir()
    (hl2_mod_dir / "bin" / "libclient.dylib").touch()
    (hl2_mod_dir / "bin" / "libserver.dylib").touch()

    detector = GameDetector(mock_steam_library)
    games = detector.scan()

    hl2 = next((g for g in games if g.name == "Source (Half-Life 2)"), None)
    hl2_comp = next((c for c in hl2.components if c.subfolder == "hl2"), None)
    assert hl2_comp.status == PatchStatus.ALREADY_PATCHED
