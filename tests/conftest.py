from __future__ import annotations

import struct
import wave
import zipfile
import zlib
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "step10"


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _write_png(path: Path, rgb: tuple[int, int, int], size: int = 64) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    row = bytes([0]) + bytes(rgb) * size
    raw = row * size
    path.write_bytes(signature + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", zlib.compress(raw)) + _png_chunk(b"IEND", b""))


def _write_wav(path: Path, seconds: int = 6, sample_rate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * sample_rate * seconds)


def _write_docx(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "tampilan scene 1 : 1",
        "asset 1 : Indonesia memiliki bentang alam yang luas dan beragam.",
        "tampilan scene 2 : 2",
        "asset 2 : Pegunungan membentuk visual dokumenter.",
        "asset 3 : Matahari terbit melengkapi adegan.",
    ]
    paragraphs = "".join(f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for line in lines)
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraphs}</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", document_xml)


def _ensure_step10_fixtures() -> None:
    assets = FIXTURE / "assets"
    _write_png(assets / "A001.png", (42, 111, 219))
    _write_png(assets / "A002.png", (22, 163, 74))
    _write_png(assets / "A003.png", (234, 88, 12))
    _write_wav(FIXTURE / "narration.wav")
    _write_docx(FIXTURE / "scene_asset_demo.docx")


_ensure_step10_fixtures()
