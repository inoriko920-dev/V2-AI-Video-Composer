from __future__ import annotations

import pytest

from aavc.subtitles import SubtitleCue, shift_subtitle_cues_from_row


def _cues() -> tuple[SubtitleCue, ...]:
    return (
        SubtitleCue(index=1, start_seconds=1.0, end_seconds=2.0, text="Satu"),
        SubtitleCue(index=2, start_seconds=3.0, end_seconds=4.5, text="Dua"),
        SubtitleCue(index=3, start_seconds=6.0, end_seconds=7.0, text="Tiga"),
    )


def test_shift_from_row_moves_selected_and_later_only() -> None:
    cues = _cues()

    shifted = shift_subtitle_cues_from_row(cues, 1, 0.75)

    assert shifted[0] is cues[0]
    assert shifted[1].start_seconds == pytest.approx(3.75)
    assert shifted[1].end_seconds == pytest.approx(5.25)
    assert shifted[2].start_seconds == pytest.approx(6.75)
    assert shifted[2].end_seconds == pytest.approx(7.75)
    assert shifted[1].index == cues[1].index
    assert shifted[1].text == cues[1].text


def test_shift_from_row_supports_negative_offset() -> None:
    shifted = shift_subtitle_cues_from_row(_cues(), 2, -1.25)

    assert shifted[0].start_seconds == pytest.approx(1.0)
    assert shifted[1].start_seconds == pytest.approx(3.0)
    assert shifted[2].start_seconds == pytest.approx(4.75)
    assert shifted[2].end_seconds == pytest.approx(5.75)


def test_shift_from_row_rejects_negative_result() -> None:
    with pytest.raises(ValueError, match="negatif"):
        shift_subtitle_cues_from_row(_cues(), 0, -1.1)


def test_shift_from_row_rejects_invalid_row() -> None:
    with pytest.raises(ValueError, match="tidak valid"):
        shift_subtitle_cues_from_row(_cues(), 3, 1.0)


def test_shift_from_row_zero_offset_is_identity() -> None:
    cues = _cues()

    assert shift_subtitle_cues_from_row(cues, 1, 0.0) is cues
