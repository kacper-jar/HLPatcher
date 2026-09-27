import struct
import zlib

import pytest

from patcher.core import EngineType, Game, VpkExtractStepConfig
from patcher.core.pipeline.misc import VpkExtractorStep

VPK_SIGNATURE = 0x55AA1234
DIR_ARCHIVE = 0x7FFF


def write_vpk(dir_vpk, files, version=2):
    grouped = {}
    for path, (content, preload_length, archive_index) in files.items():
        folder, _, file_name = path.rpartition("/")
        name, _, extension = file_name.rpartition(".")
        grouped.setdefault(extension, {}).setdefault(folder or " ", []).append(
            (name, content, preload_length, archive_index))

    tree = bytearray()
    dir_data = bytearray()
    archives = {}
    for extension, folders in grouped.items():
        tree += extension.encode() + b"\0"
        for folder, entries in folders.items():
            tree += folder.encode() + b"\0"
            for name, content, preload_length, archive_index in entries:
                preload, rest = content[:preload_length], content[preload_length:]
                target = dir_data if archive_index == DIR_ARCHIVE else archives.setdefault(archive_index, bytearray())
                offset = len(target)
                target += rest
                tree += name.encode() + b"\0"
                tree += struct.pack("<IHHIIH", zlib.crc32(content), preload_length, archive_index, offset, len(rest),
                                    0xFFFF)
                tree += preload
            tree += b"\0"
        tree += b"\0"
    tree += b"\0"

    header = struct.pack("<III", VPK_SIGNATURE, version, len(tree))
    if version == 2:
        header += struct.pack("<IIII", len(dir_data), 0, 0, 0)
    dir_vpk.write_bytes(header + tree + dir_data)
    for archive_index, data in archives.items():
        dir_vpk.with_name(dir_vpk.name.replace("_dir.vpk", f"_{archive_index:03d}.vpk")).write_bytes(data)


def corrupt_signature(dir_vpk):
    data = bytearray(dir_vpk.read_bytes())
    data[0] ^= 0xFF
    dir_vpk.write_bytes(data)


def corrupt_archive_data(dir_vpk):
    archive = dir_vpk.with_name("hl2_misc_000.vpk")
    data = bytearray(archive.read_bytes())
    data[0] ^= 0xFF
    archive.write_bytes(data)


CORRUPTIONS = [
    pytest.param(corrupt_signature, "Invalid VPK signature", id="signature"),
    pytest.param(corrupt_archive_data, "CRC32 mismatch", id="crc"),
]


@pytest.fixture
def dir_vpk(step_context):
    path = step_context.steam_library_path / "Half-Life 2" / "hl2" / "hl2_misc_dir.vpk"
    path.parent.mkdir(parents=True)
    return path


@pytest.fixture
def extract(step_context, make_component, tmp_path):
    comp = make_component("Half-Life 2: Deathmatch", "hl2mp")
    game = Game("Half-Life 2 Deathmatch", tmp_path / "game", EngineType.SOURCE, [comp])

    def run(files):
        config = VpkExtractStepConfig("vpk-extractor", vpk_path="Half-Life 2/hl2/hl2_misc_dir.vpk", files=files,
                                      output_dir="custom/shaderfix")
        VpkExtractorStep(step_context).execute(game, comp, config)
        return game.path / "hl2mp" / "custom" / "shaderfix"

    return run


@pytest.mark.parametrize("version", [1, 2])
def test_extracts_files_stored_in_the_directory_file(dir_vpk, extract, version):
    write_vpk(dir_vpk, {
        "shaders/fxc/bloom_ps20.vcs": (b"bloom shader", 0, DIR_ARCHIVE),
        "shaders/fxc/blurfilter_vs11.vcs": (b"blur shader", 0, DIR_ARCHIVE),
        "readme.txt": (b"stored at the root", 0, DIR_ARCHIVE),
    }, version=version)

    output = extract(["shaders/fxc/bloom_ps20.vcs", "shaders/fxc/blurfilter_vs11.vcs", "readme.txt"])

    assert (output / "shaders/fxc/bloom_ps20.vcs").read_bytes() == b"bloom shader"
    assert (output / "shaders/fxc/blurfilter_vs11.vcs").read_bytes() == b"blur shader"
    assert (output / "readme.txt").read_bytes() == b"stored at the root"


def test_extracts_files_stored_in_numbered_archives(dir_vpk, extract):
    write_vpk(dir_vpk, {
        "shaders/fxc/bloom_ps20.vcs": (b"from archive 000", 0, 0),
        "shaders/fxc/depthwrite_ps20.vcs": (b"from archive 001", 0, 1),
    })

    output = extract(["shaders/fxc/bloom_ps20.vcs", "shaders/fxc/depthwrite_ps20.vcs"])

    assert (output / "shaders/fxc/bloom_ps20.vcs").read_bytes() == b"from archive 000"
    assert (output / "shaders/fxc/depthwrite_ps20.vcs").read_bytes() == b"from archive 001"


def test_joins_preload_bytes_with_archive_data(dir_vpk, extract):
    write_vpk(dir_vpk, {"shaders/fxc/bloom_ps20.vcs": (b"PRELOAD+rest of the shader", 8, 0)})

    output = extract(["shaders/fxc/bloom_ps20.vcs"])

    assert (output / "shaders/fxc/bloom_ps20.vcs").read_bytes() == b"PRELOAD+rest of the shader"


def test_extracts_files_stored_only_as_preload(dir_vpk, extract):
    write_vpk(dir_vpk, {"shaders/fxc/bloom_ps20.vcs": (b"tiny", 4, DIR_ARCHIVE)})

    output = extract(["shaders/fxc/bloom_ps20.vcs"])

    assert (output / "shaders/fxc/bloom_ps20.vcs").read_bytes() == b"tiny"


def test_skips_files_missing_from_the_vpk(dir_vpk, extract, step_context):
    write_vpk(dir_vpk, {"shaders/fxc/bloom_ps20.vcs": (b"bloom shader", 0, DIR_ARCHIVE)})

    output = extract(["shaders/fxc/bloom_ps20.vcs", "shaders/fxc/missing_ps20.vcs"])

    assert (output / "shaders/fxc/bloom_ps20.vcs").exists()
    assert not (output / "shaders/fxc/missing_ps20.vcs").exists()
    step_context.log.assert_any_call("Warning: shaders/fxc/missing_ps20.vcs not found in VPK.")


def test_missing_vpk_raises(extract):
    with pytest.raises(FileNotFoundError, match="VPK not found"):
        extract(["shaders/fxc/bloom_ps20.vcs"])


@pytest.mark.parametrize(("corrupt", "message"), CORRUPTIONS)
def test_rejects_a_corrupted_vpk(dir_vpk, extract, corrupt, message):
    write_vpk(dir_vpk, {"shaders/fxc/bloom_ps20.vcs": (b"bloom shader", 0, 0)})
    corrupt(dir_vpk)

    with pytest.raises((AssertionError, ValueError), match=message):
        extract(["shaders/fxc/bloom_ps20.vcs"])


@pytest.mark.xfail(raises=AssertionError, strict=True,
                   reason="The parser validates with assert, which python -O removes")
@pytest.mark.parametrize(("corrupt", "message"), CORRUPTIONS)
def test_corrupted_vpk_raises_value_error(dir_vpk, extract, corrupt, message):
    write_vpk(dir_vpk, {"shaders/fxc/bloom_ps20.vcs": (b"bloom shader", 0, 0)})
    corrupt(dir_vpk)

    with pytest.raises(ValueError, match=message):
        extract(["shaders/fxc/bloom_ps20.vcs"])
