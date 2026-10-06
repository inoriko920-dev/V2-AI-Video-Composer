from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

_TIME_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")


@dataclass(frozen=True, slots=True)
class SubtitleCue:
    index: int
    start_seconds: float
    end_seconds: float
    text: str


def parse_srt_timestamp(value: str) -> float:
    match = _TIME_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Timestamp SRT tidak valid: {value}")
    h, m, s, ms = map(int, match.groups())
    if m >= 60 or s >= 60:
        raise ValueError(f"Timestamp SRT tidak valid: {value}")
    return h * 3600 + m * 60 + s + ms / 1000


def format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("Timestamp SRT tidak boleh negatif")
    total_ms = int(round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _normalize_cue_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return "\\N".join(line.strip() for line in normalized.splitlines())


def _validate_cue(cue: SubtitleCue) -> None:
    if cue.start_seconds < 0:
        raise ValueError("Waktu mulai cue tidak boleh negatif")
    if cue.end_seconds <= cue.start_seconds:
        raise ValueError("Waktu selesai cue harus lebih besar dari waktu mulai")
    if not cue.text.replace("\\N", "\n").strip():
        raise ValueError("Teks cue tidak boleh kosong")


def parse_srt(path: str | Path) -> tuple[SubtitleCue, ...]:
    text = (
        Path(path)
        .read_text(encoding="utf-8-sig")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    if not blocks:
        raise ValueError("File SRT tidak memiliki cue subtitle yang valid")

    cues: list[SubtitleCue] = []
    for block_number, block in enumerate(blocks, start=1):
        lines = block.splitlines()
        if len(lines) < 3:
            raise ValueError(
                f"Blok SRT #{block_number} tidak lengkap; minimal index, timing, dan teks"
            )

        index = int(lines[0].strip())
        timing_parts = [part.strip() for part in lines[1].split("-->", 1)]
        if len(timing_parts) != 2:
            raise ValueError(f"Timing blok SRT #{block_number} tidak valid")

        cue = SubtitleCue(
            index=index,
            start_seconds=parse_srt_timestamp(timing_parts[0]),
            end_seconds=parse_srt_timestamp(timing_parts[1]),
            text="\\N".join(line.strip() for line in lines[2:] if line.strip()),
        )
        _validate_cue(cue)
        cues.append(cue)

    return tuple(cues)


def replace_subtitle_cue(
    cues: tuple[SubtitleCue, ...],
    row: int,
    *,
    text: str,
    start_seconds: float,
    end_seconds: float,
) -> tuple[SubtitleCue, ...]:
    if row < 0 or row >= len(cues):
        raise ValueError("Cue subtitle yang dipilih tidak valid")
    replacement = replace(
        cues[row],
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        text=_normalize_cue_text(text),
    )
    _validate_cue(replacement)
    items = list(cues)
    items[row] = replacement
    return tuple(items)


def insert_subtitle_cue(
    cues: tuple[SubtitleCue, ...],
    after_row: int,
    *,
    text: str,
    start_seconds: float,
    end_seconds: float,
) -> tuple[SubtitleCue, ...]:
    if after_row < -1 or after_row >= len(cues):
        raise ValueError("Posisi cue baru tidak valid")
    next_index = max((cue.index for cue in cues), default=0) + 1
    new_cue = SubtitleCue(
        index=next_index,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        text=_normalize_cue_text(text),
    )
    _validate_cue(new_cue)
    items = list(cues)
    items.insert(after_row + 1, new_cue)
    return tuple(items)


def duplicate_subtitle_cue(
    cues: tuple[SubtitleCue, ...],
    row: int,
) -> tuple[SubtitleCue, ...]:
    if row < 0 or row >= len(cues):
        raise ValueError("Cue subtitle yang dipilih tidak valid")
    source = cues[row]
    duplicate = replace(
        source,
        index=max((cue.index for cue in cues), default=0) + 1,
    )
    _validate_cue(duplicate)
    items = list(cues)
    items.insert(row + 1, duplicate)
    return tuple(items)


def split_subtitle_cue(
    cues: tuple[SubtitleCue, ...],
    row: int,
    *,
    text_offset: int,
    split_seconds: float | None = None,
) -> tuple[SubtitleCue, ...]:
    if row < 0 or row >= len(cues):
        raise ValueError("Cue subtitle yang dipilih tidak valid")
    cue = cues[row]
    plain_text = cue.text.replace("\\N", "\n")
    if text_offset <= 0 or text_offset >= len(plain_text):
        raise ValueError("Posisi kursor harus berada di tengah teks cue")
    left_text = plain_text[:text_offset].strip()
    right_text = plain_text[text_offset:].strip()
    if not left_text or not right_text:
        raise ValueError("Kedua hasil Pisah Cue harus memiliki teks")

    split_time = (
        (cue.start_seconds + cue.end_seconds) / 2
        if split_seconds is None
        else split_seconds
    )
    if not cue.start_seconds < split_time < cue.end_seconds:
        raise ValueError("Waktu pisah harus berada di dalam rentang cue")

    first = replace(
        cue,
        end_seconds=split_time,
        text=_normalize_cue_text(left_text),
    )
    second = SubtitleCue(
        index=max((item.index for item in cues), default=0) + 1,
        start_seconds=split_time,
        end_seconds=cue.end_seconds,
        text=_normalize_cue_text(right_text),
    )
    _validate_cue(first)
    _validate_cue(second)
    items = list(cues)
    items[row : row + 1] = [first, second]
    return tuple(items)


def merge_subtitle_cues(
    cues: tuple[SubtitleCue, ...],
    row: int,
) -> tuple[SubtitleCue, ...]:
    if row < 0 or row >= len(cues):
        raise ValueError("Cue subtitle yang dipilih tidak valid")
    if row + 1 >= len(cues):
        raise ValueError("Cue terakhir tidak memiliki cue berikutnya untuk digabung")
    first = cues[row]
    second = cues[row + 1]
    first_text = first.text.replace("\\N", "\n")
    second_text = second.text.replace("\\N", "\n")
    merged = SubtitleCue(
        index=first.index,
        start_seconds=first.start_seconds,
        end_seconds=max(first.end_seconds, second.end_seconds),
        text=_normalize_cue_text(f"{first_text}\n{second_text}"),
    )
    _validate_cue(merged)
    items = list(cues)
    items[row : row + 2] = [merged]
    return tuple(items)


def delete_subtitle_cue(
    cues: tuple[SubtitleCue, ...],
    row: int,
) -> tuple[SubtitleCue, ...]:
    if row < 0 or row >= len(cues):
        raise ValueError("Cue subtitle yang dipilih tidak valid")
    if len(cues) <= 1:
        raise ValueError("Cue terakhir tidak dapat dihapus; sisakan minimal satu cue subtitle")
    items = list(cues)
    del items[row]
    return tuple(items)


def normalize_subtitle_cue_indexes(
    cues: tuple[SubtitleCue, ...],
) -> tuple[SubtitleCue, ...]:
    """Normalize cue indexes to 1..N without changing cue order, timing, or text."""

    return tuple(
        cue if cue.index == index else replace(cue, index=index)
        for index, cue in enumerate(cues, start=1)
    )


def sort_subtitle_cues_by_start_time(
    cues: tuple[SubtitleCue, ...],
) -> tuple[SubtitleCue, ...]:
    """Stably sort cues by start time without mutating cue contents."""

    return tuple(sorted(cues, key=lambda cue: cue.start_seconds))


def serialize_srt(cues: tuple[SubtitleCue, ...]) -> str:
    blocks: list[str] = []
    for cue in cues:
        _validate_cue(cue)
        lines = [
            str(cue.index),
            f"{format_srt_timestamp(cue.start_seconds)} --> {format_srt_timestamp(cue.end_seconds)}",
            *cue.text.replace("\\N", "\n").splitlines(),
        ]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def write_srt_atomic(path: str | Path, cues: tuple[SubtitleCue, ...]) -> Path:
    destination = Path(path).expanduser()
    if destination.suffix.lower() != ".srt":
        raise ValueError("File subtitle hasil edit harus berekstensi .srt")
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = serialize_srt(cues)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        text=True,
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(content, encoding="utf-8", newline="\n")
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination.resolve()
