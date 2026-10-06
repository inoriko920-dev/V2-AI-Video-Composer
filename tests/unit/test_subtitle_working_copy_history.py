from aavc.subtitles.history import (
    SubtitleWorkingCopyHistory,
    SubtitleWorkingCopySnapshot,
)
from aavc.subtitles.srt import SubtitleCue


def _cue(index: int, text: str) -> SubtitleCue:
    return SubtitleCue(
        index=index,
        start_seconds=float(index - 1),
        end_seconds=float(index),
        text=text,
    )


def _snapshot(*cues: SubtitleCue, selected_row: int = 0) -> SubtitleWorkingCopySnapshot:
    return SubtitleWorkingCopySnapshot(tuple(cues), selected_row)


def test_history_undo_and_redo_restore_exact_snapshots() -> None:
    first = _snapshot(_cue(1, "A"), selected_row=0)
    second = _snapshot(_cue(1, "B"), selected_row=0)
    history = SubtitleWorkingCopyHistory()

    history.record(first, second)
    assert history.can_undo is True
    assert history.can_redo is False

    restored = history.undo(second)
    assert restored == first
    assert history.can_undo is False
    assert history.can_redo is True

    redone = history.redo(restored)
    assert redone == second
    assert history.can_undo is True
    assert history.can_redo is False


def test_new_edit_after_undo_discards_redo_branch() -> None:
    first = _snapshot(_cue(1, "A"))
    second = _snapshot(_cue(1, "B"))
    third = _snapshot(_cue(1, "C"))
    history = SubtitleWorkingCopyHistory()

    history.record(first, second)
    restored = history.undo(second)
    assert history.can_redo is True

    history.record(restored, third)
    assert history.can_redo is False
    assert history.undo(third) == first


def test_selection_only_change_does_not_create_history_entry() -> None:
    cue = _cue(1, "A")
    history = SubtitleWorkingCopyHistory()

    history.record(
        _snapshot(cue, selected_row=0),
        _snapshot(cue, selected_row=1),
    )

    assert history.can_undo is False
    assert history.can_redo is False


def test_unavailable_undo_redo_are_no_ops() -> None:
    current = _snapshot(_cue(1, "A"), selected_row=0)
    history = SubtitleWorkingCopyHistory()

    assert history.undo(current) is current
    assert history.redo(current) is current
