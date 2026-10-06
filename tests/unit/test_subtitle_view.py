from aavc.presentation.subtitle_view import build_subtitle_views, format_srt_time
from aavc.subtitles import SubtitleCue


def test_format_srt_time_uses_millisecond_precision() -> None:
    assert format_srt_time(0.0) == "00:00:00,000"
    assert format_srt_time(65.432) == "00:01:05,432"
    assert format_srt_time(3661.001) == "01:01:01,001"


def test_build_subtitle_views_marks_only_actual_overlap() -> None:
    cues = (
        SubtitleCue(1, 0.0, 2.0, "Pertama"),
        SubtitleCue(2, 1.9, 3.0, "Kedua"),
        SubtitleCue(3, 3.0, 4.0, "Ketiga\\Nbaris dua"),
    )

    views = build_subtitle_views(cues)

    assert [view.overlaps_previous for view in views] == [False, True, False]
    assert "⚠" in views[1].list_label
    assert "Ketiga baris dua" in views[2].list_label
