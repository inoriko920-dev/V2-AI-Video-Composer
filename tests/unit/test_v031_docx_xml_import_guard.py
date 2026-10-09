"""DOCX user input must not expand unbounded XML or accept ambiguous duplicates."""
from __future__ import annotations

import warnings
import zipfile
from pathlib import Path

import pytest

from aavc.domain.errors import ImportError as AAVCImportError
from aavc.importing.docx_scene import parse_scene_docx

_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_MAX_XML = 16 * 1024 * 1024


def _doc_xml(*, scene_no: int = 1, pad: bytes = b"") -> bytes:
    lines = (
        f"<w:p><w:r><w:t>Tampilan Scene {scene_no}: 1</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Asset 1: contoh narasi</w:t></w:r></w:p>"
    ).encode()
    return (
        f'<w:document xmlns:w="{_NS}"><w:body>'.encode()
        + lines
        + pad
        + b"</w:body></w:document>"
    )


def test_docx_reader_accepts_normal_single_member(tmp_path: Path) -> None:
    file = tmp_path / "normal.docx"
    with zipfile.ZipFile(file, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", _doc_xml())
    scenes = parse_scene_docx(file)
    assert len(scenes) == 1
    assert scenes[0].asset_ids == ("A001",)


def test_docx_reader_rejects_xml_zip_bomb_before_decompression(tmp_path: Path) -> None:
    file = tmp_path / "expansion.docx"
    payload = _doc_xml(pad=b" " * (_MAX_XML + 1))
    with zipfile.ZipFile(file, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", payload)
    assert file.stat().st_size < 100_000  # Tiny input, >16 MiB expanded.
    with pytest.raises(AAVCImportError, match="terlalu besar|batas"):
        parse_scene_docx(file)


def test_docx_reader_rejects_ambiguous_duplicate_document_xml(tmp_path: Path) -> None:
    file = tmp_path / "ambiguous.docx"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(file, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", _doc_xml())
            archive.writestr("word/document.xml", _doc_xml())
    with pytest.raises(AAVCImportError, match="duplikat|ganda|ambigu"):
        parse_scene_docx(file)
