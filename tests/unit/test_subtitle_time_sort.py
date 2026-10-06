from pathlib import Path

from aavc.subtitles import (
    SubtitleCue,
    parse_srt,
    sort_subtitle_cues_by_start_time,
    write_srt_atomic,
)


def test_sort_by_start_time_reorders_only_tuple_positions() -> None:
    first = SubtitleCue(7, 4.0, 5.0, "Terlambat")
    second = SubtitleCue(2, 0.5, 1.5, "Awal")
    third = SubtitleCue(9, 2.0, 3.0, "Tengah")

    sorted_cues = sort_subtitle_cues_by_start_time((first, second, third))

    assert sorted_cues == (second, third, first)
    assert sorted_cues[0] is second
    assert sorted_cues[1] is third
    assert sorted_cues[2] is first
    assert [cue.index for cue in sorted_cues] == [2, 9, 7]


def test_sort_by_start_time_is_stable_for_equal_start_times() -> None:
    first = SubtitleCue(10, 1.0, 3.0, "Pertama pada waktu sama")
    second = SubtitleCue(3, 1.0, 2.0, "Kedua pada waktu sama")
    earlier = SubtitleCue(8, 0.25, 0.75, "Lebih awal")

    sorted_cues = sort_subtitle_cues_by_start_time((first, second, earlier))

    assert sorted_cues == (earlier, first, second)
    assert sorted_cues[1] is first
    assert sorted_cues[2] is second


def test_sort_by_start_time_accepts_empty_and_preserves_sorted_objects() -> None:
    assert sort_subtitle_cues_by_start_time(()) == ()

    first = SubtitleCue(4, 0.0, 1.0, "Satu")
    second = SubtitleCue(12, 1.0, 2.0, "Dua")
    sorted_cues = sort_subtitle_cues_by_start_time((first, second))

    assert sorted_cues[0] is first
    assert sorted_cues[1] is second


def test_sorted_cues_round_trip_without_renumbering(tmp_path: Path) -> None:
    cues = (
        SubtitleCue(11, 3.0, 4.0, "Ketiga"),
        SubtitleCue(5, 0.0, 1.0, "Pertama"),
        SubtitleCue(8, 1.5, 2.5, "Kedua"),
    )
    sorted_cues = sort_subtitle_cues_by_start_time(cues)
    destination = tmp_path / "sorted-copy.srt"

    write_srt_atomic(destination, sorted_cues)
    parsed = parse_srt(destination)

    assert parsed == sorted_cues
    assert [cue.index for cue in parsed] == [5, 8, 11]
    assert [cue.start_seconds for cue in parsed] == [0.0, 1.5, 3.0]
