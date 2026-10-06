from __future__ import annotations

from dataclasses import dataclass

from .ffmpeg_builder import build_ffmpeg_command
from .render_plan import RenderPlan


@dataclass(frozen=True, slots=True)
class RenderSelection:
    """Validated global timeline range used only for one render invocation."""

    start_seconds: float
    end_seconds: float

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


def validate_render_selection(
    start_seconds: float,
    end_seconds: float,
    total_duration_seconds: float,
) -> RenderSelection:
    """Validate a strict In/Out range without silently changing user intent."""

    start = float(start_seconds)
    end = float(end_seconds)
    total = max(0.0, float(total_duration_seconds))
    epsilon = 1e-6

    if start < -epsilon:
        raise ValueError("In point tidak boleh berada sebelum awal project")
    if end > total + epsilon:
        raise ValueError("Out point melewati akhir project")
    start = max(0.0, start)
    end = min(total, end)
    if end - start <= epsilon:
        raise ValueError("Range In/Out render harus memiliki durasi lebih dari 0 detik")
    return RenderSelection(start, end)


def _stream_label(mapped_value: str) -> str:
    if not (mapped_value.startswith("[") and mapped_value.endswith("]")):
        raise ValueError(f"Map video canonical tidak didukung: {mapped_value}")
    return mapped_value[1:-1]


def build_ffmpeg_selection_command(
    plan: RenderPlan,
    selection: RenderSelection,
    *,
    ffmpeg: str = "ffmpeg",
) -> list[str]:
    """Trim the canonical render after composition while preserving global timing."""

    validated = validate_render_selection(
        selection.start_seconds,
        selection.end_seconds,
        plan.duration_seconds,
    )
    command = build_ffmpeg_command(plan, ffmpeg=ffmpeg)

    filter_index = command.index("-filter_complex") + 1
    map_positions = [index for index, value in enumerate(command) if value == "-map"]
    if not map_positions:
        raise ValueError("Command render canonical tidak memiliki video map")

    video_map_index = map_positions[0] + 1
    video_label = _stream_label(command[video_map_index])
    start = validated.start_seconds
    end = validated.end_seconds
    command[filter_index] += (
        f";[{video_label}]trim=start={start:.6f}:end={end:.6f},"
        "setpts=PTS-STARTPTS[vselection]"
    )
    command[video_map_index] = "[vselection]"

    if len(map_positions) > 1:
        audio_map_index = map_positions[1] + 1
        audio_source = command[audio_map_index]
        audio_filter_source = (
            audio_source if audio_source.startswith("[") else f"[{audio_source}]"
        )
        command[filter_index] += (
            f";{audio_filter_source}atrim=start={start:.6f}:end={end:.6f},"
            "asetpts=PTS-STARTPTS[aselection]"
        )
        command[audio_map_index] = "[aselection]"

    duration_index = command.index("-t") + 1
    command[duration_index] = f"{validated.duration_seconds:.3f}"
    return command
