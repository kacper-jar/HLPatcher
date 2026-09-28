import json

import pytest

from patcher.core import EngineType, GameConfig
from patcher.core.config_loader import DATA_DIR, load_components_config, load_games_config

HALF_LIFE = {"id": "half-life", "folder": "Half-Life", "executable": "hl_osx", "engine_type": "GoldSrc"}


@pytest.fixture
def data_dir(tmp_path, mocker):
    mocker.patch("patcher.core.config_loader.DATA_DIR", tmp_path)
    return tmp_path


def write(data_dir, file_name, data):
    (data_dir / file_name).write_text(json.dumps(data), encoding="utf-8")


def test_reads_the_data_folder_shipped_with_the_patcher(pytestconfig):
    assert DATA_DIR == pytestconfig.rootpath.resolve() / "data"


def test_turns_each_game_into_a_game_config(data_dir):
    write(data_dir, "games.json", [
        HALF_LIFE,
        {"id": "day-of-defeat-source", "folder": "Day of Defeat Source", "executable": "hl2_osx",
         "engine_type": "Source", "fallback_marker": "gameinfo.txt"},
    ])

    assert load_games_config() == [
        GameConfig("half-life", "Half-Life", "hl_osx", EngineType.GOLDSRC),
        GameConfig("day-of-defeat-source", "Day of Defeat Source", "hl2_osx", EngineType.SOURCE, "gameinfo.txt"),
    ]


@pytest.mark.parametrize(("game", "error", "message"), [
    ({**HALF_LIFE, "engine_type": "Xash3D"}, ValueError, "'Xash3D' is not a valid EngineType"),
    ({**HALF_LIFE, "exe": "hl_osx"}, TypeError, "unexpected keyword argument 'exe'"),
    ({key: value for key, value in HALF_LIFE.items() if key != "executable"}, TypeError,
     "missing 1 required positional argument: 'executable'"),
], ids=["unknown-engine", "misspelled-field", "missing-field"])
def test_rejects_a_game_it_cannot_read(data_dir, game, error, message):
    write(data_dir, "games.json", [game])

    with pytest.raises(error, match=message):
        load_games_config()


def test_returns_the_components_as_written(data_dir):
    components = [{"id": "half-life", "name": "Half-Life", "game": "half-life", "subfolder": "valve",
                   "depends_on": ["goldsrc-engine"], "steps": [{"type": "patch", "patch_dir_name": "hlsdk"}]}]
    write(data_dir, "components.json", components)

    assert load_components_config() == components


@pytest.mark.parametrize(("loader", "file_name"), [
    (load_games_config, "games.json"),
    (load_components_config, "components.json"),
], ids=["games", "components"])
@pytest.mark.parametrize(("content", "error"), [
    (None, FileNotFoundError),
    ("[{", json.JSONDecodeError),
], ids=["missing", "broken"])
def test_fails_loudly_without_a_readable_data_file(data_dir, loader, file_name, content, error):
    if content is not None:
        (data_dir / file_name).write_text(content, encoding="utf-8")

    with pytest.raises(error):
        loader()
