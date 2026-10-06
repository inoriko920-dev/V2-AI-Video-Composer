from __future__ import annotations

from .srt import SubtitleCue, parse_srt_timestamp, replace_subtitle_cue


def commit_pending_subtitle_edit(
    cues: tuple[SubtitleCue, ...],
    loaded_row: int,
    *,
    text: str,
    start_timestamp: str,
    end_timestamp: str,
) -> tuple[SubtitleCue, ...]:
    """Commit form values to the cue that was loaded before selection changed."""

    if loaded_row < 0 or loaded_row >= len(cues):
        return cues
    return replace_subtitle_cue(
        cues,
        loaded_row,
        text=text,
        start_seconds=parse_srt_timestamp(start_timestamp),
        end_seconds=parse_srt_timestamp(end_timestamp),
    )
