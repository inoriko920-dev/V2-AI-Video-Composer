from __future__ import annotations

import shutil
import statistics
import time
from pathlib import Path

import pytest

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
from aavc.rendering.advanced_filters import (
    compile_k3_blur_filters,
    compile_k4_shadow_glow_clauses,
)


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


def _assignment(
    *,
    shadow: tuple[float, float | None] | None = None,
    glow: tuple[float, float | None] | None = None,
    blur: tuple[float, float | None] | None = None,
) -> AnimationAssignment:
    tracks: list[AnimationKeyframeTrack] = []
    if shadow is not None:
        tracks.append(_track("shadow", shadow[0], shadow[1]))
    if glow is not None:
        tracks.append(_track("glow", glow[0], glow[1]))
    if blur is not None:
        tracks.append(_track("blur", blur[0], blur[1]))
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        intensity=0.0,
        keyframe_tracks=tuple(tracks),
    )


def _write_ppm(
    path: Path,
    *,
    width: int,
    height: int,
    rgb: tuple[int, int, int] = (240, 32, 32),
) -> None:
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + bytes(rgb) * (width * height))


def _project(asset: Path) -> ProjectState:
    return ProjectState(
        schema_version=4,
        title="K4 shadow glow integration",
        source_docx="synthetic-k4.docx",
        asset_directory=str(asset.parent),
        scenes=(
            Scene(
                scene_number=1,
                asset_ids=("A001",),
                source_quotes=("K4 shadow glow",),
                duration_seconds=1.0,
            ),
        ),
        bindings=(
            AssetBinding(
                asset_id="A001",
                source_quote="K4 shadow glow",
                path=str(asset),
                status="READY",
            ),
        ),
        fps=12,
        width=320,
        height=180,
        animations=(
            _assignment(
                shadow=(0.2, 0.8),
                glow=(0.1, 0.7),
            ),
        ),
        render_quality=RenderQualitySettings(
            preset_name="K4 Fast",
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


def _pattern_source(*, rate: int = 4, duration: float = 1.0) -> str:
    return (
        f"color=c=black@0:s=32x32:r={rate}:d={duration},"
        "format=rgba,"
        "drawbox=x=10:y=10:w=8:h=8:color=red@1:t=fill:replace=1"
    )


def _render_k4_raw(
    tmp_path: Path,
    *,
    ffmpeg: str,
    name: str,
    assignment: AnimationAssignment,
    fps: int,
    frames: int,
    canvas_width: int = 320,
    canvas_height: int = 180,
    source_rate: int | None = None,
) -> bytes:
    clauses = compile_k4_shadow_glow_clauses(
        "0:v",
        "k4out",
        assignment,
        duration_seconds=1.0,
        fps=fps,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        instance_id=name.replace("-", "_"),
    )
    assert clauses
    output = tmp_path / f"{name}.raw"
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        _pattern_source(rate=source_rate or fps),
        "-filter_complex",
        ";".join(clauses),
        "-map",
        "[k4out]",
        "-frames:v",
        str(frames),
        "-pix_fmt",
        "rgba",
        "-f",
        "rawvideo",
        str(output),
    ]
    result = ProcessRunner().run(command, timeout_seconds=30.0)
    assert result.returncode == 0, result.stderr
    return output.read_bytes()


@pytest.mark.integration
def test_k4_real_ffmpeg_capability_probe_proves_alpha_branch_and_overlay() -> None:
    ffmpeg = _require_ffmpeg()
    capabilities = AdvancedFFmpegCapabilityProbe(
        resolver=lambda: ToolResolution(
            name="ffmpeg",
            path=ffmpeg,
            source="integration",
        )
    ).probe()

    assert capabilities.available
    assert capabilities.supports(AdvancedFFmpegFeature.ALPHA_BRANCH)
    assert capabilities.supports(AdvancedFFmpegFeature.OVERLAY_EXPRESSIONS)


@pytest.mark.integration
def test_k4_runtime_shadow_glow_match_static_reference_frame_by_frame(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    dynamic_assignment = _assignment(
        shadow=(0.0, 1.0),
        glow=(0.0, 1.0),
    )
    dynamic = _render_k4_raw(
        tmp_path,
        ffmpeg=ffmpeg,
        name="k4-dynamic",
        assignment=dynamic_assignment,
        fps=4,
        frames=4,
    )
    frame_size = 32 * 32 * 4
    assert len(dynamic) == frame_size * 4

    for frame_index in range(4):
        intensity = frame_index / 4.0
        static_assignment = _assignment(
            shadow=(intensity, None),
            glow=(intensity, None),
        )
        reference = _render_k4_raw(
            tmp_path,
            ffmpeg=ffmpeg,
            name=f"k4-reference-{frame_index}",
            assignment=static_assignment,
            fps=1,
            frames=1,
            source_rate=1,
        )
        actual = dynamic[
            frame_index * frame_size : (frame_index + 1) * frame_size
        ]
        assert actual == reference


@pytest.mark.integration
@pytest.mark.parametrize(
    ("kind", "expected_rgb"),
    [
        ("shadow", (0, 0, 0)),
        ("glow", (255, 255, 255)),
    ],
)
def test_k4_transparent_edge_branch_keeps_pure_effect_color(
    tmp_path: Path,
    kind: str,
    expected_rgb: tuple[int, int, int],
) -> None:
    ffmpeg = _require_ffmpeg()
    assignment = (
        _assignment(shadow=(0.5, None))
        if kind == "shadow"
        else _assignment(glow=(0.5, None))
    )
    raw = _render_k4_raw(
        tmp_path,
        ffmpeg=ffmpeg,
        name=f"k4-{kind}-golden",
        assignment=assignment,
        fps=1,
        frames=1,
        source_rate=1,
    )

    effect_pixels: list[tuple[int, int, int, int]] = []
    for y in range(32):
        for x in range(32):
            if 10 <= x < 18 and 10 <= y < 18:
                continue
            index = (y * 32 + x) * 4
            pixel = tuple(raw[index : index + 4])
            if pixel[3] > 0:
                effect_pixels.append(pixel)  # type: ignore[arg-type]

    assert effect_pixels
    for red, green, blue, _alpha in effect_pixels:
        assert (red, green, blue) == expected_rgb


@pytest.mark.integration
def test_k4_advanced_project_completes_real_render_and_selection(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        pytest.skip("ffprobe not available")

    asset = tmp_path / "k4-app.ppm"
    _write_ppm(asset, width=160, height=90)
    project = _project(asset)

    output = tmp_path / "k4-shadow-glow.mp4"
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

    selection = tmp_path / "k4-selection.mp4"
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
def test_k4_shadow_glow_reference_resolution_and_60fps_smoke(
    width: int,
    height: int,
    fps: int,
) -> None:
    ffmpeg = _require_ffmpeg()
    assignment = _assignment(
        shadow=(0.25, None),
        glow=(0.25, None),
    )
    clauses = compile_k4_shadow_glow_clauses(
        "0:v",
        "k4out",
        assignment,
        duration_seconds=0.12,
        fps=fps,
        canvas_width=width,
        canvas_height=height,
        instance_id=f"k4_smoke_{width}_{height}_{fps}",
    )
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
            "-filter_complex",
            ";".join(clauses),
            "-map",
            "[k4out]",
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
    result = runner.run(command, timeout_seconds=40.0)
    elapsed = time.perf_counter() - started
    assert result.returncode == 0, result.stderr
    return elapsed


@pytest.mark.integration
def test_k4_blur_shadow_glow_performance_is_within_8x_baseline() -> None:
    ffmpeg = _require_ffmpeg()
    runner = ProcessRunner()
    source = "color=c=red:s=640x360:r=30:d=1.0"
    assignment = _assignment(
        blur=(0.25, None),
        shadow=(0.35, None),
        glow=(0.35, None),
    )

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

    blur_filters = compile_k3_blur_filters(
        assignment,
        duration_seconds=1.0,
        fps=30,
        canvas_width=640,
        canvas_height=360,
        instance_id="k4_perf_blur",
    )
    k4_clauses = compile_k4_shadow_glow_clauses(
        "k4blurred",
        "k4out",
        assignment,
        duration_seconds=1.0,
        fps=30,
        canvas_width=640,
        canvas_height=360,
        instance_id="k4_perf",
    )
    graph = ";".join(
        (
            "[0:v]" + ",".join(blur_filters) + "[k4blurred]",
            *k4_clauses,
        )
    )
    advanced = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        source,
        "-filter_complex",
        graph,
        "-map",
        "[k4out]",
        "-f",
        "null",
        "-",
    ]

    _timed_run(runner, base)
    _timed_run(runner, advanced)
    baseline_times = [_timed_run(runner, base) for _ in range(3)]
    heavy_times = [_timed_run(runner, advanced) for _ in range(3)]

    baseline = statistics.median(baseline_times)
    heavy = statistics.median(heavy_times)
    assert baseline > 0
    assert heavy / baseline <= 8.0
