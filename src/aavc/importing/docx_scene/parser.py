from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from aavc.domain.errors import ImportError as AAVCImportError
from aavc.domain.errors import ValidationError
from aavc.domain.project.models import Scene

_SCENE_RE = re.compile(r"^tampilan\s+scene\s+(\d+)\s*:\s*([12])\s*$", re.I)
_ASSET_RE = re.compile(r"^asset\s+(\d+)\s*:\s*(.+?)\s*$", re.I)
_WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_MAX_DOCUMENT_XML_BYTES = 16 * 1024 * 1024


def _paragraphs_from_docx(path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            # Never decompress arbitrarily large DOCX XML into memory; a tiny
            # ZIP can expand to hundreds of megabytes.
            matches = [
                item for item in archive.infolist()
                if item.filename == "word/document.xml"
            ]
            if len(matches) != 1:
                raise AAVCImportError(
                    "DOCX memiliki word/document.xml hilang atau duplikat"
                )
            member = matches[0]
            if member.file_size > _MAX_DOCUMENT_XML_BYTES:
                raise AAVCImportError(
                    "DOCX word/document.xml terlalu besar (batas 16 MiB)"
                )
            with archive.open(member) as stream:
                # A bounded read also rejects mismatches between claimed and
                # actual expansion sizes before XML parsing begins.
                xml = stream.read(_MAX_DOCUMENT_XML_BYTES + 1)
            if len(xml) > _MAX_DOCUMENT_XML_BYTES:
                raise AAVCImportError(
                    "DOCX word/document.xml terlalu besar (batas 16 MiB)"
                )
        root = ET.fromstring(xml)
    except (
        OSError,
        KeyError,
        zipfile.BadZipFile,
        ET.ParseError,
        RuntimeError,
        NotImplementedError,
    ) as exc:
        raise AAVCImportError(f"DOCX tidak dapat dibaca: {path}") from exc
    lines: list[str] = []
    for paragraph in root.iter(f"{_WORD_NS}p"):
        text = "".join(
            node.text or "" for node in paragraph.iter(f"{_WORD_NS}t")
        ).strip()
        if text:
            lines.append(text)
    return lines


def parse_scene_docx(
    path: str | Path,
    *,
    default_duration_seconds: float = 3.0,
) -> tuple[Scene, ...]:
    source = Path(path)
    if not source.exists():
        raise AAVCImportError(f"DOCX tidak ditemukan: {source}")

    lines = _paragraphs_from_docx(source)
    scenes: list[Scene] = []
    current_number: int | None = None
    expected_count: int | None = None
    current_assets: list[tuple[int, str]] = []

    def flush() -> None:
        nonlocal current_number, expected_count, current_assets
        if current_number is None:
            return
        if expected_count is None or len(current_assets) != expected_count:
            raise ValidationError(
                f"Scene {current_number} meminta {expected_count} aset tetapi ditemukan "
                f"{len(current_assets)}"
            )
        ids = tuple(f"A{asset_no:03d}" for asset_no, _ in current_assets)
        quotes = tuple(quote for _, quote in current_assets)
        scenes.append(
            Scene(
                scene_number=current_number,
                asset_ids=ids,
                source_quotes=quotes,
                duration_seconds=default_duration_seconds,
            )
        )
        current_number = None
        expected_count = None
        current_assets = []

    for line in lines:
        scene_match = _SCENE_RE.match(line)
        if scene_match:
            flush()
            current_number = int(scene_match.group(1))
            expected_count = int(scene_match.group(2))
            continue

        asset_match = _ASSET_RE.match(line)
        if asset_match and current_number is not None:
            current_assets.append((int(asset_match.group(1)), asset_match.group(2).strip()))

    flush()

    if not scenes:
        raise ValidationError("Tidak ada scene valid pada BAGIAN 1 DOCX")

    expected_scene_numbers = list(range(1, len(scenes) + 1))
    actual_scene_numbers = [scene.scene_number for scene in scenes]
    if actual_scene_numbers != expected_scene_numbers:
        raise ValidationError(
            f"Nomor scene harus berurutan mulai 1. Ditemukan: {actual_scene_numbers}"
        )

    seen_assets = [asset for scene in scenes for asset in scene.asset_ids]
    expected_assets = [f"A{i:03d}" for i in range(1, len(seen_assets) + 1)]
    if seen_assets != expected_assets:
        raise ValidationError(
            f"Asset ID harus berurutan mulai A001. Ditemukan: {seen_assets}"
        )
    return tuple(scenes)
