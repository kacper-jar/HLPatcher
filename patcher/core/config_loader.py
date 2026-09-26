import json
from pathlib import Path
from typing import Any

from patcher.core.models import EngineType, GameConfig

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_components_config() -> list[dict[str, Any]]:
    return _load_data_file("components.json")


def load_games_config() -> list[GameConfig]:
    return [
        GameConfig(**{**data, "engine_type": EngineType(data["engine_type"])})
        for data in _load_data_file("games.json")
    ]


def _load_data_file(file_name: str) -> list[dict[str, Any]]:
    with open(DATA_DIR / file_name) as f:
        return json.load(f)
