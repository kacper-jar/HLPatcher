import json
import logging
from pathlib import Path

from patcher.core.models import GuideConfig, GuideStepConfig

logger = logging.getLogger(__name__)


class GuideRegistry:
    def __init__(self, guides_dir: Path):
        self._guides_dir = guides_dir
        self._guides: dict[str, GuideConfig] = {}
        self._load_all()

    def _load_all(self):
        if not self._guides_dir.is_dir():
            logger.warning(f"Guides directory not found at {self._guides_dir}")
            return

        for json_path in self._guides_dir.glob("*.json"):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                steps = []
                for step_data in data.get("steps", []):
                    steps.append(GuideStepConfig(
                        step_title=step_data.get("step_title", ""),
                        step_description=step_data.get("step_description", ""),
                        step_command=step_data.get("step_command", ""),
                        step_button_text=step_data.get("step_button_text", ""),
                        step_button_url=step_data.get("step_button_url", "")
                    ))

                config = GuideConfig(
                    title=data.get("title", json_path.stem),
                    steps=steps
                )

                self._guides[json_path.stem] = config
                logger.info(f"Loaded guide configuration for '{json_path.stem}'")
            except Exception as e:
                logger.error(f"Failed to load guide {json_path}: {e}")

    def get_guide(self, subfolder: str) -> GuideConfig | None:
        return self._guides.get(subfolder)
