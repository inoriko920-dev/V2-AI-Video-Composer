from __future__ import annotations

from pathlib import Path

import pytest

from aavc.presentation.windows.subtitle_timing_tools_window import (
    resolve_subtitle_fit_destination,
    subtitle_target_fit_requires_clean_working_copy,
)


def test_target_fit_blocks_only_dirty_active_editor() -> None:
    assert subtitle_target_fit_requires_clean_working_copy(
        editor_active=True,
        working_copy_dirty=True,
    )
    assert not subtitle_target_fit_requires_clean_working_copy(
        editor_active=True,
        working_copy_dirty=False,
    )
    assert not subtitle_target_fit_requires_clean_working_copy(
        editor_active=False,
        working_copy_dirty=True,
    )


def test_fit_destination_adds_srt_suffix(tmp_path: Path) -> None:
    source = tmp_path / "source.srt"
    chosen = tmp_path / "hasil-fit"

    assert resolve_subtitle_fit_destination(source, chosen) == tmp_path / "hasil-fit.srt"


def test_fit_destination_preserves_existing_srt_suffix(tmp_path: Path) -> None:
    source = tmp_path / "source.srt"
    chosen = tmp_path / "hasil.srt"

    assert resolve_subtitle_fit_destination(source, chosen) == chosen


def test_fit_destination_rejects_overwriting_source(tmp_path: Path) -> None:
    source = tmp_path / "source.srt"

    with pytest.raises(ValueError, match="tidak boleh ditimpa"):
        resolve_subtitle_fit_destination(source, source)
