import json
from pathlib import Path
from typing import Any


def load_components_config() -> list[dict[str, Any]]:
    project_root = Path(__file__).resolve().parent.parent.parent
    config_path = project_root / "data" / "components.json"

    with open(config_path, "r") as f:
        return json.load(f)
