import json
from pathlib import Path
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class I18n:
    def __init__(self, locales_dir: Path):
        self.locales_dir = locales_dir
        self.current_lang = "en"
        self.translations: dict[str, str] = {}
        self.available_langs: list[str] = []
        self.on_language_changed: Optional[Callable[[str], None]] = None
        self._scan_locales()
        self.set_language(self.current_lang, notify=False)

    def _scan_locales(self):
        if not self.locales_dir.exists():
            logger.warning(f"Locales directory {self.locales_dir} does not exist.")
            return

        self.available_langs = []
        for file in self.locales_dir.glob("*.json"):
            self.available_langs.append(file.stem)

        if "en" not in self.available_langs:
            self.available_langs.append("en")

    def set_language(self, lang_code: str, notify: bool = True):
        if lang_code not in self.available_langs and lang_code != "en":
            logger.warning(f"Language {lang_code} not available, falling back to en.")
            lang_code = "en"

        file_path = self.locales_dir / f"{lang_code}.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
                self.current_lang = lang_code
            except Exception as e:
                logger.error(f"Failed to load language {lang_code}: {e}")
        else:
            self.translations = {}
            self.current_lang = lang_code

        if notify and self.on_language_changed:
            self.on_language_changed(self.current_lang)

    def t(self, key: str, **kwargs) -> str:
        text = self.translations.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

    def get_language_name(self, lang_code: str) -> str:
        return self.t(f"lang_{lang_code}")
