from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Sequence

import pytest

from aavc.animation import (
    CropVisibility,
    evaluate_assignment_crop_visibility,
    normalize_crop_visibility,
)
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
from aavc.presentation.motion_preview import native_visual_preview_crop
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan
from aavc.rendering.advanced_filters import compile_k2_crop_mask_filter

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="k2-crop",
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
        keyframe_tracks=tracks
        or (
            _track("crop_left", 0.0, 0.25),
            _track("crop_right", 0.10, 0.0),
        ),
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


def test_k2_crop_normalization_keeps_at_least_ten_percent_visible() -> None:
    crop = normalize_crop_visibility(0.45, 0.45, 0.45, 0.45)

    assert crop.left == pytest.approx(0.45)
    assert crop.top == pytest.approx(0.45)
    assert crop.right == pytest.approx(0.45)
    assert crop.bottom == pytest.approx(0.45)
    assert crop.normalized is False
    assert crop.visible_width == pytest.approx(0.10)
    assert crop.visible_height == pytest.approx(0.10)


def test_k2_crop_preview_is_contract_aware() -> None:
    assignment = _advanced_project().animations[0]

    legacy = native_visual_preview_crop(
        assignment,
        time_seconds=1.5,
        duration_seconds=3.0,
        animation_keyframe_contract="legacy-v3",
    )
    advanced = native_visual_preview_crop(
        assignment,
        time_seconds=1.5,
        duration_seconds=3.0,
        animation_keyframe_contract="advanced-v1",
    )

    assert legacy == CropVisibility()
    assert advanced.left == pytest.approx(0.125)
    assert advanced.right == pytest.approx(0.05)
    assert advanced.visible_width == pytest.approx(0.825)


def test_k2_compiler_uses_fixed_canvas_dynamic_spatial_alpha() -> None:
    assignment = _advanced_project().animations[0]

    mask_filter = compile_k2_crop_mask_filter(
        assignment,
        duration_seconds=2.0,
    )

    assert mask_filter is not None
    assert "geq=lum='p(X,Y)*" in mask_filter
    assert "gte(X,W*" in mask_filter
    assert "lt(X,W*(1-" in mask_filter
    assert "T" in mask_filter


def test_k2_crop_precedes_scale_and_rotation_in_final_graph(tmp_path: Path) -> None:
    project = _advanced_project(
        (
            _track("crop_left", 0.0, 0.2),
            _track("scale", 1.0, 1.2),
            _track("rotation_degrees", 0.0, 10.0),
        )
    )
    graph = _filter_graph(build_ffmpeg_command(build_render_plan(project, tmp_path / "out.mp4")))

    crop_index = graph.index("geq=")
    scale_index = graph.index("scale=w='", crop_index)
    rotate_index = graph.index("rotate=a='", scale_index)

    assert crop_index < scale_index < rotate_index


def test_k2_v4_crop_preflight_and_project_validation_are_green(
    tmp_path: Path,
) -> None:
    project = _advanced_project()
    plan = build_render_plan(project, tmp_path / "out.mp4")

    assert validate_render_plan(plan).ok
    assert not any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in validate_project(project)
    )


def test_k2_crop_value_clamp_is_visible_as_warning(tmp_path: Path) -> None:
    project = _advanced_project((_track("crop_left", 0.70, 0.20),))
    plan = build_render_plan(project, tmp_path / "out.mp4")

    assert any(
        issue.code == "ADVANCED_VALUE_CLAMPED"
        for issue in validate_render_plan(plan).issues
    )
    assert any(
        issue.code == "ADVANCED_VALUE_CLAMPED"
        for issue in validate_project(project)
    )
    evaluated = evaluate_assignment_crop_visibility(project.animations[0], 0.0)
    assert evaluated.left == pytest.approx(0.45)


def test_k2_v3_crop_stays_dormant_and_filtergraph_unchanged(
    tmp_path: Path,
) -> None:
    project = _project()
    scene = project.scenes[0]
    baseline_assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
    )
    crop_assignment = replace(
        baseline_assignment,
        keyframe_tracks=(_track("crop_left", 0.0, 0.25),),
    )
    baseline = replace(project, animations=(baseline_assignment,))
    dormant = replace(project, animations=(crop_assignment,))

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


def test_k2_bezier_crop_remains_blocked_until_k6(tmp_path: Path) -> None:
    project = _advanced_project(
        (_track("crop_left", 0.0, 0.25, interpolation="bezier"),)
    )
    plan = build_render_plan(project, tmp_path / "bezier.mp4")
    graph = _filter_graph(build_ffmpeg_command(plan))
    report = validate_render_plan(plan)

    assert "geq=" not in graph
    assert any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in report.issues
    )
    assert not report.ok


class _CropCapabilityRunner(ProcessRunner):
    def __init__(self, *, crop_ok: bool) -> None:
        self.crop_ok = crop_ok

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
        if "geq=" in joined and not self.crop_ok:
            return ProcessResult(1, "", "dynamic spatial alpha unavailable")
        return ProcessResult(0, "", "")


def test_k2_capability_gate_fails_closed_when_spatial_alpha_probe_fails(
    tmp_path: Path,
) -> None:
    plan = build_render_plan(_advanced_project(), tmp_path / "out.mp4")

    with pytest.raises(
        RenderError,
        match="dynamic_spatial_alpha",
    ):
        ensure_advanced_render_capabilities(
            plan,
            ffmpeg_path="fake-ffmpeg",
            runner=_CropCapabilityRunner(crop_ok=False),
        )


def test_k2_capability_gate_accepts_proven_spatial_alpha(tmp_path: Path) -> None:
    plan = build_render_plan(_advanced_project(), tmp_path / "out.mp4")

    ensure_advanced_render_capabilities(
        plan,
        ffmpeg_path="fake-ffmpeg",
        runner=_CropCapabilityRunner(crop_ok=True),
    )
