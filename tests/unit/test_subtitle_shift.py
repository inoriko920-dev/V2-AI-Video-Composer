from __future__ import annotations

from aavc.subtitles import (
    SubtitleCue,
    SubtitleWorkingCopyHistory,
    SubtitleWorkingCopySnapshot,
    parse_srt,
    shift_subtitle_cues,
    write_srt_atomic,
)


def _cues() -> tuple[SubtitleCue, ...]:
    return (
        SubtitleCue(7, 1.25, 2.75, "Pertama"),
        SubtitleCue(11, 3.0, 4.5, "Kedua\\Nbaris dua"),
    )


def test_shift_all_cues_forward_preserves_index_text_and_duration() -> None:
    source = _cues()
    shifted = shift_subtitle_cues(source, 0.5)

    assert [(cue.start_seconds, cue.end_seconds) for cue in shifted] == [
        (1.75, 3.25),
        (3.5, 5.0),
    ]
    assert [cue.index for cue in shifted] == [7, 11]
    assert [cue.text for cue in shifted] == ["Pertama", "Kedua\\Nbaris dua"]
    assert [cue.end_seconds - cue.start_seconds for cue in shifted] == [1.5, 1.5]


def test_shift_all_cues_backward_when_result_stays_non_negative() -> None:
    shifted = shift_subtitle_cues(_cues(), -1.0)

    assert shifted[0].start_seconds == 0.25
    assert shifted[0].end_seconds == 1.75
    assert shifted[1].start_seconds == 2.0
    assert shifted[1].end_seconds == 3.5


def test_shift_rejects_negative_result_without_mutating_source() -> None:
    source = _cues()

    try:
        shift_subtitle_cues(source, -1.251)
    except ValueError as error:
        assert "negatif" in str(error)
    else:
        raise AssertionError("Offset negatif yang melewati nol harus ditolak")

    assert source == _cues()


def test_zero_offset_and_empty_input_are_identity_noops() -> None:
    source = _cues()
    assert shift_subtitle_cues(source, 0.0) is source
    empty: tuple[SubtitleCue, ...] = ()
    assert shift_subtitle_cues(empty, 0.75) is empty


def test_shift_can_be_recorded_as_one_working_copy_history_step() -> None:
    source = SubtitleWorkingCopySnapshot(_cues(), 1)
    shifted = SubtitleWorkingCopySnapshot(shift_subtitle_cues(source.cues, 0.25), 1)
    history = SubtitleWorkingCopyHistory()

    history.record(source, shifted)

    assert history.can_undo
    assert history.undo(shifted) == source
    assert history.can_redo
    assert history.redo(source) == shifted


def test_shifted_cues_survive_srt_write_parse_round_trip(tmp_path) -> None:
    shifted = shift_subtitle_cues(_cues(), 0.375)
    target = tmp_path / "shifted.srt"

    write_srt_atomic(target, shifted)
    parsed = parse_srt(target)

    assert parsed == shifted
