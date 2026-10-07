from __future__ import annotations

import math
import shutil
import statistics
import time
from pathlib import Path

import pytest

from aavc.animation import evaluate_assignment_advanced_keyframe
from aavc.animation.contract import (
    ADVANCED_KEYFRAME_CONTRACT,
    ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY,
)
from aavc.application.services.export_service import ExportOptions, render_project
from aavc.application.services.selection_export_service import render_project_selection
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import (
    AnimationAssignment,
    AssetBinding,
    ProjectState,
    RenderQualitySettings,
    Scene,
)
from aavc.platform.process_runner import ProcessRunner
from aavc.platform.tool_registry import ToolResolution
from aavc.rendering.advanced_capabilities import (
    AdvancedFFmpegCapabilityProbe,
    AdvancedFFmpegFeature,
)
from aavc.rendering.advanced_filters import compile_k5_mask_filters


def _write_ppm(
    path: Path,
    *,
    width: int,
    height: int,
    rgb: tuple[int, int, int] = (240, 32, 32),
) -> None:
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + bytes(rgb) * (width * height))


def _write_pam_rgba(
    path: Path,
    *,
    width: int,
    height: int,
    rgba: tuple[int, int, int, int] = (240, 32, 32, 128),
) -> None:
    header = (
        "P7\n"
        f"WIDTH {width}\n"
        f"HEIGHT {height}\n"
        "DEPTH 4\n"
        "MAXVAL 255\n"
        "TUPLTYPE RGB_ALPHA\n"
        "ENDHDR\n"
    ).encode("ascii")
    path.write_bytes(header + bytes(rgba) * (width * height))


def _track(
    property_name: str,
    start: float,
    end: float | None = None,
) -> AnimationKeyframeTrack:
    points = [AnimationKeyframe(time=0.0, value=start)]
    if end is not None:
        points.append(AnimationKeyframe(time=1.0, value=end))
    return AnimationKeyframeTrack(
        property_name=property_name,  # type: ignore[arg-type]
        keyframes=tuple(points),
    )


def _mask_assignment(*, with_shadow: bool = False) -> AnimationAssignment:
    tracks: list[AnimationKeyframeTrack] = [
        _track("mask_progress", 0.0, 1.0),
    ]
    if with_shadow:
        tracks.append(_track("shadow", 0.35, None))
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        intensity=0.0,
        keyframe_tracks=tuple(tracks),
    )


def _project(asset: Path, *, with_shadow: bool = True) -> ProjectState:
    return ProjectState(
        schema_version=4,
        title="K5 mask progress integration",
        source_docx="synthetic-k5.docx",
        asset_directory=str(asset.parent),
        scenes=(
            Scene(
                scene_number=1,
                asset_ids=("A001",),
                source_quotes=("K5 mask progress",),
                duration_seconds=1.0,
            ),
        ),
        bindings=(
            AssetBinding(
                asset_id="A001",
                source_quote="K5 mask progress",
                path=str(asset),
                status="READY",
            ),
        ),
        fps=12,
        width=320,
        height=180,
        animations=(_mask_assignment(with_shadow=with_shadow),),
        render_quality=RenderQualitySettings(
            preset_name="K5 Fast",
            video_codec="libx264",
            encoder_preset="ultrafast",
            crf=30,
            audio_bitrate_kbps=128,
            scale_algorithm="bilinear",
            sharpen_amount=0.0,
        ),
        metadata={
            ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY: ADVANCED_KEYFRAME_CONTRACT,
        },
    )


def _require_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg not available")
    return ffmpeg


def _mask_filter_chain(
    assignment: AnimationAssignment,
    *,
    duration_seconds: float,
    instance_id: str,
) -> str:
    filters = compile_k5_mask_filters(
        assignment,
        duration_seconds=duration_seconds,
        instance_id=instance_id,
    )
    assert filters
    return ",".join(filters)


def _render_alpha_frames(
    tmp_path: Path,
    *,
    ffmpeg: str,
    asset: Path,
    source_alpha: int,
    width: int,
    height: int,
) -> tuple[bytes, ...]:
    assignment = _mask_assignment()
    output = tmp_path / f"{asset.stem}-mask-alpha.raw"
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-framerate",
        "4",
        "-i",
        str(asset),
        "-vf",
        _mask_filter_chain(
            assignment,
            duration_seconds=1.0,
            instance_id=f"alpha_{asset.stem}",
        )
        + ",alphaextract",
        "-frames:v",
        "4",
        "-pix_fmt",
        "gray",
        "-f",
        "rawvideo",
        str(output),
    ]
    result = ProcessRunner().run(command, timeout_seconds=30.0)
    assert result.returncode == 0, result.stderr

    raw = output.read_bytes()
    frame_size = width * height
    assert len(raw) == frame_size * 4
    frames = tuple(
        raw[index * frame_size : (index + 1) * frame_size]
        for index in range(4)
    )

    for frame_index, frame in enumerate(frames):
        progress = evaluate_assignment_advanced_keyframe(
            assignment,
            "mask_progress",
            frame_index / 4.0,
        )
        assert progress is not None
        boundary = math.ceil(width * progress)
        for y in range(height):
            for x in range(width):
                expected = source_alpha if x < boundary else 0
                actual = frame[y * width + x]
                if abs(actual - expected) <= 1:
                    continue
                assert abs(x - boundary) <= 1
    return frames


