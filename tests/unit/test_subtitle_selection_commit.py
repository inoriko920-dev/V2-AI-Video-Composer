import pytest

from aavc.subtitles.selection import commit_pending_subtitle_edit
from aavc.subtitles.srt import SubtitleCue


def _cue(index: int, start: float, end: float, text: str) -> SubtitleCue:
    return SubtitleCue(index=index, start_seconds=start, end_seconds=end, text=text)


def test_pending_edit_updates_loaded_row_not_new_selection() -> None:
    first = _cue(1, 0.0, 1.0, "Pertama")
    second = _cue(2, 1.0, 2.0, "Kedua")

    updated = commit_pending_subtitle_edit(
        (first, second),
        0,
        text="Pertama diedit",
        start_timestamp="00:00:00,100",
        end_timestamp="00:00:01,100",
    )

    assert updated[0].text == "Pertama diedit"
    assert updated[0].start_seconds == pytest.approx(0.1)
    assert updated[0].end_seconds == pytest.approx(1.1)
    assert updated[1] is second


def test_invalid_pending_edit_does_not_mutate_input() -> None:
    cues = (
        _cue(1, 0.0, 1.0, "Pertama"),
        _cue(2, 1.0, 2.0, "Kedua"),
    )

    with pytest.raises(ValueError):
        commit_pending_subtitle_edit(
            cues,
            0,
            text="Pertama",
            start_timestamp="bukan-timestamp",
            end_timestamp="00:00:01,000",
        )

    assert cues[0].text == "Pertama"
    assert cues[0].start_seconds == 0.0


def test_no_loaded_row_is_a_no_op() -> None:
    cues = (_cue(1, 0.0, 1.0, "Pertama"),)

    assert (
        commit_pending_subtitle_edit(
            cues,
            -1,
            text="diabaikan",
            start_timestamp="invalid",
            end_timestamp="invalid",
        )
        is cues
    )
