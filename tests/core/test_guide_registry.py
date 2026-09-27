import json
import logging

import pytest

from patcher.core import GuideConfig, GuideRegistry, GuideStepConfig


def write_guide(guides_dir, name, data):
    (guides_dir / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def guides_dir(tmp_path):
    guides = tmp_path / "guides"
    guides.mkdir()
    write_guide(guides, "hl2", {
        "title": "guide_hl2_title",
        "steps": [
            {"step_title": "guide_hl2_step1_title", "step_description": "guide_hl2_step1_desc"},
            {"step_title": "guide_hl2_step2_title", "step_description": "guide_hl2_step2_desc"},
        ],
    })
    write_guide(guides, "portal", {
        "title": "guide_portal_title",
        "steps": [{"step_title": "guide_portal_step1_title", "step_description": "guide_portal_step1_desc"}],
    })
    return guides


def test_loads_each_guide_under_its_file_name(guides_dir):
    registry = GuideRegistry(guides_dir)

    assert registry.get_guide("hl2") == GuideConfig("guide_hl2_title", [
        GuideStepConfig("guide_hl2_step1_title", "guide_hl2_step1_desc"),
        GuideStepConfig("guide_hl2_step2_title", "guide_hl2_step2_desc"),
    ])
    assert registry.get_guide("portal").title == "guide_portal_title"
    assert registry.get_guide("episodic") is None


def test_reads_the_command_and_link_of_a_step(guides_dir):
    write_guide(guides_dir, "dod", {"title": "guide_dods_title", "steps": [{
        "step_title": "guide_dods_step1_title",
        "step_description": "guide_dods_step1_desc",
        "step_command": "download_depot 300 232291 1051567359483024463",
        "step_button_text": "guide_open_console",
        "step_button_url": "steam://open/console",
    }]})

    [step] = GuideRegistry(guides_dir).get_guide("dod").steps

    assert step == GuideStepConfig(
        step_title="guide_dods_step1_title",
        step_description="guide_dods_step1_desc",
        step_command="download_depot 300 232291 1051567359483024463",
        step_button_text="guide_open_console",
        step_button_url="steam://open/console",
    )


def test_fills_in_what_a_guide_leaves_out(guides_dir):
    write_guide(guides_dir, "hl2mp", {"steps": [{"step_title": "guide_hl2mp_step1_title"}]})
    write_guide(guides_dir, "cstrike", {"title": "guide_css_title"})

    registry = GuideRegistry(guides_dir)

    assert registry.get_guide("hl2mp") == GuideConfig("hl2mp", [GuideStepConfig("guide_hl2mp_step1_title", "")])
    assert registry.get_guide("cstrike") == GuideConfig("guide_css_title", [])


@pytest.mark.parametrize("content", [
    "{",
    json.dumps({"title": "guide_css_title", "steps": ["guide_css_step1_title"]}),
], ids=["invalid-json", "step-not-an-object"])
def test_skips_a_broken_guide_and_loads_the_rest(guides_dir, caplog, content):
    (guides_dir / "cstrike.json").write_text(content, encoding="utf-8")

    registry = GuideRegistry(guides_dir)

    assert registry.get_guide("cstrike") is None
    assert registry.get_guide("hl2").title == "guide_hl2_title"
    assert [record.levelno for record in caplog.records if "cstrike.json" in record.message] == [logging.ERROR]


def test_ignores_files_that_are_not_guides(guides_dir, caplog):
    (guides_dir / ".DS_Store").write_bytes(b"\x00\x00\x00\x01Bud1")
    (guides_dir / "notes.txt").write_text("check the depot ids", encoding="utf-8")

    registry = GuideRegistry(guides_dir)

    assert registry.get_guide("hl2").title == "guide_hl2_title"
    assert not [record for record in caplog.records if record.levelno >= logging.WARNING]


def test_has_no_guides_without_the_guides_folder(tmp_path, caplog):
    registry = GuideRegistry(tmp_path / "guides")

    assert registry.get_guide("hl2") is None
    assert f"Guides directory not found at {tmp_path / 'guides'}" in caplog.messages
