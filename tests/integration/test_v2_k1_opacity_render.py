from __future__ import annotations

import shutil
import statistics
import time
from pathlib import Path

import pytest

from aavc.animation import evaluate_advanced_keyframe_track
from aavc.animation.contract import (
    ADVANCED_KEYFRAME_CONTRACT,
    ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY,
)
from aavc.application.services.export_service import ExportOptions
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
from aavc.rendering import (
    build_ffmpeg_command,
    build_render_plan,
    execute_ffmpeg,
    validate_render_plan,
)
from aavc.rendering.advanced_capabilities import (
    AdvancedFFmpegCapabilityProbe,
    AdvancedFFmpegFeature,
)
from aavc.rendering.advanced_filters import compile_k1_opacity_filters


def _write_ppm(path: Path, rgb: tuple[int, int, int] = (240, 32, 32)) -> None:
    path.write_bytes(b"P6\n1 1\n255\n" + bytes(rgb))


def _write_pam_rgba(
    path: Path,
    rgba: tuple[int, int, int, int] = (240, 32, 32, 128),
) -> None:
    header = (
        "P7\n"
        "WIDTH 1\n"
        "HEIGHT 1\n"
        "DEPTH 4\n"
        "MAXVAL 255\n"
        "TUPLTYPE RGB_ALPHA\n"
        "ENDHDR\n"
    ).encode("ascii")
    path.write_bytes(header + bytes(rgba))


def _opacity_track() -> AnimationKeyframeTrack:
    return AnimationKeyframeTrack(
        property_name="opacity",
        keyframes=(
            AnimationKeyframe(time=0.0, value=0.0, easing="linear"),
            AnimationKeyframe(time=1.0, value=1.0),
        ),
    )


def _project(asset: Path) -> ProjectState:
    track = _opacity_track()
    return ProjectState(
        schema_version=4,
        title="K1 opacity integration",
        source_docx="synthetic-k1.docx",
        asset_directory=str(asset.parent),
        scenes=(
            Scene(
                scene_number=1,
                asset_ids=("A001",),
                source_quotes=("K1 opacity",),
                duration_seconds=1.0,
            ),
        ),
        bindings=(
            AssetBinding(
                asset_id="A001",
                source_quote="K1 opacity",
                path=str(asset),
                status="READY",
            ),
        ),
        fps=12,
        width=320,
        height=180,
        animations=(
            AnimationAssignment(
                scene_number=1,
                asset_id="A001",
                intensity=0.0,
                keyframe_tracks=(track,),
            ),
        ),
        render_quality=RenderQualitySettings(
            preset_name="K1 Fast",
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


def _alpha_samples(
    tmp_path: Path,
    *,
    ffmpeg: str,
    asset: Path,
    source_alpha: int,
) -> tuple[float, ...]:
    track = _opacity_track()
    assignment = AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        intensity=0.0,
        keyframe_tracks=(track,),
    )
    filters = compile_k1_opacity_filters(
        assignment,
        duration_seconds=1.0,
        instance_id="k1_alpha_probe",
    )
    output = tmp_path / f"{asset.stem}-alpha.raw"
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
        ",".join((*filters, "alphaextract")),
        "-t",
        "1.0",
        "-an",
        "-pix_fmt",
        "gray",
        "-f",
        "rawvideo",
        str(output),
    ]
    result = ProcessRunner().run(command, timeout_seconds=20.0)
    assert result.returncode == 0, result.stderr
    raw = output.read_bytes()
    assert len(raw) >= 4

    actual = tuple(value / 255.0 for value in raw[:4])
    expected = tuple(
        (source_alpha / 255.0)
        * evaluate_advanced_keyframe_track(track, index / 4.0)
        for index in range(4)
    )
    for got, want in zip(actual, expected, strict=True):
        assert abs(got - want) <= (1.0 / 255.0) + 1e-9
    return actual


@pytest.mark.integration
def test_k1_runtime_opacity_capability_probe_passes_on_real_ffmpeg() -> None:
    ffmpeg = _require_ffmpeg()
    probe = AdvancedFFmpegCapabilityProbe(
        resolver=lambda: ToolResolution(
            name="ffmpeg",
            path=ffmpeg,
            source="integration",
        )
    )

    capabilities = probe.probe()

    assert capabilities.available
    assert capabilities.supports(AdvancedFFmpegFeature.OPACITY_RUNTIME_ALPHA)


@pytest.mark.integration
def test_k1_real_ffmpeg_opacity_preserves_rgb_and_rgba_source_alpha(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    rgb = tmp_path / "rgb.ppm"
    rgba = tmp_path / "rgba.pam"
    _write_ppm(rgb)
    _write_pam_rgba(rgba)

    rgb_samples = _alpha_samples(
        tmp_path,
        ffmpeg=ffmpeg,
        asset=rgb,
        source_alpha=255,
    )
    rgba_samples = _alpha_samples(
        tmp_path,
        ffmpeg=ffmpeg,
        asset=rgba,
        source_alpha=128,
    )

    assert rgb_samples[-1] > rgba_samples[-1]


@pytest.mark.integration
def test_k1_advanced_project_completes_real_app_render_and_selection(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        pytest.skip("ffprobe not available")
    asset = tmp_path / "app.ppm"
    _write_ppm(asset)
    project = _project(asset)

    output = tmp_path / "k1-opacity.mp4"
    plan = build_render_plan(project, output)
    report = validate_render_plan(plan)
    assert report.ok

    result = execute_ffmpeg(
        build_ffmpeg_command(plan, ffmpeg=ffmpeg),
        expected_duration_seconds=plan.duration_seconds,
    )
    assert Path(result.output_path).is_file()
    assert Path(result.output_path).stat().st_size > 500

    selection = tmp_path / "k1-selection.mp4"
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


def _timed_run(runner: ProcessRunner, command: list[str]) -> float:
    started = time.perf_counter()
    result = runner.run(command, timeout_seconds=20.0)
    elapsed = time.perf_counter() - started
    assert result.returncode == 0, result.stderr
    return elapsed


@pytest.mark.integration
def test_k1_opacity_performance_is_within_2_5x_baseline() -> None:
    ffmpeg = _require_ffmpeg()
    runner = ProcessRunner()
    source = "color=c=red:s=640x360:r=30:d=1.5"
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
        (
            "format=rgba,"
            "sendcmd=c='0-1.5 [expr] "
            "colorchannelmixer@k1_perf aa TI',"
            "colorchannelmixer@k1_perf=aa=0"
        ),
        "-f",
        "null",
        "-",
    ]

    _timed_run(runner, base)
    _timed_run(runner, advanced)
    baseline_times = [_timed_run(runner, base) for _ in range(3)]
    opacity_times = [_timed_run(runner, advanced) for _ in range(3)]

    baseline = statistics.median(baseline_times)
    opacity = statistics.median(opacity_times)
    assert baseline > 0
    assert opacity / baseline <= 2.5
