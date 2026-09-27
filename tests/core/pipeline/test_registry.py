import subprocess
import sys

import pytest

from patcher.core import (ArchiveInstallStepConfig, BuildStepConfig, FetchStepConfig, InstallStepConfig,
                          PatchStepConfig, VpkExtractStepConfig)
from patcher.core.models import SourceInstallStepConfig
from patcher.core.pipeline import STEP_REGISTRY, BaseStep, parse_step_config, step
from patcher.core.pipeline.builders import CMakeBuilder, WafBuilder
from patcher.core.pipeline.fetchers import GitFetcher, GoldSrcEngineFetcher, UrlFetcherStep
from patcher.core.pipeline.installers import (ArchiveInstallerStep, GenericInstaller, GoldSrcEngineInstaller,
                                              SourceInstaller)
from patcher.core.pipeline.misc import PatchStep, VpkExtractorStep

HLSDK_URL = "https://github.com/FWGS/hlsdk-portable"

STEPS = {
    "git-fetcher": (GitFetcher, FetchStepConfig),
    "goldsrc-engine-fetcher": (GoldSrcEngineFetcher, FetchStepConfig),
    "url-fetcher": (UrlFetcherStep, FetchStepConfig),
    "cmake-builder": (CMakeBuilder, BuildStepConfig),
    "waf-builder": (WafBuilder, BuildStepConfig),
    "patch": (PatchStep, PatchStepConfig),
    "generic-installer": (GenericInstaller, InstallStepConfig),
    "goldsrc-engine-installer": (GoldSrcEngineInstaller, InstallStepConfig),
    "source-installer": (SourceInstaller, SourceInstallStepConfig),
    "archive-installer": (ArchiveInstallerStep, ArchiveInstallStepConfig),
    "vpk-extractor": (VpkExtractorStep, VpkExtractStepConfig),
}

DEFINITIONS = [
    {"type": "git-fetcher", "url": HLSDK_URL, "patch_dir_name": "hlsdk-portable-hlfixed", "branch": "hlfixed",
     "stable_commit": "5bc5bec", "force_stable": False},
    {"type": "goldsrc-engine-fetcher", "url": "https://github.com/FWGS/xash3d-fwgs", "patch_dir_name": "xash3d-fwgs",
     "stable_commit": "8b5732b", "force_stable": False},
    {"type": "url-fetcher", "patch_dir_name": "dejavu-fonts",
     "url": "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip"},
    {"type": "cmake-builder", "patch_dir_name": "cs16-client", "build_args": []},
    {"type": "waf-builder", "patch_dir_name": "source-engine", "build_args": ["-T", "release", "--build-games=hl2"],
     "waf_game": "hl2"},
    {"type": "patch", "patch_dir_name": "cs16-client"},
    {"type": "generic-installer", "patch_dir_name": "hlsdk-portable-hlfixed"},
    {"type": "goldsrc-engine-installer", "patch_dir_name": "xash3d-fwgs"},
    {"type": "source-installer", "patch_dir_name": "source-engine", "steam_executable": "hl2mp.exe"},
    {"type": "archive-installer", "patch_dir_name": "dejavu-fonts", "output_dir": "platform/resource/linux_fonts",
     "file_pattern": "*.ttf"},
    {"type": "vpk-extractor", "vpk_path": "Half-Life 2/hl2/hl2_misc_dir.vpk", "output_dir": "custom/shaderfix",
     "files": ["shaders/fxc/bloom_ps20.vcs", "shaders/fxc/water_ps20.vcs"]},
]


def test_every_step_type_is_registered_with_its_config():
    assert {name: (step_class, step_class.config_class) for name, step_class in STEP_REGISTRY.items()} == STEPS


def test_importing_the_pipeline_registers_every_step(pytestconfig):
    result = subprocess.run(
        [sys.executable, "-c", "from patcher.core.pipeline import STEP_REGISTRY; print(*STEP_REGISTRY)"],
        cwd=pytestconfig.rootpath, capture_output=True, text=True, check=True,
    )

    assert sorted(result.stdout.split()) == sorted(STEPS)


@pytest.mark.parametrize("definition", DEFINITIONS, ids=lambda definition: definition["type"])
def test_parses_a_definition_into_the_config_of_its_step(definition):
    config = parse_step_config(definition)

    assert type(config) is STEPS[definition["type"]][1]
    assert {key: getattr(config, key) for key in definition} == definition


@pytest.mark.parametrize(("definition", "message"), [
    ({"type": "svn-fetcher", "url": HLSDK_URL}, "Unknown step type: 'svn-fetcher'"),
    ({"url": HLSDK_URL, "patch_dir_name": "hlsdk-portable-hlfixed"}, "Unknown step type: None"),
], ids=["unknown", "missing"])
def test_rejects_a_step_without_a_known_type(definition, message):
    with pytest.raises(ValueError, match=message):
        parse_step_config(definition)


@pytest.mark.parametrize(("definition", "field"), [
    ({"type": "git-fetcher", "url": HLSDK_URL, "brnch": "hlfixed"}, "brnch"),
    ({"type": "generic-installer", "patch_dir_name": "source-engine", "steam_executable": "hl2mp.exe"},
     "steam_executable"),
], ids=["typo", "field-of-another-step"])
def test_rejects_fields_the_step_does_not_read(definition, field):
    with pytest.raises(TypeError, match=f"unexpected keyword argument '{field}'"):
        parse_step_config(definition)


def test_step_decorator_registers_a_new_step_type(mocker):
    mocker.patch.dict(STEP_REGISTRY)

    @step("rsync-installer", config=InstallStepConfig)
    class RsyncInstaller(BaseStep):
        pass

    config = parse_step_config({"type": "rsync-installer", "patch_dir_name": "hlsdk-portable-hlfixed"})

    assert STEP_REGISTRY["rsync-installer"] is RsyncInstaller
    assert RsyncInstaller.config_class is InstallStepConfig
    assert config == InstallStepConfig("rsync-installer", patch_dir_name="hlsdk-portable-hlfixed")


def test_steps_that_write_to_the_game_cannot_be_interrupted():
    assert {name for name, step_class in STEP_REGISTRY.items() if not step_class.interruptible} == {
        "generic-installer", "goldsrc-engine-installer", "source-installer", "archive-installer", "vpk-extractor",
    }
