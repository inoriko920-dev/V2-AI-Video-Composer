from __future__ import annotations

import math

import pytest

from aavc.subtitles import SubtitleCue, fit_subtitle_cues_from_row_to_end


def _cues() -> tuple[SubtitleCue, ...]:
    return (
        SubtitleCue(index=1, start_seconds=1.0, end_seconds=2.0, text="Satu"),
        SubtitleCue(index=2, start_seconds=3.0, end_seconds=4.5, text="Dua"),
        SubtitleCue(index=3, start_seconds=6.0, end_seconds=7.0, text="Tiga"),
    )


def test_fit_from_row_expands_to_requested_final_end() -> None:
    cues = _cues()

    fitted = fit_subtitle_cues_from_row_to_end(cues, 1, 9.0)

    assert fitted[0] is cues[0]
    assert fitted[1].start_seconds == pytest.approx(3.0)
    assert fitted[1].end_seconds == pytest.approx(5.25)
    assert fitted[2].start_seconds == pytest.approx(7.5)
    assert fitted[2].end_seconds == pytest.approx(9.0)
    assert fitted[1].index == cues[1].index
    assert fitted[1].text == cues[1].text


def test_fit_from_row_compresses_to_requested_final_end() -> None:
    fitted = fit_subtitle_cues_from_row_to_end(_cues(), 1, 5.0)

    assert fitted[1].start_seconds == pytest.approx(3.0)
    assert fitted[1].end_seconds == pytest.approx(3.75)
    assert fitted[2].start_seconds == pytest.approx(4.5)
    assert fitted[2].end_seconds == pytest.approx(5.0)


def test_fit_from_row_identity_returns_original_tuple() -> None:
    cues = _cues()

    assert fit_subtitle_cues_from_row_to_end(cues, 1, 7.0) is cues


def test_fit_from_row_rejects_invalid_row() -> None:
    with pytest.raises(ValueError, match="tidak valid"):
        fit_subtitle_cues_from_row_to_end(_cues(), 3, 8.0)


def test_fit_from_row_rejects_target_not_after_anchor() -> None:
    with pytest.raises(ValueError, match="lebih besar"):
        fit_subtitle_cues_from_row_to_end(_cues(), 1, 3.0)


def test_fit_from_row_rejects_non_finite_target() -> None:
    with pytest.raises(ValueError, match="waktu yang valid"):
        fit_subtitle_cues_from_row_to_end(_cues(), 1, math.inf)
    with pytest.raises(ValueError, match="waktu yang valid"):
        fit_subtitle_cues_from_row_to_end(_cues(), 1, math.nan)


def test_fit_from_row_rejects_degenerate_source_span() -> None:
    cues = (
        SubtitleCue(index=1, start_seconds=5.0, end_seconds=5.5, text="Anchor"),
        SubtitleCue(index=2, start_seconds=4.5, end_seconds=5.0, text="Akhir"),
    )

    with pytest.raises(ValueError, match="tidak valid untuk di-fit"):
        fit_subtitle_cues_from_row_to_end(cues, 0, 8.0)
