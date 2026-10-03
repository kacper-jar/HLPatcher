import json
import shutil
from pathlib import Path

import pytest

from patcher.core import I18n

ENGLISH = {
    "welcome_title": "Welcome to HLPatcher ({version})",
    "progress_time_format": "Elapsed time: {mins:02d}:{secs:02d}",
    "update_available_title": "Update available",
}
POLISH = {
    "welcome_title": "Witaj w HLPatcher ({version})",
    "progress_time_format": "Upłynęło czasu: {mins:02d}:{secs:02d}",
}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def locales_dir(tmp_path):
    write_json(tmp_path / "locales.json", {
        "en-US": "English", "pl-PL": "Polski", "de-DE": "Deutsch", "pt-BR": "Português (Brasil)",
        "sv-SE": "Svenska", "fi-FI": "Suomi",
    })
    locales = tmp_path / "locales"
    write_json(locales / "en-US.json", ENGLISH)
    write_json(locales / "pl-PL.json", POLISH)
    write_json(locales / "de-DE.json", {"welcome_title": "Willkommen bei HLPatcher ({version})"})
    write_json(locales / "pt-BR.json", {"welcome_title": "Bem-vindo ao HLPatcher ({version})"})
    write_json(locales / "sv-SE.json", {})
    (locales / "fi-FI.json").write_text("{", encoding="utf-8")
    return locales


@pytest.fixture(autouse=True)
def system_locale(mocker, monkeypatch):
    monkeypatch.delenv("LANG", raising=False)
    return mocker.patch("locale.getlocale", return_value=("en_US", "UTF-8"))


@pytest.fixture
def polish(locales_dir):
    i18n = I18n(locales_dir)
    i18n.set_language("pl-PL")
    return i18n


@pytest.mark.parametrize(("detected", "lang", "expected"), [
    (("pl_PL", "UTF-8"), None, "pl-PL"),
    (("de_AT", "UTF-8"), None, "de-DE"),
    (("sv_SE", "UTF-8"), None, "en-US"),
    (("C", "UTF-8"), None, "en-US"),
    ((None, None), "pl_PL.UTF-8", "pl-PL"),
    ((None, None), None, "en-US"),
    (ValueError("unknown locale: UTF-8"), None, "en-US"),
], ids=["exact", "other-region", "untranslated", "posix", "from-lang", "nothing-set", "unknown-locale"])
def test_starts_in_the_system_language(locales_dir, system_locale, monkeypatch, detected, lang, expected):
    system_locale.side_effect = [detected]
    if lang:
        monkeypatch.setenv("LANG", lang)

    assert I18n(locales_dir).current_lang == expected


@pytest.mark.parametrize("damage", [
    lambda locales: shutil.rmtree(locales),
    lambda locales: (locales / "en-US.json").write_text("{", encoding="utf-8"),
], ids=["no-locales-folder", "broken-english"])
def test_shows_keys_when_the_translations_cannot_be_read(locales_dir, damage):
    damage(locales_dir)

    i18n = I18n(locales_dir)

    assert (i18n.current_lang, i18n.t("update_available_title")) == ("en-US", "update_available_title")


def test_offers_every_translated_language(locales_dir):
    assert sorted(I18n(locales_dir).available_langs) == ["de-DE", "en-US", "pl-PL", "pt-BR"]


def test_offers_english_even_without_its_file(locales_dir):
    (locales_dir / "en-US.json").unlink()

    i18n = I18n(locales_dir)

    assert "en-US" in i18n.available_langs
    assert i18n.t("welcome_title") == "welcome_title"


def test_lists_languages_and_picks_a_region_the_same_way_whatever_the_disk_order(locales_dir, system_locale,
                                                                               mocker):
    write_json(locales_dir / "pt-PT.json", {"welcome_title": "Bem-vindo ao HLPatcher ({version})"})
    system_locale.return_value = ("pt_AO", "UTF-8")
    real_glob = Path.glob
    seen = []
    for reverse in (False, True):
        mocker.patch.object(Path, "glob",
                            lambda self, pattern, reverse=reverse: sorted(real_glob(self, pattern), reverse=reverse))
        i18n = I18n(locales_dir)
        seen.append((i18n.available_langs, i18n.current_lang))

    assert seen == [(["de-DE", "en-US", "pl-PL", "pt-BR", "pt-PT"], "pt-BR")] * 2


def test_switches_language_and_tells_the_app(locales_dir):
    i18n = I18n(locales_dir)
    changes = []
    i18n.on_language_changed = changes.append

    i18n.set_language("pl-PL")

    assert (i18n.current_lang, i18n.t("welcome_title", version="3.2"), changes) == (
        "pl-PL", "Witaj w HLPatcher (3.2)", ["pl-PL"],
    )


def test_switches_to_english_when_a_language_is_not_available(polish):
    changes = []
    polish.on_language_changed = changes.append

    polish.set_language("sv-SE")

    assert (polish.current_lang, polish.t("update_available_title"), changes) == (
        "en-US", ENGLISH["update_available_title"], ["en-US"],
    )


def test_switches_quietly_when_asked_to(locales_dir):
    i18n = I18n(locales_dir)
    changes = []
    i18n.on_language_changed = changes.append

    i18n.set_language("pl-PL", notify=False)

    assert (i18n.current_lang, changes) == ("pl-PL", [])


def test_falls_back_to_english_and_then_to_the_key(polish):
    assert [polish.t(key) for key in ["progress_time_format", "update_available_title", "no_such_key"]] == [
        POLISH["progress_time_format"], ENGLISH["update_available_title"], "no_such_key",
    ]


def test_fills_in_placeholders(polish):
    assert polish.t("progress_time_format", mins=3, secs=7) == "Upłynęło czasu: 03:07"


def test_a_missing_placeholder_value_leaves_the_text_unformatted(polish):
    assert polish.t("progress_time_format", mins=3) == POLISH["progress_time_format"]


@pytest.mark.parametrize("broken", [
    "Upłynęło czasu: {mins:02d}:{secs:02d",
    "Upłynęło czasu: {mins:02d}:secs:02d}",
    "Upłynęło czasu: {0:02d}:{1:02d}",
    "Upłynęło czasu: {mins.minutes}",
    "Upłynęło czasu: {mins[0]}",
    "Upłynęło czasu: {mins:02s}:{secs:02s}",
], ids=["unclosed", "stray-closing-brace", "positional", "attribute", "indexing", "wrong-format-code"])
def test_a_malformed_placeholder_leaves_the_text_unformatted(locales_dir, broken):
    write_json(locales_dir / "pl-PL.json", {"progress_time_format": broken})
    i18n = I18n(locales_dir)
    i18n.set_language("pl-PL")

    assert i18n.t("progress_time_format", mins=3, secs=7) == broken


def test_names_each_language_in_that_language(locales_dir):
    i18n = I18n(locales_dir)

    assert [i18n.get_language_name(code) for code in ["pl-PL", "pt-BR", "ko-KR"]] == [
        "Polski", "Português (Brasil)", "ko-KR",
    ]


@pytest.mark.parametrize("index", [None, "{"], ids=["missing", "broken"])
def test_shows_language_codes_without_a_readable_locales_json(locales_dir, index):
    names = locales_dir.parent / "locales.json"
    if index is None:
        names.unlink()
    else:
        names.write_text(index, encoding="utf-8")

    assert I18n(locales_dir).get_language_name("pl-PL") == "pl-PL"
