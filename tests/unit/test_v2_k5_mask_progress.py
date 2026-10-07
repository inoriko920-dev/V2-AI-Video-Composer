from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation import evaluate_assignment_advanced_keyframe
from aavc.animation.contract import (
    ADVANCED_KEYFRAME_CONTRACT,
    ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY,
)
from aavc.application.services.export_service import ensure_advanced_render_capabilities
from aavc.application.services.validation import validate_project
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.errors import RenderError
from aavc.domain.project.models import AnimationAssignment
from aavc.platform.process_runner import ProcessResult, ProcessRunner
from aavc.presentation.motion_preview import native_visual_preview_mask_progress
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan
from aavc.rendering.advanced_filters import compile_k5_mask_filters

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="k5-mask-progress",
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


def _advanced_project(
    tracks: tuple[AnimationKeyframeTrack, ...] | None = None,
):
    project = _project()
    scene = project.scenes[0]
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
        keyframe_tracks=tracks or (_track("mask_progress", 0.0, 1.0),),
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


def test_k5_mask_evaluator_clamps_and_preview_is_contract_aware() -> None:
    project = _advanced_project((_track("mask_progress", -0.5, 1.5),))
    assignment = project.animations[0]

    assert evaluate_assignment_advanced_keyframe(
        assignment,
        "mask_progress",
        0.0,
    ) == pytest.approx(0.0)
    assert evaluate_assignment_advanced_keyframe(
        assignment,
        "mask_progress",
        0.5,
    ) == pytest.approx(0.5)
    assert evaluate_assignment_advanced_keyframe(
        assignment,
        "mask_progress",
        1.0,
    ) == pytest.approx(1.0)

    legacy = native_visual_preview_mask_progress(
        assignment,
        time_seconds=1.5,
        duration_seconds=3.0,
        animation_keyframe_contract="legacy-v3",
    )
    advanced = native_visual_preview_mask_progress(
        assignment,
        time_seconds=1.5,
        duration_seconds=3.0,
        animation_keyframe_contract="advanced-v1",
    )

    assert legacy == pytest.approx(1.0)
    assert advanced == pytest.approx(0.5)


def test_k5_compiler_uses_fixed_canvas_transparent_right_edge() -> None:
    assignment = _advanced_project().animations[0]

    filters = compile_k5_mask_filters(
        assignment,
        duration_seconds=2.0,
        instance_id="unit_mask",
    )
    joined = ",".join(filters)

    assert filters[0] == "format=rgba"
    assert "sendcmd=c='" in joined
    assert "drawbox@unit_mask" in joined
    assert "ceil(W*" in joined
    assert "ceil(iw*" in joined
    assert "color=black@0" in joined
    assert "replace=1" in joined


def test_k5_stage_order_is_rotation_mask_shadow_glow_opacity(
    tmp_path: Path,
) -> None:
    project = _advanced_project(
        (
            _track("rotation_degrees", 0.0, 10.0),
            _track("mask_progress", 0.2, 0.8),
            _track("shadow", 0.2, 0.6),
            _track("glow", 0.1, 0.5),
            _track("opacity", 1.0, 0.5),
        )
    )
    graph = _filter_graph(
        build_ffmpeg_command(
            build_render_plan(project, tmp_path / "out.mp4")
        )
    )

    rotation = graph.index("rotate=a='")
    mask = graph.index("drawbox@mask_opacity_0_0")
    k4 = graph.index("k4_opacity_0_0")
    opacity = graph.index("colorchannelmixer@opacity_0_0")

    assert rotation < mask < k4 < opacity


def test_k5_v4_mask_preflight_and_project_validation_are_green(
    tmp_path: Path,
) -> None:
    project = _advanced_project()
    plan = build_render_plan(project, tmp_path / "out.mp4")

    assert validate_render_plan(plan).ok
    assert not any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in validate_project(project)
    )


def test_k5_v3_mask_stays_dormant_and_filtergraph_unchanged(
    tmp_path: Path,
) -> None:
    project = _project()
    scene = project.scenes[0]
    baseline_assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
    )
    mask_assignment = replace(
        baseline_assignment,
        keyframe_tracks=(_track("mask_progress", 0.0, 1.0),),
    )
    baseline = replace(project, animations=(baseline_assignment,))
    dormant = replace(project, animations=(mask_assignment,))

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


def test_k5_bezier_mask_remains_blocked_until_k6(tmp_path: Path) -> None:
    project = _advanced_project(
        (_track("mask_progress", 0.0, 1.0, interpolation="bezier"),)
    )
    plan = build_render_plan(project, tmp_path / "bezier.mp4")
    graph = _filter_graph(build_ffmpeg_command(plan))
    report = validate_render_plan(plan)

    assert "drawbox@mask_opacity_0_0" not in graph
    assert any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in report.issues
    )
    assert not report.ok


class _MaskCapabilityRunner(ProcessRunner):
    def __init__(self, *, spatial_alpha_ok: bool) -> None:
        self.spatial_alpha_ok = spatial_alpha_ok

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del timeout_seconds
        if "-version" in argv:
            return ProcessResult(0, "ffmpeg version 9.0 Copyright", "")

        joined = " ".join(argv)
        if "drawbox@k2_left" in joined:
            if not self.spatial_alpha_ok:
                return ProcessResult(
                    1,
                    "",
                    "dynamic spatial alpha unavailable",
                )
            return ProcessResult(0, "", "")
        if "gblur@k3_probe" in joined:
            return ProcessResult(
                0,
                (
                    "0, 0, 0, 1, 4096, aaaa\n"
                    "0, 1, 1, 1, 4096, bbbb\n"
                    "0, 2, 2, 1, 4096, cccc\n"
                    "0, 3, 3, 1, 4096, dddd\n"
                ),
                "",
            )
        return ProcessResult(0, "", "")


def test_k5_capability_gate_fails_closed_without_spatial_alpha(
    tmp_path: Path,
) -> None:
    plan = build_render_plan(_advanced_project(), tmp_path / "out.mp4")

    with pytest.raises(RenderError, match="dynamic_spatial_alpha"):
        ensure_advanced_render_capabilities(
            plan,
            ffmpeg_path="fake-ffmpeg",
            runner=_MaskCapabilityRunner(spatial_alpha_ok=False),
        )


def test_k5_capability_gate_accepts_proven_spatial_alpha(tmp_path: Path) -> None:
    plan = build_render_plan(_advanced_project(), tmp_path / "out.mp4")

    ensure_advanced_render_capabilities(
        plan,
        ffmpeg_path="fake-ffmpeg",
        runner=_MaskCapabilityRunner(spatial_alpha_ok=True),
    )
