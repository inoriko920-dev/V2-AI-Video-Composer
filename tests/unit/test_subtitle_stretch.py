from __future__ import annotations

import pytest

from aavc.subtitles import SubtitleCue, stretch_subtitle_cues_from_row


def _cues() -> tuple[SubtitleCue, ...]:
    return (
        SubtitleCue(index=1, start_seconds=1.0, end_seconds=2.0, text="Satu"),
        SubtitleCue(index=2, start_seconds=3.0, end_seconds=4.5, text="Dua"),
        SubtitleCue(index=3, start_seconds=6.0, end_seconds=7.0, text="Tiga"),
    )


def test_stretch_from_row_keeps_anchor_and_scales_following_timing() -> None:
    cues = _cues()

    stretched = stretch_subtitle_cues_from_row(cues, 1, 1.1)

    assert stretched[0] is cues[0]
    assert stretched[1].start_seconds == pytest.approx(3.0)
    assert stretched[1].end_seconds == pytest.approx(4.65)
    assert stretched[2].start_seconds == pytest.approx(6.3)
    assert stretched[2].end_seconds == pytest.approx(7.4)
    assert stretched[1].index == cues[1].index
    assert stretched[1].text == cues[1].text


def test_stretch_from_row_can_compress_timing() -> None:
    stretched = stretch_subtitle_cues_from_row(_cues(), 1, 0.5)

    assert stretched[1].start_seconds == pytest.approx(3.0)
    assert stretched[1].end_seconds == pytest.approx(3.75)
    assert stretched[2].start_seconds == pytest.approx(4.5)
    assert stretched[2].end_seconds == pytest.approx(5.0)


def test_stretch_from_row_rejects_non_positive_factor() -> None:
    with pytest.raises(ValueError, match="lebih besar dari 0"):
        stretch_subtitle_cues_from_row(_cues(), 1, 0.0)
    with pytest.raises(ValueError, match="lebih besar dari 0"):
        stretch_subtitle_cues_from_row(_cues(), 1, -1.0)


def test_stretch_from_row_rejects_invalid_row() -> None:
    with pytest.raises(ValueError, match="tidak valid"):
        stretch_subtitle_cues_from_row(_cues(), 3, 1.1)


def test_stretch_from_row_factor_one_is_identity() -> None:
    cues = _cues()

    assert stretch_subtitle_cues_from_row(cues, 1, 1.0) is cues
