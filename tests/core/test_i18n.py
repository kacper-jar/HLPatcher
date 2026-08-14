import json
import pytest
from unittest.mock import Mock

from patcher.core.i18n import I18n


@pytest.fixture
def mock_locales_dir(tmp_path):
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()

    en_data = {
        "hello": "Hello",
        "greeting": "Hello {name}",
        "lang_en-US": "English",
        "lang_pl-PL": "Polski"
    }
    with open(locales_dir / "en-US.json", "w", encoding="utf-8") as f:
        json.dump(en_data, f)

    pl_data = {
        "hello": "Cześć",
        "greeting": "Cześć {name}",
        "lang_en-US": "English",
        "lang_pl-PL": "Polski"
    }
    with open(locales_dir / "pl-PL.json", "w", encoding="utf-8") as f:
        json.dump(pl_data, f)

    return locales_dir


def test_i18n_initialization(mock_locales_dir):
    i18n = I18n(mock_locales_dir)
    assert i18n.current_lang == "en-US"
    assert set(i18n.available_langs) == {"en-US", "pl-PL"}
    assert i18n.translations["hello"] == "Hello"


def test_i18n_translation(mock_locales_dir):
    i18n = I18n(mock_locales_dir)
    assert i18n.t("hello") == "Hello"
    assert i18n.t("missing_key") == "missing_key"


def test_i18n_translation_with_kwargs(mock_locales_dir):
    i18n = I18n(mock_locales_dir)
    assert i18n.t("greeting", name="John") == "Hello John"


def test_i18n_set_language(mock_locales_dir):
    i18n = I18n(mock_locales_dir)
    assert i18n.t("hello") == "Hello"

    i18n.set_language("pl-PL")
    assert i18n.current_lang == "pl-PL"
    assert i18n.t("hello") == "Cześć"
    assert i18n.t("greeting", name="Jan") == "Cześć Jan"


def test_i18n_fallback_to_en_us(mock_locales_dir):
    i18n = I18n(mock_locales_dir)
    i18n.set_language("non_existent_lang")

    assert i18n.current_lang == "en-US"
    assert i18n.t("hello") == "Hello"


def test_i18n_on_language_changed_callback(mock_locales_dir):
    i18n = I18n(mock_locales_dir)
    mock_callback = Mock()
    i18n.on_language_changed = mock_callback

    i18n.set_language("pl-PL")
    mock_callback.assert_called_once_with("pl-PL")


def test_i18n_get_language_name(mock_locales_dir):
    i18n = I18n(mock_locales_dir)
    assert i18n.get_language_name("en-US") == "English"
    assert i18n.get_language_name("pl-PL") == "Polski"
