from __future__ import annotations

from dataclasses import dataclass

from aavc.subtitles import SubtitleCue


@dataclass(frozen=True, slots=True)
class SubtitleCueView:
    index: int
    start_seconds: float
    end_seconds: float
    text: str
    overlaps_previous: bool

    @property
    def start_label(self) -> str:
        return format_srt_time(self.start_seconds)

    @property
    def end_label(self) -> str:
        return format_srt_time(self.end_seconds)

    @property
    def list_label(self) -> str:
        warning = "  ⚠" if self.overlaps_previous else ""
        preview = self.text.replace("\\N", " ")
        return (
            f"{self.index}   {self.start_label} → {self.end_label}{warning}\n"
            f"{preview}"
        )


def format_srt_time(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_subtitle_views(cues: tuple[SubtitleCue, ...]) -> tuple[SubtitleCueView, ...]:
    views: list[SubtitleCueView] = []
    previous_end: float | None = None
    for cue in cues:
        overlaps = previous_end is not None and cue.start_seconds < previous_end
        views.append(
            SubtitleCueView(
                index=cue.index,
                start_seconds=cue.start_seconds,
                end_seconds=cue.end_seconds,
                text=cue.text,
                overlaps_previous=overlaps,
            )
        )
        previous_end = cue.end_seconds
    return tuple(views)
