from pathlib import Path

from aavc.presentation.widgets.live_subtitle import load_subtitle_views


def test_load_subtitle_views_reads_real_srt_and_marks_overlap(tmp_path: Path) -> None:
    source = tmp_path / "actual.srt"
    source.write_text(
        "1\n"
        "00:00:00,000 --> 00:00:02,000\n"
        "Baris pertama\n\n"
        "2\n"
        "00:00:01,900 --> 00:00:03,500\n"
        "Baris kedua\n"
        "lanjutan\n",
        encoding="utf-8",
    )

    views = load_subtitle_views(source)

    assert len(views) == 2
    assert views[0].text == "Baris pertama"
    assert views[1].text == "Baris kedua\\Nlanjutan"
    assert views[1].overlaps_previous is True
    assert views[1].start_label == "00:00:01,900"
