from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation import (
    advanced_keyframe_track_support_reason,
    evaluate_advanced_keyframe_track,
    keyframe_parameter_clamps,
    keyframe_parameter_mismatches,
    keyframe_track_support_reason,
)
from aavc.animation.compiler import compile_keyframe_value_expression
from aavc.animation.contract import (
    ADVANCED_KEYFRAME_CONTRACT,
    ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY,
)
from aavc.application.services.validation import validate_project
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
        title="k6-bezier",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _bezier_track(
    property_name: str = "opacity",
    *,
    start: float = 0.0,
    end: float = 1.0,
    velocity0: float | None = 1.0,
    velocity1: float | None = 1.0,
    overshoot: float | None = 0.0,
    easing: str = "linear",
) -> AnimationKeyframeTrack:
    return AnimationKeyframeTrack(
        property_name=property_name,  # type: ignore[arg-type]
        keyframes=(
            AnimationKeyframe(
                time=0.0,
                value=start,
                interpolation="bezier",
                easing=easing,  # type: ignore[arg-type]
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


def _advanced_project(tracks: tuple[AnimationKeyframeTrack, ...]):
    project = _project()
    scene = project.scenes[0]
    metadata = dict(project.metadata)
    metadata[ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY] = ADVANCED_KEYFRAME_CONTRACT
    return replace(
        project,
        schema_version=4,
        metadata=metadata,
        animations=(
            AnimationAssignment(
                scene_number=scene.scene_number,
                asset_id=scene.asset_ids[0],
                intensity=0.0,
                keyframe_tracks=tracks,
            ),
        ),
    )


def _filter_graph(command: list[str]) -> str:
    return command[command.index("-filter_complex") + 1]


@pytest.mark.parametrize(
    ("velocity", "expected"),
    [
        (0.0, (0.15625, 0.5, 0.84375)),
        (1.0, (0.25, 0.5, 0.75)),
        (4.0, (0.53125, 0.5, 0.46875)),
    ],
)
def test_k6_velocity_controls_bezier_tangent(
    velocity: float,
    expected: tuple[float, float, float],
) -> None:
    track = _bezier_track(
        velocity0=velocity,
        velocity1=velocity,
    )

    assert evaluate_advanced_keyframe_track(track, 0.25) == pytest.approx(expected[0])
    assert evaluate_advanced_keyframe_track(track, 0.50) == pytest.approx(expected[1])
    assert evaluate_advanced_keyframe_track(track, 0.75) == pytest.approx(expected[2])


@pytest.mark.parametrize(
    ("overshoot", "expected_midpoint"),
    [
        (0.0, 0.5),
        (0.25, 0.625),
        (0.50, 0.75),
    ],
)
def test_k6_overshoot_matches_locked_formula(
    overshoot: float,
    expected_midpoint: float,
) -> None:
    track = _bezier_track(
        property_name="shadow",
        overshoot=overshoot,
    )

    assert evaluate_advanced_keyframe_track(track, 0.0) == pytest.approx(0.0)
    assert evaluate_advanced_keyframe_track(track, 0.5) == pytest.approx(
        expected_midpoint
    )
    assert evaluate_advanced_keyframe_track(track, 1.0) == pytest.approx(1.0)


def test_k6_overshoot_is_zero_at_endpoints_and_final_value_is_clamped() -> None:
    track = _bezier_track(
        property_name="opacity",
        overshoot=0.50,
    )

    assert evaluate_advanced_keyframe_track(track, 0.0) == pytest.approx(0.0)
    assert evaluate_advanced_keyframe_track(track, 0.75) == pytest.approx(1.0)
    assert evaluate_advanced_keyframe_track(track, 1.0) == pytest.approx(1.0)


def test_k6_velocity_and_overshoot_are_hard_clamped() -> None:
    track = _bezier_track(
        property_name="shadow",
        velocity0=-3.0,
        velocity1=9.0,
        overshoot=1.0,
    )

    assert keyframe_parameter_clamps(track) == (
        "velocity keyframe 1 di-clamp ke rentang 0–4",
        "overshoot keyframe 1 di-clamp ke rentang 0–0,50",
        "velocity keyframe 2 di-clamp ke rentang 0–4",
    )
    # Endpoint exactness survives clamping.
    assert evaluate_advanced_keyframe_track(track, 0.0) == pytest.approx(0.0)
    assert evaluate_advanced_keyframe_track(track, 1.0) == pytest.approx(1.0)


def test_k6_parameter_mismatch_warns_but_linear_math_is_not_reinterpreted() -> None:
    track = AnimationKeyframeTrack(
        property_name="opacity",
        keyframes=(
            AnimationKeyframe(
                time=0.0,
                value=0.0,
                interpolation="linear",
                velocity=2.0,
                overshoot=0.25,
            ),
            AnimationKeyframe(time=1.0, value=1.0),
        ),
    )

    mismatches = keyframe_parameter_mismatches(track)

    assert len(mismatches) == 2
    assert any("velocity" in item for item in mismatches)
    assert any("overshoot" in item for item in mismatches)
    assert evaluate_advanced_keyframe_track(track, 0.5) == pytest.approx(0.5)


def test_k6_end_velocity_is_valid_as_incoming_bezier_tangent() -> None:
    track = _bezier_track(
        velocity0=1.0,
        velocity1=3.0,
    )

    assert not keyframe_parameter_mismatches(track)


def test_k6_legacy_support_stays_blocked_while_advanced_support_is_green() -> None:
    track = _bezier_track(property_name="position_x", end=0.08)

    assert keyframe_track_support_reason(track) is not None
    assert advanced_keyframe_track_support_reason(track) is None


def test_k6_foundational_preview_uses_bezier_only_for_advanced_contract() -> None:
    project = _advanced_project(
        (
            _bezier_track(
                "position_x",
                end=0.08,
                velocity0=0.0,
                velocity1=0.0,
            ),
            _bezier_track(
                "scale",
                start=1.0,
                end=1.4,
                velocity0=0.0,
                velocity1=0.0,
            ),
            _bezier_track(
                "rotation_degrees",
                start=0.0,
                end=20.0,
                velocity0=0.0,
                velocity1=0.0,
            ),
        )
    )
    assignment = project.animations[0]

    legacy_offset = native_motion_preview_offset(
        assignment,
        time_seconds=0.5,
        duration_seconds=2.0,
        animation_keyframe_contract="legacy-v3",
    )
    advanced_offset = native_motion_preview_offset(
        assignment,
        time_seconds=0.5,
        duration_seconds=2.0,
        animation_keyframe_contract="advanced-v1",
    )

    assert legacy_offset.x == pytest.approx(0.0)
    assert advanced_offset.x == pytest.approx(0.08 * 0.15625)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=0.5,
        duration_seconds=2.0,
        animation_keyframe_contract="advanced-v1",
    ) == pytest.approx(1.0 + 0.4 * 0.15625)
    assert native_visual_preview_rotation(
        assignment,
        time_seconds=0.5,
        duration_seconds=2.0,
        animation_keyframe_contract="advanced-v1",
    ) == pytest.approx(20.0 * 0.15625)


def test_k6_foundational_ffmpeg_expression_activates_only_with_advanced_semantics() -> None:
    track = _bezier_track(
        "position_x",
        end=0.08,
        velocity0=0.0,
        velocity1=4.0,
        overshoot=0.25,
    )
    project = _advanced_project((track,))
    assignment = project.animations[0]

    assert compile_keyframe_value_expression(
        assignment,
        "position_x",
        duration_seconds=2.0,
    ) is None
    expression = compile_keyframe_value_expression(
        assignment,
        "position_x",
        duration_seconds=2.0,
        advanced_semantics=True,
    )
    assert expression is not None
    assert "sin(3.141592654" in expression

    graph = _filter_graph(
        build_ffmpeg_command(
            build_render_plan(project, Path("k6-output.mp4"))
        )
    )
    assert "sin(3.141592654" in graph


def test_k6_validation_surfaces_mismatch_and_clamp_warnings(tmp_path: Path) -> None:
    track = AnimationKeyframeTrack(
        property_name="opacity",
        keyframes=(
            AnimationKeyframe(
                time=0.0,
                value=0.0,
                interpolation="linear",
                velocity=9.0,
                overshoot=0.75,
            ),
            AnimationKeyframe(time=1.0, value=1.0),
        ),
    )
    project = _advanced_project((track,))
    plan = build_render_plan(project, tmp_path / "out.mp4")

    project_codes = {issue.code for issue in validate_project(project)}
    render_codes = {issue.code for issue in validate_render_plan(plan).issues}

    assert "ADVANCED_PARAMETER_MISMATCH" in project_codes
    assert "ADVANCED_VALUE_CLAMPED" in project_codes
    assert "ADVANCED_PARAMETER_MISMATCH" in render_codes
    assert "ADVANCED_VALUE_CLAMPED" in render_codes
    assert validate_render_plan(plan).ok
