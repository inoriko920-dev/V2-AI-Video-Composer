"""AAVC asset preflight: never label a forged PNG READY."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

from aavc.domain.project.models import Scene
from aavc.importing.assets.binder import bind_assets

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _scene() -> Scene:
    return Scene(scene_number=1, asset_ids=("A001",), source_quotes=("test",))


def _status(folder: Path) -> str:
    return bind_assets((_scene(),), folder)[0].status


def _ihdr(*, width: int = 1, height: int = 1, corrupt_crc: bool = False) -> bytes:
    data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    header = b"IHDR" + data
    checksum = zlib.crc32(header)
    if corrupt_crc:
        checksum ^= 0xFFFFFFFF
    return PNG_SIGNATURE + struct.pack(">I", 13) + header + struct.pack(">I", checksum)


def test_reject_non_png_bytes_even_if_large_enough(tmp_path: Path) -> None:
    (tmp_path / "A001.png").write_bytes(b"not-a-png-file" * 32)
    assert _status(tmp_path) == "CORRUPT"


def test_reject_truncated_png_header(tmp_path: Path) -> None:
    (tmp_path / "A001.png").write_bytes(PNG_SIGNATURE + b"\x00" * 20)
    assert _status(tmp_path) == "CORRUPT"


def test_reject_png_zero_width_even_with_valid_ihdr_crc(tmp_path: Path) -> None:
    (tmp_path / "A001.png").write_bytes(_ihdr(width=0) + b"x" * 64)
    assert _status(tmp_path) == "CORRUPT"


def test_reject_png_bad_ihdr_crc(tmp_path: Path) -> None:
    (tmp_path / "A001.png").write_bytes(_ihdr(corrupt_crc=True) + b"x" * 64)
    assert _status(tmp_path) == "CORRUPT"


def test_binding_handles_non_directory_asset_selection(tmp_path: Path) -> None:
    not_a_directory = tmp_path / "assets"
    not_a_directory.write_text("A file selected as the asset directory")
    assert _status(not_a_directory) == "MISSING"


def test_valid_step10_png_fixture_still_ready() -> None:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "step10" / "assets"
    # Known project test fixtures are actual PNGs and must remain supported.
    assert _status(fixture) == "READY"
