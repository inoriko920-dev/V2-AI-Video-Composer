from __future__ import annotations

import shutil
import statistics
import time
from pathlib import Path

import pytest

from aavc.animation import blur_sigma_limit
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
from aavc.rendering.advanced_filters import (
    compile_k2_crop_filters,
    compile_k3_blur_filters,
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


def _blur_track(
    start: float = 0.0,
    end: float = 0.5,
) -> AnimationKeyframeTrack:
    return AnimationKeyframeTrack(
        property_name="blur",
        keyframes=(
            AnimationKeyframe(time=0.0, value=start),
            AnimationKeyframe(time=1.0, value=end),
        ),
    )


def _constant_track(property_name: str, value: float) -> AnimationKeyframeTrack:
    return AnimationKeyframeTrack(
        property_name=property_name,  # type: ignore[arg-type]
        keyframes=(AnimationKeyframe(time=0.0, value=value),),
    )


def _assignment(
    *,
    tracks: tuple[AnimationKeyframeTrack, ...] | None = None,
) -> AnimationAssignment:
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        intensity=0.0,
        keyframe_tracks=tracks or (_blur_track(),),
    )


def _project(asset: Path) -> ProjectState:
    return ProjectState(
        schema_version=4,
        title="K3 blur integration",
        source_docx="synthetic-k3.docx",
        asset_directory=str(asset.parent),
        scenes=(
            Scene(
                scene_number=1,
                asset_ids=("A001",),
                source_quotes=("K3 blur",),
                duration_seconds=1.0,
            ),
        ),
        bindings=(
            AssetBinding(
                asset_id="A001",
                source_quote="K3 blur",
                path=str(asset),
                status="READY",
            ),
        ),
        fps=12,
        width=320,
        height=180,
        animations=(_assignment(),),
        render_quality=RenderQualitySettings(
            preset_name="K3 Fast",
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
        "drawbox=x=12:y=12:w=8:h=8:color=red@1:t=fill:replace=1"
    )


def _render_raw(
    tmp_path: Path,
    *,
    ffmpeg: str,
    name: str,
    source: str,
    filters: str,
    frames: int,
) -> bytes:
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
        source,
        "-vf",
        filters,
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
def test_k3_runtime_blur_matches_static_reference_frame_by_frame(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    assignment = _assignment(tracks=(_blur_track(0.0, 1.0),))
    filters = compile_k3_blur_filters(
        assignment,
        duration_seconds=1.0,
        fps=4,
        canvas_width=320,
        canvas_height=180,
        instance_id="k3_parity",
    )
    dynamic = _render_raw(
        tmp_path,
        ffmpeg=ffmpeg,
        name="dynamic",
        source=_pattern_source(),
        filters=",".join(filters),
        frames=4,
    )

    frame_size = 32 * 32 * 4
    assert len(dynamic) == frame_size * 4
    sigma_limit = blur_sigma_limit(320, 180)
    expected_sigmas = tuple(
        round((frame_index / 4.0) * sigma_limit, 2)
        for frame_index in range(4)
    )

    for frame_index, sigma in enumerate(expected_sigmas):
        reference = _render_raw(
            tmp_path,
            ffmpeg=ffmpeg,
            name=f"reference-{frame_index}",
            source=_pattern_source(rate=1, duration=1.0),
            filters=(
                "format=rgba,"
                "premultiply=inplace=1,"
                f"gblur=sigma={sigma:.2f}:sigmaV={sigma:.2f}:steps=2,"
                "unpremultiply=inplace=1"
            ),
            frames=1,
        )
        actual = dynamic[
            frame_index * frame_size : (frame_index + 1) * frame_size
        ]
        assert actual == reference


@pytest.mark.integration
def test_k3_premultiply_path_prevents_dark_transparent_edge_fringe(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    assignment = _assignment(tracks=(_constant_track("blur", 0.5),))
    filters = compile_k3_blur_filters(
        assignment,
        duration_seconds=1.0,
        fps=1,
        canvas_width=320,
        canvas_height=180,
        instance_id="k3_alpha",
    )
    raw = _render_raw(
        tmp_path,
        ffmpeg=ffmpeg,
        name="transparent-edge",
        source=_pattern_source(rate=1, duration=1.0),
        filters=",".join(filters),
        frames=1,
    )

    pixels = tuple(
        tuple(raw[index : index + 4])
        for index in range(0, len(raw), 4)
    )
    visible = [pixel for pixel in pixels if pixel[3] > 0]
    assert visible

    # Judge the edge after compositing on white. Very low-alpha pixels can
    # have noisy unpremultiplied RGB in 8-bit FFmpeg, while remaining visually
    # correct after alpha composition. A dark fringe would show up here.
    for red, green, blue, alpha in visible:
        actual = (
            round((red * alpha + 255 * (255 - alpha)) / 255.0),
            round((green * alpha + 255 * (255 - alpha)) / 255.0),
            round((blue * alpha + 255 * (255 - alpha)) / 255.0),
        )
        ideal = (255, 255 - alpha, 255 - alpha)
        assert max(
            abs(channel - expected)
            for channel, expected in zip(actual, ideal, strict=True)
        ) <= 1


@pytest.mark.integration
def test_k3_crop_blur_reapplies_hard_crop_boundary(tmp_path: Path) -> None:
    ffmpeg = _require_ffmpeg()
    assignment = _assignment(
        tracks=(
            _constant_track("crop_left", 0.25),
            _constant_track("crop_right", 0.25),
            _constant_track("blur", 0.5),
        )
    )
    pre_crop = compile_k2_crop_filters(
        assignment,
        duration_seconds=1.0,
        instance_id="k3_crop_pre",
    )
    blur = compile_k3_blur_filters(
        assignment,
        duration_seconds=1.0,
        fps=1,
        canvas_width=320,
        canvas_height=180,
        instance_id="k3_crop_blur",
    )
    post_crop = compile_k2_crop_filters(
        assignment,
        duration_seconds=1.0,
        instance_id="k3_crop_post",
    )
    raw = _render_raw(
        tmp_path,
        ffmpeg=ffmpeg,
        name="crop-blur",
        source="color=c=red:s=32x32:r=1:d=1,format=rgba",
        filters=",".join((*pre_crop, *blur, *post_crop)),
        frames=1,
    )

    for y in range(32):
        for x in range(32):
            alpha = raw[(y * 32 + x) * 4 + 3]
            if x < 8 or x >= 24:
                assert alpha == 0
    center_alpha = raw[(16 * 32 + 16) * 4 + 3]
    assert center_alpha > 0


@pytest.mark.integration
def test_k3_advanced_project_completes_real_render_and_selection(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        pytest.skip("ffprobe not available")

    asset = tmp_path / "k3-app.ppm"
    _write_ppm(asset, width=160, height=90)
    project = _project(asset)

    output = tmp_path / "k3-blur.mp4"
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

    selection = tmp_path / "k3-selection.mp4"
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
def test_k3_blur_reference_resolution_and_60fps_smoke(
    width: int,
    height: int,
    fps: int,
) -> None:
    ffmpeg = _require_ffmpeg()
    assignment = _assignment(tracks=(_constant_track("blur", 0.25),))
    filters = compile_k3_blur_filters(
        assignment,
        duration_seconds=0.12,
        fps=fps,
        canvas_width=width,
        canvas_height=height,
        instance_id=f"k3_smoke_{width}_{height}_{fps}",
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
            "-vf",
            ",".join(filters),
            "-frames:v",
            "2",
            "-f",
            "null",
            "-",
        ],
        timeout_seconds=45.0,
    )
    assert result.returncode == 0, result.stderr


def _timed_run(runner: ProcessRunner, command: list[str]) -> float:
    started = time.perf_counter()
    result = runner.run(command, timeout_seconds=30.0)
    elapsed = time.perf_counter() - started
    assert result.returncode == 0, result.stderr
    return elapsed


@pytest.mark.integration
def test_k3_blur_performance_is_within_4x_baseline() -> None:
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
    filters = compile_k3_blur_filters(
        _assignment(tracks=(_blur_track(0.0, 0.5),)),
        duration_seconds=1.0,
        fps=30,
        canvas_width=640,
        canvas_height=360,
        instance_id="k3_perf",
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
        "-vf",
        ",".join(filters),
        "-f",
        "null",
        "-",
    ]

    _timed_run(runner, base)
    _timed_run(runner, advanced)
    baseline_times = [_timed_run(runner, base) for _ in range(3)]
    blur_times = [_timed_run(runner, advanced) for _ in range(3)]

    baseline = statistics.median(baseline_times)
    blur = statistics.median(blur_times)
    assert baseline > 0
    assert blur / baseline <= 4.0
