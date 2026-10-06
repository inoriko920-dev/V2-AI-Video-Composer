from __future__ import annotations

from aavc.subtitles.srt import SubtitleCue, format_srt_timestamp


def subtitle_working_copy_is_dirty(
    source_cues: tuple[SubtitleCue, ...],
    working_cues: tuple[SubtitleCue, ...],
    *,
    loaded_row: int,
    pending_text: str,
    pending_start: str,
    pending_end: str,
) -> bool:
    """Return whether reload would discard working-copy or pending form edits."""

    if working_cues != source_cues:
        return True
    if loaded_row < 0 or loaded_row >= len(working_cues):
        return False

    cue = working_cues[loaded_row]
    return (
        pending_text != cue.text.replace("\\N", "\n")
        or pending_start != format_srt_timestamp(cue.start_seconds)
        or pending_end != format_srt_timestamp(cue.end_seconds)
    )
