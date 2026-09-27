import json

import pytest

from patcher.core import EngineType, GameDetector, PatchStatus
from patcher.core.pipeline import parse_step_config

PATCHED = PatchStatus.ALREADY_PATCHED
UNPATCHED = PatchStatus.NEEDS_PATCH

DEFINITION_FIELDS = {
    "name": "name",
    "subfolder": "subfolder",
    "downgrade_group": "downgrade_group",
    "downgrade_requires": "downgrade_requires",
    "depends_on": "depends_on",
    "auto_select": "auto_select",
    "estimated_time": "estimated_patch_time",
    "estimated_space": "estimated_free_space_required",
}


def touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def components_by_id(games):
    return {comp.id: comp for game in games for comp in game.components}


@pytest.fixture
def definitions(pytestconfig):
    return json.loads((pytestconfig.rootpath / "data" / "components.json").read_text())


@pytest.fixture
def game_configs(pytestconfig):
    return {game["id"]: game for game in json.loads((pytestconfig.rootpath / "data" / "games.json").read_text())}


@pytest.fixture
def full_library(tmp_path, definitions, game_configs):
    for game in game_configs.values():
        touch(tmp_path / game["folder"] / game["executable"])
    for definition in definitions:
        (tmp_path / game_configs[definition["game"]]["folder"] / definition["subfolder"]).mkdir(exist_ok=True)
    return tmp_path


def test_finds_nothing_in_an_empty_library(tmp_path):
    assert GameDetector(tmp_path).scan() == []


def test_finds_every_supported_game_in_games_json_order(full_library, game_configs):
    games = GameDetector(full_library).scan()

    assert [game.name for game in games] == [
        "GoldSrc (Half-Life)", "Source (Half-Life 2)", "Source (Portal)", "Source (Half-Life 2 Deathmatch)",
        "Source (Day of Defeat Source)", "Source (Counter-Strike Source)",
    ]
    assert [(game.path, game.engine_type) for game in games] == [
        (full_library / config["folder"], EngineType(config["engine_type"])) for config in game_configs.values()
    ]


def test_lists_only_the_components_whose_folders_exist(mock_steam_library):
    for folder in ["valve", "gearbox", "cstrike"]:
        (mock_steam_library / "Half-Life" / folder).mkdir()
    for folder in ["hl2", "episodic"]:
        (mock_steam_library / "Half-Life 2" / folder).mkdir()

    games = GameDetector(mock_steam_library).scan()

    assert {game.name: [comp.id for comp in game.components] for game in games} == {
        "GoldSrc (Half-Life)": ["goldsrc-engine", "half-life", "opposing-force", "counter-strike"],
        "Source (Half-Life 2)": ["half-life-2", "episodic"],
        "Source (Half-Life 2 Deathmatch)": ["half-life-2-deathmatch"],
        "Source (Day of Defeat Source)": ["day-of-defeat-source"],
        "Source (Counter-Strike Source)": ["counter-strike-source"],
    }


def test_every_component_carries_its_definition(full_library, definitions, game_configs):
    detected = components_by_id(GameDetector(full_library).scan())

    assert detected.keys() == {definition["id"] for definition in definitions}
    for definition in definitions:
        comp = detected[definition["id"]]
        present = {key: attr for key, attr in DEFINITION_FIELDS.items() if key in definition}
        assert {attr: getattr(comp, attr) for attr in present.values()} == {
            attr: definition[key] for key, attr in present.items()
        }
        assert comp.engine_type == EngineType(game_configs[definition["game"]]["engine_type"])
        assert comp.steps == [parse_step_config(step) for step in definition["steps"]]


@pytest.mark.parametrize(("folder", "comp_id", "files", "status"), [
    ("Half-Life", "goldsrc-engine", ["libxash.dylib", "libmenu.dylib", "SDL2.framework/SDL2"], PATCHED),
    ("Half-Life", "goldsrc-engine", ["libxash.dylib", "SDL2.framework/SDL2"], UNPATCHED),
    ("Half-Life", "goldsrc-engine", ["libxash.dylib", "libmenu.dylib"], UNPATCHED),
    ("Half-Life", "half-life", ["valve/dlls/hl_arm64.dylib"], PATCHED),
    ("Half-Life", "half-life", ["valve/cl_dlls/client_arm64.dylib"], PATCHED),
    ("Half-Life", "half-life", ["valve/dlls/hl.dylib"], UNPATCHED),
    ("Half-Life 2", "half-life-2", ["hl2/bin/libclient.dylib", "hl2/bin/libserver.dylib"], PATCHED),
    ("Half-Life 2", "half-life-2", ["hl2/bin/libclient.dylib"], UNPATCHED),
    ("Half-Life 2", "half-life-2", ["hl2/bin/client.dylib", "hl2/bin/server.dylib"], UNPATCHED),
], ids=["engine", "engine-without-menu", "engine-without-sdl2", "mod-server", "mod-client", "mod-original",
        "source", "source-without-server", "source-original"])
def test_detects_whether_a_component_is_already_patched(mock_steam_library, folder, comp_id, files, status):
    for file in files:
        touch(mock_steam_library / folder / file)

    components = components_by_id(GameDetector(mock_steam_library).scan())

    assert components[comp_id].status == status


@pytest.mark.parametrize(("folder", "file", "found"), [
    ("Half-Life 2 Deathmatch", "hl2mp/gameinfo.txt", True),
    ("Day of Defeat Source", "dod/gameinfo.txt", True),
    ("Counter-Strike Source", "cstrike/gameinfo.txt", True),
    ("Counter-Strike Source", "cstrike/maps/de_dust2.bsp", False),
    ("Half-Life 2", "hl2/gameinfo.txt", False),
    ("Portal", "portal/gameinfo.txt", False),
    ("Half-Life", "valve/liblist.gam", False),
], ids=["hl2dm", "dods", "css", "css-without-gameinfo", "hl2", "portal", "half-life"])
def test_finds_only_multiplayer_games_by_gameinfo_when_the_launcher_is_missing(tmp_path, folder, file, found):
    touch(tmp_path / folder / file)

    games = GameDetector(tmp_path).scan()

    assert [game.path for game in games] == ([tmp_path / folder] if found else [])


@pytest.mark.parametrize(("comp_id", "changes", "message"), [
    ("portal", {"game": "portal-2"}, "Components with an unknown game: Portal$"),
    ("lost-coast", {"id": "half-life-2"}, "Duplicate component ids: half-life-2$"),
    ("day-of-defeat-source", {"depends_on": ["half-life-2-episode-two"]},
     "Components depending on unknown components: Day of Defeat: Source$"),
    ("half-life", {"steps": [{"type": "svn-fetcher"}]}, "Invalid step in Half-Life: Unknown step type: 'svn-fetcher'$"),
    ("half-life", {"steps": [{"type": "git-fetcher", "brnch": "hlfixed"}]},
     "Invalid step in Half-Life: .*unexpected keyword argument 'brnch'"),
], ids=["unknown-game", "duplicate-id", "unknown-dependency", "unknown-step-type", "unknown-step-field"])
def test_rejects_broken_component_data(tmp_path, definitions, mocker, comp_id, changes, message):
    next(definition for definition in definitions if definition["id"] == comp_id).update(changes)
    mocker.patch("patcher.core.game_detector.load_components_config", return_value=definitions)

    with pytest.raises(ValueError, match=message):
        GameDetector(tmp_path)
