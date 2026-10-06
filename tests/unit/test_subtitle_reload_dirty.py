from aavc.subtitles.dirty import subtitle_working_copy_is_dirty
from aavc.subtitles.srt import SubtitleCue


def _cue(
    *,
    index: int = 1,
    start_seconds: float = 1.0,
    end_seconds: float = 2.5,
    text: str = "Halo\\NDunia",
) -> SubtitleCue:
    return SubtitleCue(
        index=index,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        text=text,
    )


def test_clean_working_copy_and_form_are_not_dirty() -> None:
    source = (_cue(),)

    assert not subtitle_working_copy_is_dirty(
        source,
        source,
        loaded_row=0,
        pending_text="Halo\nDunia",
        pending_start="00:00:01,000",
        pending_end="00:00:02,500",
    )


def test_committed_working_copy_change_is_dirty() -> None:
    source = (_cue(),)
    working = (_cue(text="Sudah diubah"),)

    assert subtitle_working_copy_is_dirty(
        source,
        working,
        loaded_row=0,
        pending_text="Sudah diubah",
        pending_start="00:00:01,000",
        pending_end="00:00:02,500",
    )


def test_pending_text_change_is_dirty_before_commit() -> None:
    source = (_cue(),)

    assert subtitle_working_copy_is_dirty(
        source,
        source,
        loaded_row=0,
        pending_text="Belum dikomit",
        pending_start="00:00:01,000",
        pending_end="00:00:02,500",
    )


def test_pending_timing_change_is_dirty_before_commit() -> None:
    source = (_cue(),)

    assert subtitle_working_copy_is_dirty(
        source,
        source,
        loaded_row=0,
        pending_text="Halo\nDunia",
        pending_start="00:00:01,250",
        pending_end="00:00:02,500",
    )


def test_invalid_pending_timing_is_still_dirty() -> None:
    source = (_cue(),)

    assert subtitle_working_copy_is_dirty(
        source,
        source,
        loaded_row=0,
        pending_text="Halo\nDunia",
        pending_start="timestamp rusak",
        pending_end="00:00:02,500",
    )


def test_no_loaded_row_only_uses_working_copy_state() -> None:
    source = (_cue(),)

    assert not subtitle_working_copy_is_dirty(
        source,
        source,
        loaded_row=-1,
        pending_text="",
        pending_start="",
        pending_end="",
    )
