from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation import (
    evaluate_advanced_keyframe_track,
    is_supported_advanced_keyframe_track,
)
from aavc.animation.contract import (
    ADVANCED_KEYFRAME_CONTRACT,
    ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY,
)
from aavc.application.services.validation import validate_project
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.motion_preview import native_visual_preview_opacity
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan
from aavc.rendering.advanced_filters import compile_k1_opacity_filters

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="k1-opacity",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _track(
    start: float = 0.0,
    end: float = 1.0,
    *,
    interpolation: str = "linear",
    easing: str = "linear",
) -> AnimationKeyframeTrack:
    return AnimationKeyframeTrack(
        property_name="opacity",
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


def _advanced_project(track: AnimationKeyframeTrack | None = None):
    project = _project()
    scene = project.scenes[0]
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
        keyframe_tracks=((track or _track()),),
    )
    metadata = dict(project.metadata)
    metadata[ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY] = ADVANCED_KEYFRAME_CONTRACT
    return replace(
        project,
        schema_version=4,
        metadata=metadata,
        animations=(assignment,),
    )


def _filter_graph(command: list[str]) -> str:
    return command[command.index("-filter_complex") + 1]


def test_k1_opacity_evaluator_clamps_and_matches_quadratic_easing() -> None:
    track = _track(-0.5, 1.5, easing="ease_in_out")

    assert is_supported_advanced_keyframe_track(track)
    assert evaluate_advanced_keyframe_track(track, 0.0) == pytest.approx(0.0)
    assert evaluate_advanced_keyframe_track(track, 0.25) == pytest.approx(0.0)
    assert evaluate_advanced_keyframe_track(track, 0.50) == pytest.approx(0.5)
    assert evaluate_advanced_keyframe_track(track, 0.75) == pytest.approx(1.0)
    assert evaluate_advanced_keyframe_track(track, 1.0) == pytest.approx(1.0)


def test_k1_preview_is_contract_aware_and_works_with_zero_legacy_intensity() -> None:
    assignment = _advanced_project().animations[0]

    legacy = native_visual_preview_opacity(
        assignment,
        time_seconds=1.5,
        duration_seconds=3.0,
        animation_keyframe_contract="legacy-v3",
    )
    advanced = native_visual_preview_opacity(
        assignment,
        time_seconds=1.5,
        duration_seconds=3.0,
        animation_keyframe_contract="advanced-v1",
    )

    assert legacy == pytest.approx(1.0)
    assert advanced == pytest.approx(0.5)


def test_k1_compiler_uses_runtime_alpha_gain_and_preserves_source_alpha() -> None:
    assignment = _advanced_project(_track(0.2, 0.8, easing="ease_out")).animations[0]

    filters = compile_k1_opacity_filters(
        assignment,
        duration_seconds=2.0,
        instance_id="opacity_test",
    )
    joined = ",".join(filters)

    assert filters[0] == "format=rgba"
    assert "sendcmd=c='" in joined
    assert "colorchannelmixer@opacity_test aa" in joined
    assert "1-(1-TI)*(1-TI)" in joined
    assert "colorchannelmixer@opacity_test=aa=0.200000" in joined


def test_k1_v4_opacity_reaches_final_graph_and_preflight_is_green(
    tmp_path: Path,
) -> None:
    project = _advanced_project()
    plan = build_render_plan(project, tmp_path / "out.mp4")
    graph = _filter_graph(build_ffmpeg_command(plan))
    report = validate_render_plan(plan)

    assert "sendcmd=c='" in graph
    assert "colorchannelmixer@opacity_0_0" in graph
    assert not any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in report.issues
    )
    assert report.ok


def test_k1_v4_project_validation_no_longer_flags_opacity_backend() -> None:
    issues = validate_project(_advanced_project())

    assert not any(issue.code == "ADVANCED_BACKEND_UNAVAILABLE" for issue in issues)


def test_k1_v3_opacity_stays_dormant_and_filtergraph_unchanged(
    tmp_path: Path,
) -> None:
    project = _project()
    scene = project.scenes[0]
    baseline_assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
    )
    opacity_assignment = replace(
        baseline_assignment,
        keyframe_tracks=(_track(),),
    )
    baseline = replace(project, animations=(baseline_assignment,))
    dormant = replace(project, animations=(opacity_assignment,))

    baseline_graph = _filter_graph(
        build_ffmpeg_command(build_render_plan(baseline, tmp_path / "base.mp4"))
    )
    dormant_plan = build_render_plan(dormant, tmp_path / "dormant.mp4")
    dormant_graph = _filter_graph(build_ffmpeg_command(dormant_plan))

    assert dormant_graph == baseline_graph
    assert any(
        issue.code == "ADVANCED_TRACK_DORMANT"
        for issue in validate_render_plan(dormant_plan).issues
    )


def test_k1_bezier_opacity_remains_blocked_until_k6(tmp_path: Path) -> None:
    project = _advanced_project(_track(interpolation="bezier"))
    plan = build_render_plan(project, tmp_path / "bezier.mp4")
    graph = _filter_graph(build_ffmpeg_command(plan))
    report = validate_render_plan(plan)

    assert "colorchannelmixer@opacity_0_0" not in graph
    assert any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in report.issues
    )
    assert not report.ok
