import json
import re
import string

import pytest

from patcher.core import GameDetector

COMPONENT_FIELDS = {"id", "name", "game", "subfolder", "steps", "depends_on", "auto_select", "downgrade_group",
                    "downgrade_requires", "estimated_time", "estimated_space"}
GUIDE_FIELDS = {"title", "steps"}
GUIDE_STEP_FIELDS = {"step_title", "step_description", "step_command", "step_button_text", "step_button_url"}
WAF_PLACEHOLDERS = {"working_dir", "waf_game"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def placeholders(text):
    return {field for _, field, _, _ in string.Formatter().parse(text) if field is not None}


def guide_key(component):
    return component.get("downgrade_group") or component["subfolder"]


@pytest.fixture(scope="module")
def data_dir(pytestconfig):
    return pytestconfig.rootpath / "data"


@pytest.fixture(scope="module")
def games(data_dir):
    return read(data_dir / "games.json")


@pytest.fixture(scope="module")
def components(data_dir):
    return read(data_dir / "components.json")


@pytest.fixture(scope="module")
def steps(components):
    return [(component["id"], step) for component in components for step in component["steps"]]


@pytest.fixture(scope="module")
def guides(data_dir):
    return {path.stem: read(path) for path in sorted((data_dir / "guides").glob("*.json"))}


@pytest.fixture(scope="module")
def translations(data_dir):
    return {path.stem: read(path) for path in sorted((data_dir / "locales").glob("*.json"))}


@pytest.fixture(scope="module")
def english(translations):
    return translations["en-US"]


@pytest.mark.parametrize("field", ["id", "folder"])
def test_every_game_has_its_own_id_and_folder(games, field):
    values = [game[field] for game in games]

    assert sorted({value for value in values if values.count(value) > 1}) == []


def test_every_game_has_components(games, components):
    assert [game["id"] for game in games if not any(comp["game"] == game["id"] for comp in components)] == []


def test_games_come_after_the_games_they_depend_on(games, components):
    position = {game["id"]: index for index, game in enumerate(games)}
    game_of = {comp["id"]: comp["game"] for comp in components}

    assert [(comp["id"], dependency) for comp in components for dependency in comp.get("depends_on", [])
            if position[game_of[dependency]] > position[comp["game"]]] == []


def test_the_detector_accepts_the_shipped_components(tmp_path):
    assert GameDetector(tmp_path).scan() == []


def test_components_use_only_fields_the_detector_reads(components):
    assert [(comp["id"], field) for comp in components for field in sorted(comp.keys() - COMPONENT_FIELDS)] == []


def test_every_component_fetches_a_folder_before_working_on_it(components):
    problems = []
    for comp in components:
        fetched = set()
        for step in comp["steps"]:
            if step["type"].endswith("-fetcher"):
                fetched.add(step["patch_dir_name"])
            elif "patch_dir_name" in step and step["patch_dir_name"] not in fetched:
                problems.append((comp["id"], step["type"], step["patch_dir_name"]))

    assert problems == []


def test_every_git_fetch_pins_a_full_stable_commit(steps):
    assert [(comp_id, step.get("stable_commit")) for comp_id, step in steps
            if step["type"] in ("git-fetcher", "goldsrc-engine-fetcher")
            and not re.fullmatch(r"[0-9a-f]{40}", step.get("stable_commit", ""))] == []


def test_downloads_use_https(steps):
    assert [(comp_id, step["url"]) for comp_id, step in steps
            if "url" in step and not step["url"].startswith("https://")] == []


def test_build_arguments_go_only_to_waf_and_use_the_placeholders_it_fills_in(steps):
    problems = []
    for comp_id, step in steps:
        for arg in step.get("build_args", []):
            try:
                unknown = placeholders(arg) - WAF_PLACEHOLDERS
            except ValueError as error:
                unknown = {str(error)}
            if step["type"] != "waf-builder" or unknown:
                problems.append((comp_id, step["type"], arg))

    assert problems == []


def test_patch_folders_match_the_patch_steps(steps, data_dir):
    fixes = data_dir / "fixes" / "src"
    containers = {step.get("patch_container") or f"{step['patch_dir_name']}-base"
                  for _, step in steps if step["type"] == "patch"}

    assert sorted(path.name for path in fixes.iterdir() if path.is_dir()) == sorted(containers)
    assert [name for name in sorted(containers) if not list((fixes / name).glob("*.patch"))] == []


def test_vpks_come_from_games_the_component_depends_on(games, components):
    game_by_folder = {game["folder"]: game["id"] for game in games}
    game_of = {comp["id"]: comp["game"] for comp in components}
    problems = []
    for comp in components:
        allowed = {comp["game"], *(game_of[dependency] for dependency in comp.get("depends_on", []))}
        for step in comp["steps"]:
            if step["type"] == "vpk-extractor" and game_by_folder.get(step["vpk_path"].split("/")[0]) not in allowed:
                problems.append((comp["id"], step["vpk_path"]))

    assert problems == []


def test_downgrade_hashes_are_lowercase_sha256_or_empty(components):
    assert [(comp["id"], path) for comp in components for path, digest in comp.get("downgrade_requires", {}).items()
            if not re.fullmatch(r"(?:[0-9a-f]{64})?", digest)] == []


def test_every_downgrade_group_has_a_guide_and_every_guide_a_group(components, guides):
    groups = {guide_key(comp) for comp in components if comp.get("downgrade_requires")}

    assert sorted(groups) == sorted(guides)


def test_each_downgrade_guide_belongs_to_one_game(components):
    games_by_guide = {}
    for comp in components:
        if comp.get("downgrade_requires"):
            games_by_guide.setdefault(guide_key(comp), set()).add(comp["game"])

    assert {key: sorted(ids) for key, ids in games_by_guide.items() if len(ids) > 1} == {}


def test_guides_use_only_fields_the_registry_reads(guides):
    unknown = []
    for name, guide in guides.items():
        unknown += [(name, field) for field in sorted(guide.keys() - GUIDE_FIELDS)]
        for step in guide.get("steps", []):
            unknown += [(name, field) for field in sorted(step.keys() - GUIDE_STEP_FIELDS)]

    assert unknown == []


def test_guides_use_only_messages_that_exist_in_english(guides, english):
    keys = set()
    for name, guide in guides.items():
        keys.add(guide.get("title", name))
        for step in guide.get("steps", []):
            keys |= {step[field] for field in ("step_title", "step_description", "step_button_text") if step.get(field)}

    assert sorted(keys - english.keys()) == []


def test_locales_json_names_every_locale(data_dir, translations):
    assert sorted(read(data_dir / "locales.json")) == sorted(translations)


def test_translations_keep_the_placeholders_of_the_english_text(translations, english):
    problems = []
    for code, messages in translations.items():
        for key, text in messages.items():
            try:
                if placeholders(text) != placeholders(english.get(key, text)):
                    problems.append((code, key, text))
            except (TypeError, ValueError) as error:
                problems.append((code, key, str(error)))

    assert problems == []


def test_the_code_asks_only_for_messages_that_exist_in_english(pytestconfig, english):
    keys = {key for path in (pytestconfig.rootpath / "patcher").rglob("*.py")
            for key in re.findall(r'\bt\(\s*"(\w+)"', path.read_text(encoding="utf-8"))}

    assert keys
    assert sorted(keys - english.keys()) == []
