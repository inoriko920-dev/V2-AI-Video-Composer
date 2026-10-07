from __future__ import annotations

import shutil
import statistics
import time
from pathlib import Path

import pytest

from aavc.animation import evaluate_assignment_crop_visibility
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
from aavc.rendering.advanced_filters import compile_k2_crop_filters


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
    end: float,
) -> AnimationKeyframeTrack:
    return AnimationKeyframeTrack(
        property_name=property_name,  # type: ignore[arg-type]
        keyframes=(
            AnimationKeyframe(time=0.0, value=start, easing="ease_in_out"),
            AnimationKeyframe(time=1.0, value=end),
        ),
    )


def _crop_assignment() -> AnimationAssignment:
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        intensity=0.0,
        keyframe_tracks=(
            _track("crop_left", 0.00, 0.25),
            _track("crop_top", 0.10, 0.20),
            _track("crop_right", 0.15, 0.00),
            _track("crop_bottom", 0.00, 0.10),
        ),
    )


def _project(asset: Path) -> ProjectState:
    assignment = _crop_assignment()
    return ProjectState(
        schema_version=4,
        title="K2 crop integration",
        source_docx="synthetic-k2.docx",
        asset_directory=str(asset.parent),
        scenes=(
            Scene(
                scene_number=1,
                asset_ids=("A001",),
                source_quotes=("K2 crop",),
                duration_seconds=1.0,
            ),
        ),
        bindings=(
            AssetBinding(
                asset_id="A001",
                source_quote="K2 crop",
                path=str(asset),
                status="READY",
            ),
        ),
        fps=12,
        width=320,
        height=180,
        animations=(assignment,),
        render_quality=RenderQualitySettings(
            preset_name="K2 Fast",
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


def _crop_filter_chain(
    assignment: AnimationAssignment,
    *,
    duration_seconds: float,
    instance_id: str,
) -> str:
    filters = compile_k2_crop_filters(
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
    assignment = _crop_assignment()
    output = tmp_path / f"{asset.stem}-crop-alpha.raw"
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
        _crop_filter_chain(
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
        crop = evaluate_assignment_crop_visibility(
            assignment,
            frame_index / 4.0,
        )
        for y in range(height):
            for x in range(width):
                visible = (
                    x >= width * crop.left
                    and x < width * (1.0 - crop.right)
                    and y >= height * crop.top
                    and y < height * (1.0 - crop.bottom)
                )
                expected = source_alpha if visible else 0
                actual = frame[y * width + x]
                if abs(actual - expected) <= 1:
                    continue
                edge_distance = min(
                    abs(x - width * crop.left),
                    abs(x - width * (1.0 - crop.right)),
                    abs(y - height * crop.top),
                    abs(y - height * (1.0 - crop.bottom)),
                )
                assert edge_distance <= 1.0
    return frames


@pytest.mark.integration
def test_k2_dynamic_spatial_alpha_capability_probe_passes_on_real_ffmpeg() -> None:
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
def test_k2_real_ffmpeg_crop_matches_canonical_edges_for_rgb_and_rgba(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    width = 20
    height = 12
    rgb = tmp_path / "crop-rgb.ppm"
    rgba = tmp_path / "crop-rgba.pam"
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
def test_k2_advanced_project_completes_real_render_and_selection(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        pytest.skip("ffprobe not available")

    asset = tmp_path / "k2-app.ppm"
    _write_ppm(asset, width=160, height=90)
    project = _project(asset)

    output = tmp_path / "k2-crop.mp4"
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

    selection = tmp_path / "k2-selection.mp4"
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
def test_k2_crop_reference_resolution_and_60fps_smoke(
    width: int,
    height: int,
    fps: int,
) -> None:
    ffmpeg = _require_ffmpeg()
    runner = ProcessRunner()
    filters = compile_k2_crop_filters(
        _crop_assignment(),
        duration_seconds=0.12,
        instance_id=f"smoke_{width}_{height}_{fps}",
    )
    assert filters
    graph = ",".join(filters)
    result = runner.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c=red:s={width}x{height}:r={fps}:d=0.12",
            "-vf",
            graph,
            "-frames:v",
            "2",
            "-f",
            "null",
            "-",
        ],
        timeout_seconds=30.0,
    )
    assert result.returncode == 0, result.stderr


def _timed_run(runner: ProcessRunner, command: list[str]) -> float:
    started = time.perf_counter()
    result = runner.run(command, timeout_seconds=30.0)
    elapsed = time.perf_counter() - started
    assert result.returncode == 0, result.stderr
    return elapsed


@pytest.mark.integration
def test_k2_crop_performance_is_within_2_5x_baseline() -> None:
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
    crop_filters = compile_k2_crop_filters(
        _crop_assignment(),
        duration_seconds=1.0,
        instance_id="k2_perf",
    )
    assert crop_filters
    crop_graph = ",".join(crop_filters)
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
        crop_graph,
        "-f",
        "null",
        "-",
    ]

    _timed_run(runner, base)
    _timed_run(runner, advanced)
    baseline_times = [_timed_run(runner, base) for _ in range(3)]
    crop_times = [_timed_run(runner, advanced) for _ in range(3)]

    baseline = statistics.median(baseline_times)
    crop = statistics.median(crop_times)
    assert baseline > 0
    assert crop / baseline <= 2.5
