from __future__ import annotations

from dataclasses import replace
from math import isfinite

from .srt import SubtitleCue


def stretch_subtitle_cues_from_row(
    cues: tuple[SubtitleCue, ...],
    row: int,
    factor: float,
) -> tuple[SubtitleCue, ...]:
    """Scale timing from one cue onward relative to that cue's start time."""

    if row < 0 or row >= len(cues):
        raise ValueError("Cue subtitle yang dipilih tidak valid")

    scale = float(factor)
    if scale <= 0:
        raise ValueError("Faktor stretch subtitle harus lebih besar dari 0")
    if scale == 1.0:
        return cues

    anchor = cues[row].start_seconds
    result: list[SubtitleCue] = []
    for index, cue in enumerate(cues):
        if index < row:
            result.append(cue)
            continue
        start_seconds = anchor + (cue.start_seconds - anchor) * scale
        end_seconds = anchor + (cue.end_seconds - anchor) * scale
        if start_seconds < 0:
            raise ValueError("Stretch membuat waktu mulai subtitle menjadi negatif")
        result.append(
            replace(
                cue,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
            )
        )
    return tuple(result)


def fit_subtitle_cues_from_row_to_end(
    cues: tuple[SubtitleCue, ...],
    row: int,
    target_end_seconds: float,
) -> tuple[SubtitleCue, ...]:
    """Stretch one cue onward so the final cue ends at the requested timestamp."""

    if row < 0 or row >= len(cues):
        raise ValueError("Cue subtitle yang dipilih tidak valid")

    target_end = float(target_end_seconds)
    if not isfinite(target_end):
        raise ValueError("Target OUT akhir subtitle harus berupa waktu yang valid")

    anchor = cues[row].start_seconds
    if target_end <= anchor:
        raise ValueError("Target OUT akhir harus lebih besar dari waktu mulai cue terpilih")

    current_end = cues[-1].end_seconds
    source_span = current_end - anchor
    if not isfinite(source_span) or source_span <= 0:
        raise ValueError("Rentang timing subtitle dari cue terpilih tidak valid untuk di-fit")
    if target_end == current_end:
        return cues

    factor = (target_end - anchor) / source_span
    return stretch_subtitle_cues_from_row(cues, row, factor)
