from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation import evaluate_keyframe_track, keyframe_track_support_reason
from aavc.animation.compiler import compile_keyframe_value_expression
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.motion_preview import (
    native_motion_preview_offset,
    native_visual_preview_rotation,
    native_visual_preview_scale,
)
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="wave-e-keyframe-motion",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _track(
    property_name: str,
    start: float,
    end: float,
    *,
    interpolation: str = "linear",
    easing: str = "linear",
) -> AnimationKeyframeTrack:
    return AnimationKeyframeTrack(
        property_name=property_name,  # type: ignore[arg-type]
        keyframes=(
            AnimationKeyframe(
                time=0.0,
                value=start,
                interpolation=interpolation,  # type: ignore[arg-type]
                easing=easing,  # type: ignore[arg-type]
            ),
            AnimationKeyframe(time=1.0, value=end),
        ),
    )


def _filter_graph(command: list[str]) -> str:
    return command[command.index("-filter_complex") + 1]


def test_foundational_keyframe_evaluator_interpolates_and_clamps() -> None:
    x_track = _track("position_x", -0.20, 0.20)
    scale_track = _track("scale", 0.20, 2.00)

    assert evaluate_keyframe_track(x_track, 0.0) == pytest.approx(-0.10)
    assert evaluate_keyframe_track(x_track, 0.5) == pytest.approx(0.0)
    assert evaluate_keyframe_track(x_track, 1.0) == pytest.approx(0.10)

    assert evaluate_keyframe_track(scale_track, 0.0) == pytest.approx(0.75)
    assert evaluate_keyframe_track(scale_track, 0.5) == pytest.approx(1.10)
    assert evaluate_keyframe_track(scale_track, 1.0) == pytest.approx(1.50)


def test_hold_interpolation_switches_at_next_keyframe() -> None:
    track = _track("rotation_degrees", -10.0, 20.0, interpolation="hold")

    assert evaluate_keyframe_track(track, 0.5) == pytest.approx(-10.0)
    assert evaluate_keyframe_track(track, 1.0) == pytest.approx(20.0)


def test_ease_in_out_matches_preview_midpoint() -> None:
    track = _track("position_y", -0.08, 0.08, easing="ease_in_out")

    assert evaluate_keyframe_track(track, 0.25) == pytest.approx(-0.06)
    assert evaluate_keyframe_track(track, 0.50) == pytest.approx(0.0)
    assert evaluate_keyframe_track(track, 0.75) == pytest.approx(0.06)


def test_preview_applies_keyframes_even_when_legacy_intensity_is_zero() -> None:
    assignment = AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        enter_effect="Fade",
        exit_effect="Fade",
        intensity=0.0,
        keyframe_tracks=(
            _track("position_x", 0.0, 0.08),
            _track("position_y", -0.04, 0.04),
            _track("scale", 1.0, 1.4),
            _track("rotation_degrees", -10.0, 20.0),
        ),
    )

    offset = native_motion_preview_offset(
        assignment,
        time_seconds=1.0,
        duration_seconds=2.0,
    )
    assert offset.x == pytest.approx(0.04)
    assert offset.y == pytest.approx(0.0)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=1.0,
        duration_seconds=2.0,
    ) == pytest.approx(1.2)
    assert native_visual_preview_rotation(
        assignment,
        time_seconds=1.0,
        duration_seconds=2.0,
    ) == pytest.approx(5.0)


def test_ffmpeg_compiler_activates_foundational_keyframes(tmp_path: Path) -> None:
    project = _project()
    scene = project.scenes[0]
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
        keyframe_tracks=(
            _track("position_x", 0.0, 0.08, easing="ease_out"),
            _track("position_y", -0.04, 0.04),
            _track("scale", 1.0, 1.4),
            _track("rotation_degrees", -10.0, 20.0),
        ),
    )
    project = replace(project, animations=(assignment,))

    command = build_ffmpeg_command(
        build_render_plan(project, tmp_path / "out.mp4")
    )
    graph = _filter_graph(command)

    assert "eval=frame" in graph
    assert "rotate=a='" in graph
    assert "*0.017453293" in graph
    assert "overlay=x='" in graph
    assert "W*(min(0.100000,max(-0.100000" in graph
    assert "H*(min(0.100000,max(-0.100000" in graph
    assert "fade=t=in:st=0:d=0.250000:alpha=1" not in graph

    report = validate_render_plan(build_render_plan(project, tmp_path / "out.mp4"))
    assert not any(
        issue.code == "KEYFRAME_TRACK_FALLBACK" for issue in report.issues
    )


def test_legacy_motion_and_keyframe_motion_are_additive() -> None:
    assignment = AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        enter_effect="Pan",
        exit_effect="Fade",
        intensity=1.0,
        keyframe_tracks=(_track("position_x", 0.0, 0.08),),
    )

    start = native_motion_preview_offset(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    )
    midpoint = native_motion_preview_offset(
        assignment,
        time_seconds=1.0,
        duration_seconds=2.0,
    )

    assert start.x == pytest.approx(0.06)
    assert midpoint.x == pytest.approx(0.04)


def test_unsupported_keyframe_property_warns_and_is_ignored(tmp_path: Path) -> None:
    project = _project()
    scene = project.scenes[0]
    baseline_assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
    )
    unsupported = replace(
        baseline_assignment,
        keyframe_tracks=(_track("opacity", 0.0, 1.0),),
    )

    baseline = replace(project, animations=(baseline_assignment,))
    candidate = replace(project, animations=(unsupported,))
    baseline_graph = _filter_graph(
        build_ffmpeg_command(build_render_plan(baseline, tmp_path / "base.mp4"))
    )
    candidate_plan = build_render_plan(candidate, tmp_path / "candidate.mp4")
    candidate_graph = _filter_graph(build_ffmpeg_command(candidate_plan))

    assert candidate_graph == baseline_graph
    reasons = [
        issue.message
        for issue in validate_render_plan(candidate_plan).issues
        if issue.code == "KEYFRAME_TRACK_FALLBACK"
    ]
    assert any("opacity" in message and "belum aktif" in message for message in reasons)


def test_bezier_velocity_overshoot_remain_fail_soft_in_wave_e(tmp_path: Path) -> None:
    project = _project()
    scene = project.scenes[0]
    track = AnimationKeyframeTrack(
        property_name="position_x",
        keyframes=(
            AnimationKeyframe(
                time=0.0,
                value=0.0,
                interpolation="bezier",
                velocity=0.5,
                overshoot=0.1,
            ),
            AnimationKeyframe(time=1.0, value=0.08),
        ),
    )
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
        keyframe_tracks=(track,),
    )
    project = replace(project, animations=(assignment,))
    plan = build_render_plan(project, tmp_path / "out.mp4")

    assert keyframe_track_support_reason(track) is not None
    assert compile_keyframe_value_expression(
        assignment,
        "position_x",
        duration_seconds=scene.duration_seconds,
    ) is None
    report = validate_render_plan(plan)
    assert any(issue.code == "KEYFRAME_TRACK_FALLBACK" for issue in report.issues)
