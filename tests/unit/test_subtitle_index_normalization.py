from pathlib import Path

from aavc.subtitles import (
    SubtitleCue,
    normalize_subtitle_cue_indexes,
    parse_srt,
    write_srt_atomic,
)


def test_normalize_indexes_repairs_gaps_and_duplicates_without_reordering() -> None:
    cues = (
        SubtitleCue(7, 0.0, 1.0, "Pertama"),
        SubtitleCue(7, 1.5, 2.5, "Kedua"),
        SubtitleCue(12, 3.0, 4.0, "Ketiga"),
    )

    normalized = normalize_subtitle_cue_indexes(cues)

    assert [cue.index for cue in normalized] == [1, 2, 3]
    assert [cue.start_seconds for cue in normalized] == [0.0, 1.5, 3.0]
    assert [cue.end_seconds for cue in normalized] == [1.0, 2.5, 4.0]
    assert [cue.text for cue in normalized] == ["Pertama", "Kedua", "Ketiga"]


def test_normalize_indexes_preserves_objects_that_are_already_canonical() -> None:
    first = SubtitleCue(1, 0.0, 1.0, "Satu")
    second = SubtitleCue(9, 1.5, 2.5, "Dua")

    normalized = normalize_subtitle_cue_indexes((first, second))

    assert normalized[0] is first
    assert normalized[1] == SubtitleCue(2, 1.5, 2.5, "Dua")
    assert normalized[1] is not second


def test_normalize_indexes_accepts_empty_input() -> None:
    assert normalize_subtitle_cue_indexes(()) == ()


def test_normalized_indexes_round_trip_through_atomic_copy(tmp_path: Path) -> None:
    cues = (
        SubtitleCue(5, 0.125, 1.5, "Baris satu\\NBaris dua"),
        SubtitleCue(11, 2.0, 3.875, "Cue kedua"),
    )
    normalized = normalize_subtitle_cue_indexes(cues)
    destination = tmp_path / "normalized.srt"

    write_srt_atomic(destination, normalized)

    assert parse_srt(destination) == normalized
    assert [cue.index for cue in parse_srt(destination)] == [1, 2]
