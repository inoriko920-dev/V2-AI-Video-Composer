from __future__ import annotations

from dataclasses import replace

from .srt import SubtitleCue


def shift_subtitle_cues(
    cues: tuple[SubtitleCue, ...],
    offset_seconds: float,
) -> tuple[SubtitleCue, ...]:
    """Shift every cue by one offset while preserving text, index, and duration."""

    offset = float(offset_seconds)
    if offset == 0.0 or not cues:
        return cues

    earliest_start = min(cue.start_seconds for cue in cues)
    if earliest_start + offset < 0:
        raise ValueError("Offset membuat waktu mulai subtitle menjadi negatif")

    return tuple(
        replace(
            cue,
            start_seconds=cue.start_seconds + offset,
            end_seconds=cue.end_seconds + offset,
        )
        for cue in cues
    )


def shift_subtitle_cues_from_row(
    cues: tuple[SubtitleCue, ...],
    row: int,
    offset_seconds: float,
) -> tuple[SubtitleCue, ...]:
    """Shift the selected cue and every later cue by one offset."""

    if row < 0 or row >= len(cues):
        raise ValueError("Cue subtitle yang dipilih tidak valid")

    offset = float(offset_seconds)
    if offset == 0.0:
        return cues

    if cues[row].start_seconds + offset < 0:
        raise ValueError("Offset membuat waktu mulai subtitle menjadi negatif")

    return tuple(
        cue
        if index < row
        else replace(
            cue,
            start_seconds=cue.start_seconds + offset,
            end_seconds=cue.end_seconds + offset,
        )
        for index, cue in enumerate(cues)
    )
