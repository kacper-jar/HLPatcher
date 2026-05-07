from __future__ import annotations

import json
import logging
import urllib.request
from packaging import version
from patcher.core import UpdateInfo

logger = logging.getLogger(__name__)


class Updater:
    def __init__(self):
        self.api_url = "https://api.github.com/repos/kacper-jar/HLPatcher/releases/latest"

    def check_for_update(self, current_version: str) -> UpdateInfo | None:
        if current_version == "indev":
            logger.info("Running 'indev' version, skipping update check.")
            return None

        try:
            req = urllib.request.Request(
                self.api_url,
                headers={"User-Agent": "HLPatcher-Updater"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    logger.warning(f"Update check failed with status: {response.status}")
                    return None
                data = json.loads(response.read().decode())

            latest_version_str = data.get("tag_name", "").lstrip("v")
            release_url = data.get(
                "html_url", "https://github.com/kacper-jar/HLPatcher/releases"
            )

            if not latest_version_str:
                logger.warning("Could not find tag_name in GitHub response.")
                return None

            try:
                latest_v = version.parse(latest_version_str)
                current_v = version.parse(current_version)
                update_available = latest_v > current_v
            except version.InvalidVersion:
                logger.warning(
                    f"Invalid version format: latest={latest_version_str}, current={current_version}"
                )
                return None

            logger.info(
                f"Update check completed. Latest: {latest_version_str}, Update available: {update_available}"
            )
            return UpdateInfo(
                latest_version=latest_version_str,
                update_available=update_available,
                release_url=release_url,
            )
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return None
