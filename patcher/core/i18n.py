import json
import locale
import logging
import os
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class I18n:
    def __init__(self, locales_dir: Path):
        self.locales_dir = locales_dir
        self.translations: dict[str, str] = {}
        self.fallback_translations: dict[str, str] = {}
        self.available_langs: list[str] = []
        self.locale_names: dict[str, str] = {}
        self.on_language_changed: Callable[[str], None] | None = None
        self._load_fallback()
        self._scan_locales()

        try:
            loc, _ = locale.getlocale()
            if not loc:
                loc = os.environ.get("LANG", "en_US")
            default_lang = loc.split(".")[0].replace("_", "-")
        except Exception:
            default_lang = "en-US"

        if default_lang not in self.available_langs:
            lang_only = default_lang.split("-")[0]
            matches = [l for l in self.available_langs if l.startswith(f"{lang_only}-")]
            if matches:
                default_lang = matches[0]
            else:
                default_lang = "en-US"

        self.current_lang = default_lang
        self.set_language(self.current_lang, notify=False)

    def _load_fallback(self):
        fallback_path = self.locales_dir / "en-US.json"
        if fallback_path.exists():
            try:
                with open(fallback_path, encoding="utf-8") as f:
                    self.fallback_translations = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load fallback language en-US: {e}")

    def _scan_locales(self):
        if not self.locales_dir.exists():
            logger.warning(f"Locales directory {self.locales_dir} does not exist.")
            return

        index_file = self.locales_dir.parent / "locales.json"
        if index_file.exists():
            try:
                with open(index_file, encoding="utf-8") as f:
                    self.locale_names = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load locales.json: {e}")

        self.available_langs = []
        for file in self.locales_dir.glob("*.json"):
            try:
                with open(file, encoding="utf-8") as f:
                    data = json.load(f)
                    if not data:
                        continue
            except Exception:
                continue
            self.available_langs.append(file.stem)

        if "en-US" not in self.available_langs:
            self.available_langs.append("en-US")

    def set_language(self, lang_code: str, notify: bool = True):
        if lang_code not in self.available_langs and lang_code != "en-US":
            logger.warning(f"Language {lang_code} not available, falling back to en-US.")
            lang_code = "en-US"

        file_path = self.locales_dir / f"{lang_code}.json"
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
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
        text = self.translations.get(key, self.fallback_translations.get(key, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

    def get_language_name(self, lang_code: str) -> str:
        return self.locale_names.get(lang_code, lang_code)
