from __future__ import annotations

from pathlib import Path
from typing import Literal

MediaKind = Literal["narration", "subtitle"]

SUPPORTED_AUDIO_EXTENSIONS = frozenset({".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"})
SUPPORTED_SUBTITLE_EXTENSIONS = frozenset({".srt"})


def classify_media_path(path: str | Path) -> MediaKind:
    source = Path(path)
    if not source.is_file():
        raise ValueError(f"File media tidak ditemukan: {source}")

    suffix = source.suffix.lower()
    if suffix in SUPPORTED_SUBTITLE_EXTENSIONS:
        return "subtitle"
    if suffix in SUPPORTED_AUDIO_EXTENSIONS:
        return "narration"

    supported = ", ".join(
        sorted(SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_SUBTITLE_EXTENSIONS)
    )
    raise ValueError(
        f"Format media belum didukung: {suffix or '(tanpa ekstensi)'}. "
        f"Format yang didukung: {supported}"
    )
