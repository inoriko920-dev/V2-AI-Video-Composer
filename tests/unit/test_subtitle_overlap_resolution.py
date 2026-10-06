from pathlib import Path

import pytest

from aavc.subtitles import (
    SubtitleCue,
    parse_srt,
    resolve_subtitle_cue_overlap,
    write_srt_atomic,
)


def test_resolve_overlap_shifts_selected_cue_and_preserves_duration() -> None:
    cues = (
        SubtitleCue(4, 0.0, 2.0, "Pertama"),
        SubtitleCue(9, 1.25, 3.0, "Kedua\\Ndua baris"),
        SubtitleCue(12, 4.0, 5.0, "Ketiga"),
    )

    resolved = resolve_subtitle_cue_overlap(cues, 1)

    assert resolved[0] is cues[0]
    assert resolved[2] is cues[2]
    assert resolved[1].index == 9
    assert resolved[1].text == "Kedua\\Ndua baris"
    assert resolved[1].start_seconds == pytest.approx(2.0)
    assert resolved[1].end_seconds == pytest.approx(3.75)
    assert (resolved[1].end_seconds - resolved[1].start_seconds) == pytest.approx(1.75)


def test_resolve_overlap_is_noop_for_first_or_non_overlapping_cue() -> None:
    cues = (
        SubtitleCue(1, 0.0, 1.0, "Pertama"),
        SubtitleCue(2, 1.0, 2.0, "Kedua"),
    )

    assert resolve_subtitle_cue_overlap(cues, 0) is cues
    assert resolve_subtitle_cue_overlap(cues, 1) is cues


def test_resolve_overlap_rejects_invalid_row() -> None:
    cues = (SubtitleCue(1, 0.0, 1.0, "Pertama"),)
    with pytest.raises(ValueError, match="dipilih tidak valid"):
        resolve_subtitle_cue_overlap(cues, -1)
    with pytest.raises(ValueError, match="dipilih tidak valid"):
        resolve_subtitle_cue_overlap(cues, len(cues))


def test_resolved_overlap_round_trips_through_copy(tmp_path: Path) -> None:
    cues = (
        SubtitleCue(1, 0.0, 2.0, "Pertama"),
        SubtitleCue(2, 1.5, 2.5, "Kedua"),
    )
    resolved = resolve_subtitle_cue_overlap(cues, 1)
    destination = tmp_path / "resolved-overlap.srt"

    write_srt_atomic(destination, resolved)

    assert parse_srt(destination) == resolved
