from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aavc.animation import evaluate_advanced_keyframe_track
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
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan
from aavc.rendering.advanced_filters import compile_k1_opacity_filters


def _write_ppm(
    path: Path,
    *,
    width: int,
    height: int,
    rgb: tuple[int, int, int] = (240, 32, 32),
) -> None:
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + bytes(rgb) * (width * height))


def _bezier_track(
    property_name: str,
    start: float,
    end: float,
    *,
    velocity0: float = 0.0,
    velocity1: float = 2.0,
    overshoot: float = 0.20,
) -> AnimationKeyframeTrack:
    return AnimationKeyframeTrack(
        property_name=property_name,  # type: ignore[arg-type]
        keyframes=(
            AnimationKeyframe(
                time=0.0,
                value=start,
                interpolation="bezier",
                easing="ease_in_out",
                velocity=velocity0,
                overshoot=overshoot,
            ),
            AnimationKeyframe(
                time=1.0,
                value=end,
                velocity=velocity1,
            ),
        ),
    )


def _assignment() -> AnimationAssignment:
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        intensity=0.0,
        keyframe_tracks=(
            _bezier_track("position_x", -0.03, 0.05),
            _bezier_track("position_y", -0.02, 0.03),
            _bezier_track("scale", 0.95, 1.15),
            _bezier_track("rotation_degrees", -6.0, 8.0),
            _bezier_track("opacity", 0.30, 1.00),
            _bezier_track("crop_left", 0.02, 0.10, overshoot=0.10),
            _bezier_track("blur", 0.02, 0.12, overshoot=0.05),
            _bezier_track("shadow", 0.02, 0.10, overshoot=0.05),
            _bezier_track("glow", 0.02, 0.08, overshoot=0.05),
            _bezier_track("mask_progress", 0.30, 1.00, overshoot=0.15),
        ),
    )


def _project(asset: Path) -> ProjectState:
    return ProjectState(
        schema_version=4,
        title="K6 Bezier integration",
        source_docx="synthetic-k6.docx",
        asset_directory=str(asset.parent),
        scenes=(
            Scene(
                scene_number=1,
                asset_ids=("A001",),
                source_quotes=("K6 Bezier",),
                duration_seconds=1.0,
            ),
        ),
        bindings=(
            AssetBinding(
                asset_id="A001",
                source_quote="K6 Bezier",
                path=str(asset),
                status="READY",
            ),
        ),
        fps=12,
        width=320,
        height=180,
        animations=(_assignment(),),
        render_quality=RenderQualitySettings(
            preset_name="K6 Fast",
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


@pytest.mark.integration
def test_k6_real_ffmpeg_opacity_bezier_matches_canonical_evaluator(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    track = _bezier_track(
        "opacity",
        0.0,
        1.0,
        velocity0=0.0,
        velocity1=4.0,
        overshoot=0.25,
    )
    assignment = AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        intensity=0.0,
        keyframe_tracks=(track,),
    )
    filters = compile_k1_opacity_filters(
        assignment,
        duration_seconds=1.0,
        instance_id="k6_opacity",
    )
    assert filters

    output = tmp_path / "k6-opacity.raw"
    result = ProcessRunner().run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=1x1:r=4:d=1,format=rgba",
            "-vf",
            ",".join((*filters, "alphaextract")),
            "-frames:v",
            "4",
            "-pix_fmt",
            "gray",
            "-f",
            "rawvideo",
            str(output),
        ],
        timeout_seconds=30.0,
    )
    assert result.returncode == 0, result.stderr

    raw = output.read_bytes()
    assert len(raw) == 4
    for frame_index, alpha in enumerate(raw):
        expected = evaluate_advanced_keyframe_track(track, frame_index / 4.0)
        assert abs((alpha / 255.0) - expected) <= (1.0 / 255.0) + 1e-9


@pytest.mark.integration
def test_k6_all_property_bezier_project_renders_full_and_selection(
    tmp_path: Path,
) -> None:
    ffmpeg = _require_ffmpeg()
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        pytest.skip("ffprobe not available")

    asset = tmp_path / "k6-app.ppm"
    _write_ppm(asset, width=160, height=90)
    project = _project(asset)
    plan = build_render_plan(project, tmp_path / "planned.mp4")
    report = validate_render_plan(plan)
    graph = build_ffmpeg_command(plan, ffmpeg=ffmpeg)
    filter_graph = graph[graph.index("-filter_complex") + 1]

    assert report.ok
    assert "sin(3.141592654" in filter_graph
    assert "colorchannelmixer@opacity_0_0" in filter_graph
    assert "drawbox@crop_opacity_0_0_left" in filter_graph
    assert "gblur@blur_opacity_0_0" in filter_graph
    assert "drawbox@mask_opacity_0_0" in filter_graph
    assert "k4_opacity_0_0" in filter_graph

    output = tmp_path / "k6-bezier.mp4"
    options = ExportOptions(
        output_path=str(output),
        video_codec="libx264",
        encoder_preset="ultrafast",
        crf=30,
        width=320,
        height=180,
        fps=12,
        sharpen_amount=0.0,
        burn_subtitles=False,
    )
    result = render_project(
        project,
        options,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    assert Path(result.output_path).is_file()
    assert Path(result.output_path).stat().st_size > 500

    selection = tmp_path / "k6-selection.mp4"
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
