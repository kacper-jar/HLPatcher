import struct
import zlib
from pathlib import Path
from typing import BinaryIO

from patcher.core.models import Component, Game, VpkEntry, VpkExtractStepConfig
from patcher.core.pipeline.base import BaseStep
from patcher.core.pipeline.registry import step

VPK_SIGNATURE = 0x55AA1234
ENTRY_TERMINATOR = 0xFFFF
DIR_ARCHIVE = 0x7FFF
HEADER_SIZES = {1: 12, 2: 28}


class VpkArchive:
    def __init__(self, dir_path: Path):
        self._dir_path = dir_path
        with open(dir_path, "rb") as f:
            signature, version, tree_size = struct.unpack("<III", self._read_exactly(f, 12))
            if signature != VPK_SIGNATURE:
                raise ValueError(f"Invalid VPK signature in {dir_path}")
            if version not in HEADER_SIZES:
                raise ValueError(f"Unsupported VPK version {version} in {dir_path}")

            self._data_offset = HEADER_SIZES[version] + tree_size
            f.seek(HEADER_SIZES[version])
            self._entries = self._read_tree(f)
            if f.tell() != self._data_offset:
                raise ValueError(f"Truncated VPK index in {dir_path}")

    def __contains__(self, path: str) -> bool:
        return path in self._entries

    def read(self, path: str) -> bytes:
        entry = self._entries[path]
        data = entry.preload + self._read_archive_data(entry)
        if zlib.crc32(data) != entry.crc:
            raise ValueError(f"CRC32 mismatch for {path} in {self._dir_path}")
        return data

    def _read_tree(self, f: BinaryIO) -> dict[str, VpkEntry]:
        entries = {}
        while extension := self._read_string(f):
            while folder := self._read_string(f):
                while name := self._read_string(f):
                    crc, preload_length, archive_index, offset, length, terminator = struct.unpack(
                        "<IHHIIH", self._read_exactly(f, 18))
                    if terminator != ENTRY_TERMINATOR:
                        raise ValueError(f"Corrupt VPK index in {self._dir_path}")
                    preload = self._read_exactly(f, preload_length)
                    path = f"{name}.{extension}" if folder == " " else f"{folder}/{name}.{extension}"
                    entries[path] = VpkEntry(crc, archive_index, offset, length, preload)
        return entries

    def _read_archive_data(self, entry: VpkEntry) -> bytes:
        if entry.length == 0:
            return b""
        if entry.archive_index == DIR_ARCHIVE:
            source, offset = self._dir_path, self._data_offset + entry.offset
        else:
            base = self._dir_path.name.removesuffix("_dir.vpk")
            source, offset = self._dir_path.with_name(f"{base}_{entry.archive_index:03d}.vpk"), entry.offset
        with open(source, "rb") as f:
            f.seek(offset)
            return self._read_exactly(f, entry.length)

    @staticmethod
    def _read_string(f: BinaryIO) -> str:
        out = bytearray()
        while (char := f.read(1)) not in (b"", b"\0"):
            out += char
        return out.decode("latin-1")

    @staticmethod
    def _read_exactly(f: BinaryIO, size: int) -> bytes:
        data = f.read(size)
        if len(data) != size:
            raise ValueError(f"Truncated VPK file {f.name}")
        return data


@step("vpk-extractor", config=VpkExtractStepConfig)
class VpkExtractorStep(BaseStep):
    interruptible = False

    def execute(self, game: Game, comp: Component, step_config: VpkExtractStepConfig):
        self.context.log(f"Extracting VPK files for {game.name}...")

        vpk_path = self.context.steam_library_path / step_config.vpk_path
        if not vpk_path.exists():
            raise FileNotFoundError(f"VPK not found: {vpk_path}")

        archive = VpkArchive(vpk_path)
        output_base = game.path / comp.subfolder / step_config.output_dir

        for file_path in step_config.files:
            if file_path not in archive:
                self.context.log(f"Warning: {file_path} not found in VPK.")
                continue

            out_file = output_base / file_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(archive.read(file_path))
