from __future__ import annotations

from dataclasses import replace

from .srt import SubtitleCue


def resolve_subtitle_cue_overlap(
    cues: tuple[SubtitleCue, ...],
    row: int,
) -> tuple[SubtitleCue, ...]:
    """Shift one overlapping cue after the previous cue while preserving duration."""

    if row < 0 or row >= len(cues):
        raise ValueError("Cue subtitle yang dipilih tidak valid")
    if row == 0:
        return cues

    previous = cues[row - 1]
    cue = cues[row]
    if cue.start_seconds >= previous.end_seconds:
        return cues

    delta = previous.end_seconds - cue.start_seconds
    resolved = replace(
        cue,
        start_seconds=previous.end_seconds,
        end_seconds=cue.end_seconds + delta,
    )
    items = list(cues)
    items[row] = resolved
    return tuple(items)
