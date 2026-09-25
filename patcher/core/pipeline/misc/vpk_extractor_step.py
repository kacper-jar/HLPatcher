import struct
from pathlib import Path
import zlib

from patcher.core import Component, Game, VpkExtractStepConfig
from patcher.core.pipeline import BaseStep, step


def read_cstring(f) -> str:
    out = bytearray()
    while (c := f.read(1)) not in (b"", b"\0"):
        out += c
    return out.decode("latin-1")


@step("vpk-extractor")
class VpkExtractorStep(BaseStep):
    interruptible = False

    def execute(self, game: Game, comp: Component, step_config: VpkExtractStepConfig):
        self.patcher.log(f"Extracting VPK files for {game.name}...")

        full_vpk_path = self.patcher._context.steam_library_path / step_config.vpk_path
        if not full_vpk_path.exists():
            raise FileNotFoundError(f"VPK not found: {full_vpk_path}")

        entries, dir_data_base = self._read_vpk_index(full_vpk_path)
        output_base = game.path / comp.subfolder / step_config.output_dir

        for file_path in step_config.files:
            if file_path not in entries:
                self.patcher.log(f"Warning: {file_path} not found in VPK.")
                continue

            entry = entries[file_path]
            data = self._extract_file(full_vpk_path, entry, dir_data_base)

            out_file = output_base / file_path
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(data)

    def _read_vpk_index(self, path: Path) -> tuple[dict, int]:
        VPK_SIGNATURE = 0x55aa1234
        entries = {}

        with open(path, "rb") as f:
            signature, version = struct.unpack("<II", f.read(8))
            assert signature == VPK_SIGNATURE, "Invalid VPK signature"
            tree_size = struct.unpack("<I", f.read(4))[0]
            header_size = 12
            if version == 2:
                f.read(16)
                header_size = 28

            dir_data_base = header_size + tree_size

            while ext := read_cstring(f):
                while folder := read_cstring(f):
                    while name := read_cstring(f):
                        crc, preload_len, archive_index, offset, length = struct.unpack("<IHHII", f.read(16))
                        f.read(2)
                        preload = f.read(preload_len) if preload_len else b""
                        path_str = f"{name}.{ext}" if folder == " " else f"{folder}/{name}.{ext}"
                        entries[path_str] = (crc, archive_index, offset, length, preload)

        return entries, dir_data_base

    def _extract_file(self, dir_vpk: Path, entry: tuple, dir_data_base: int) -> bytes:
        crc, archive_index, offset, length, preload = entry
        if length == 0:
            return preload

        if archive_index == 0x7fff:
            src = dir_vpk
            seek = dir_data_base + offset
        else:
            base = str(dir_vpk)[:-len("_dir.vpk")]
            src = Path(f"{base}_{archive_index:03d}.vpk")
            seek = offset

        with open(src, "rb") as f:
            f.seek(seek)
            data = f.read(length)

        full_data = preload + data
        assert zlib.crc32(full_data) & 0xffffffff == crc, "CRC32 mismatch on extracted VPK file"
        return full_data