@pytest.mark.integration
def test_k5_real_ffmpeg_uses_proven_dynamic_spatial_alpha() -> None:
    ffmpeg = _require_ffmpeg()
    capabilities = AdvancedFFmpegCapabilityProbe(
        resolver=lambda: ToolResolution(
            name="ffmpeg",
            path=ffmpeg,
            source="integration",
        )
    ).probe()

    assert capabilities.available
    assert capabilities.supports(AdvancedFFmpegFeature.DYNAMIC_SPATIAL_ALPHA)


@pytest.mark.integration
def test_k5_real_ffmpeg_mask_matches_canonical_edge_for_rgb_and_rgba(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    width = 20
    height = 12
    rgb = tmp_path / "mask-rgb.ppm"
    rgba = tmp_path / "mask-rgba.pam"
    _write_ppm(rgb, width=width, height=height)
    _write_pam_rgba(rgba, width=width, height=height)

    rgb_frames = _render_alpha_frames(
        tmp_path,
        ffmpeg=ffmpeg,
        asset=rgb,
        source_alpha=255,
        width=width,
        height=height,
    )
    rgba_frames = _render_alpha_frames(
        tmp_path,
        ffmpeg=ffmpeg,
        asset=rgba,
        source_alpha=128,
        width=width,
        height=height,
    )

    assert max(rgb_frames[-1]) == 255
    assert max(rgba_frames[-1]) == 128


@pytest.mark.integration
def test_k5_mask_shadow_project_completes_real_render_and_selection(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        pytest.skip("ffprobe not available")

    asset = tmp_path / "k5-app.ppm"
    _write_ppm(asset, width=160, height=90)
    project = _project(asset, with_shadow=True)

    output = tmp_path / "k5-mask-shadow.mp4"
    result = render_project(
        project,
        ExportOptions(
            output_path=str(output),
            video_codec="libx264",
            encoder_preset="ultrafast",
            crf=30,
            width=320,
            height=180,
            fps=12,
            sharpen_amount=0.0,
            burn_subtitles=False,
        ),
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    assert Path(result.output_path).is_file()
    assert Path(result.output_path).stat().st_size > 500

    selection = tmp_path / "k5-selection.mp4"
    selection_result = render_project_selection(
        project,
        ExportOptions(
            output_path=str(selection),
            video_codec="libx264",
            encoder_preset="ultrafast",
            crf=30,
            width=320,
            height=180,
            fps=12,
            sharpen_amount=0.0,
            burn_subtitles=False,
        ),
        start_seconds=0.2,
        end_seconds=0.8,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    assert Path(selection_result.output_path).is_file()
    assert Path(selection_result.output_path).stat().st_size > 500


@pytest.mark.integration
@pytest.mark.parametrize(
    ("width", "height", "fps"),
    [
        (1280, 720, 30),
        (1920, 1080, 30),
        (3840, 2160, 30),
        (640, 360, 60),
    ],
)
def test_k5_mask_reference_resolution_and_60fps_smoke(
    width: int,
    height: int,
    fps: int,
) -> None:
    ffmpeg = _require_ffmpeg()
    filters = compile_k5_mask_filters(
        _mask_assignment(),
        duration_seconds=0.12,
        instance_id=f"k5_smoke_{width}_{height}_{fps}",
    )
    assert filters

    result = ProcessRunner().run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c=red:s={width}x{height}:r={fps}:d=0.12,format=rgba",
            "-vf",
            ",".join(filters),
            "-frames:v",
            "2",
            "-f",
            "null",
            "-",
        ],
        timeout_seconds=60.0,
    )
    assert result.returncode == 0, result.stderr


def _timed_run(runner: ProcessRunner, command: list[str]) -> float:
    started = time.perf_counter()
    result = runner.run(command, timeout_seconds=30.0)
    elapsed = time.perf_counter() - started
    assert result.returncode == 0, result.stderr
    return elapsed


@pytest.mark.integration
def test_k5_mask_performance_is_within_2_5x_baseline() -> None:
    ffmpeg = _require_ffmpeg()
    runner = ProcessRunner()
    source = "color=c=red:s=640x360:r=30:d=1.0"

    base = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        source,
        "-vf",
        "format=rgba",
        "-f",
        "null",
        "-",
    ]

    filters = compile_k5_mask_filters(
        _mask_assignment(),
        duration_seconds=1.0,
        instance_id="k5_perf",
    )
    assert filters
    advanced = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        source,
        "-vf",
        ",".join(filters),
        "-f",
        "null",
        "-",
    ]

    _timed_run(runner, base)
    _timed_run(runner, advanced)
    baseline_times = [_timed_run(runner, base) for _ in range(3)]
    mask_times = [_timed_run(runner, advanced) for _ in range(3)]

    baseline = statistics.median(baseline_times)
    mask = statistics.median(mask_times)
    assert baseline > 0
    assert mask / baseline <= 2.5
