from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from aavc.domain.errors import RenderError
from aavc.platform.process_runner import ProcessRunner

from .render_plan import RenderPlan


@dataclass(frozen=True, slots=True)
class RenderManifest:
    backend_id: str
    expected_duration_seconds: float
    width: int
    height: int
    fps: int
    scene_count: int
    expects_audio: bool
    burns_subtitles: bool
    video_codec: str
    encoder_preset: str
    crf: int

    @classmethod
    def from_plan(
        cls,
        plan: RenderPlan,
        *,
        expected_duration_seconds: float | None = None,
        backend_id: str = "ffmpeg-cli",
    ) -> RenderManifest:
        return cls(
            backend_id=backend_id,
            expected_duration_seconds=(
                plan.duration_seconds
                if expected_duration_seconds is None
                else float(expected_duration_seconds)
            ),
            width=plan.width,
            height=plan.height,
            fps=plan.fps,
            scene_count=len(plan.scenes),
            expects_audio=plan.narration_audio is not None,
            burns_subtitles=plan.subtitle_ass is not None,
            video_codec=plan.quality.video_codec,
            encoder_preset=plan.quality.encoder_preset,
            crf=plan.quality.crf,
        )


@dataclass(frozen=True, slots=True)
class RenderVerification:
    path: str
    file_size: int
    duration_seconds: float
    width: int
    height: int
    fps: float
    has_video: bool
    has_audio: bool


def _parse_rate(value: object) -> float:
    text = str(value or "0")
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        den = float(denominator)
        return float(numerator) / den if den else 0.0
    return float(text)


def verify_render_output(
    path: str | Path,
    manifest: RenderManifest,
    *,
    ffprobe: str,
    runner: ProcessRunner | None = None,
) -> RenderVerification:
    if (
        not math.isfinite(manifest.expected_duration_seconds)
        or manifest.expected_duration_seconds <= 0
    ):
        raise RenderError("Manifest durasi render tidak valid")

    candidate = Path(path)
    if not candidate.is_file() or candidate.stat().st_size <= 0:
        raise RenderError("Output render kosong atau tidak ditemukan")

    process_runner = runner or ProcessRunner()
    result = process_runner.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height,r_frame_rate",
            "-of",
            "json",
            str(candidate),
        ],
        timeout_seconds=30.0,
    )
    if result.returncode != 0:
        raise RenderError(result.stderr[-2000:] or "ffprobe gagal memvalidasi output render")

    try:
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise ValueError("ffprobe root is not an object")
        streams = payload.get("streams")
        format_info = payload.get("format")
        if (
            not isinstance(streams, list)
            or not all(isinstance(stream, dict) for stream in streams)
            or not isinstance(format_info, dict)
        ):
            raise ValueError("ffprobe streams/format have invalid structure")
        video_stream = next(
            stream for stream in streams if stream.get("codec_type") == "video"
        )
        duration = float(format_info["duration"])
        width = int(video_stream["width"])
        height = int(video_stream["height"])
        fps = _parse_rate(video_stream.get("r_frame_rate"))
        if (
            not math.isfinite(duration)
            or duration <= 0
            or not math.isfinite(fps)
            or fps <= 0
            or width <= 0
            or height <= 0
        ):
            raise ValueError("ffprobe video metadata is non-finite or non-positive")
    except (KeyError, TypeError, ValueError, StopIteration) as error:
        raise RenderError("Output ffprobe tidak memiliki metadata video yang valid") from error

    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
    tolerance = max(0.25, 2.0 / max(1, manifest.fps))
    problems: list[str] = []
    if width != manifest.width or height != manifest.height:
        problems.append(
            f"resolusi {width}x{height}, expected {manifest.width}x{manifest.height}"
        )
    if abs(fps - manifest.fps) > 0.05:
        problems.append(f"fps {fps:.3f}, expected {manifest.fps}")
    if abs(duration - manifest.expected_duration_seconds) > tolerance:
        problems.append(
            f"durasi {duration:.3f}s, expected {manifest.expected_duration_seconds:.3f}s"
        )
    if manifest.expects_audio and not has_audio:
        problems.append("stream audio yang diharapkan tidak ditemukan")
    if problems:
        raise RenderError("Validasi output render gagal: " + "; ".join(problems))

    return RenderVerification(
        path=str(candidate),
        file_size=candidate.stat().st_size,
        duration_seconds=duration,
        width=width,
        height=height,
        fps=fps,
        has_video=True,
        has_audio=has_audio,
    )
