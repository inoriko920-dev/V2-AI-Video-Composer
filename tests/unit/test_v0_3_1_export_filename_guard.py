"""Regression: export filename must never escape the explicitly chosen directory."""
from __future__ import annotations

from pathlib import Path

import pytest

from aavc.presentation.dialogs.export_settings import build_export_options


def _export(tmp_path: Path, name: str) -> Path:
    options = build_export_options(
        output_directory=str(tmp_path / "selected-output"),
        output_name=name,
        format_label="MP4 (H.264)",
        preset_label="Documentary Crisp",
        resolution_label="1920 × 1080 (Full HD)",
        fps_label="30 fps",
        quality_value=78,
        sharpen_label="Normal",
        burn_subtitles=True,
    )
    return Path(options.output_path)


@pytest.mark.parametrize(
    "untrusted_name",
    [
        "../other-video",
        "subfolder/video.mp4",
        "/tmp/unexpected-output.mp4",
        r"..\\other-video",
        r"C:\\Users\\Someone\\Documents\\video.mp4",
        r"\\\\server\\share\\video.mp4",
        "escape:video",
        "bad|video.mp4",
        "file?.mp4",
        ".",
        "..",
        ".mp4",
        "CON",
        "NUL.mp4",
        "LPT1",
    ],
)
def test_export_filename_rejects_paths_and_windows_reserved_names(
    tmp_path: Path, untrusted_name: str
) -> None:
    with pytest.raises(ValueError, match="Nama file"):
        _export(tmp_path, untrusted_name)


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("Final Video", "Final Video.mp4"),
        ("Film v1.mp4", "Film v1.mp4"),
        ("Fim Akhir.MP4", "Fim Akhir.MP4"),
        ("Видео selesai", "Видео selesai.mp4"),
    ],
)
def test_export_filename_keeps_safe_unicode_and_existing_mp4_suffix(
    tmp_path: Path, filename: str, expected: str
) -> None:
    directory = tmp_path / "selected-output"
    result = _export(tmp_path, filename)
    assert result == directory / expected
    assert result.parent == directory
