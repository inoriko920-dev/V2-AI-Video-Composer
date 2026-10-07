from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation import (
    evaluate_assignment_glow,
    evaluate_assignment_shadow,
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
from aavc.presentation.motion_preview import (
    native_visual_preview_glow,
    native_visual_preview_shadow,
)
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan
from aavc.rendering.advanced_filters import compile_k4_shadow_glow_clauses

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="k4-shadow-glow",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _track(
    property_name: str,
    start: float,
    end: float | None = None,
    *,
    interpolation: str = "linear",
    easing: str = "linear",
) -> AnimationKeyframeTrack:
    points = [
        AnimationKeyframe(
            time=0.0,
            value=start,
            interpolation=interpolation,  # type: ignore[arg-type]
            easing=easing,  # type: ignore[arg-type]
        )
    ]
    if end is not None:
        points.append(AnimationKeyframe(time=1.0, value=end))
    return AnimationKeyframeTrack(
        property_name=property_name,  # type: ignore[arg-type]
        keyframes=tuple(points),
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
            _track("shadow", 0.5),
            _track("glow", 0.5),
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


def test_k4_shadow_glow_mapping_matches_locked_contract() -> None:
    assignment = _advanced_project().animations[0]

    shadow = evaluate_assignment_shadow(
        assignment,
        0.5,
        canvas_width=1920,
        canvas_height=1080,
    )
    glow = evaluate_assignment_glow(
        assignment,
        0.5,
        canvas_width=1920,
        canvas_height=1080,
    )

    assert shadow.intensity == pytest.approx(0.5)
    assert shadow.alpha == pytest.approx(0.275)
    assert shadow.offset == pytest.approx(6.48)
    assert shadow.sigma == pytest.approx(7.56)
    assert glow.intensity == pytest.approx(0.5)
    assert glow.alpha == pytest.approx(0.325)
    assert glow.sigma == pytest.approx(9.72)


def test_k4_preview_states_share_canonical_mapping() -> None:
    assignment = _advanced_project(
        (
            _track("shadow", 0.0, 1.0, easing="ease_in_out"),
            _track("glow", 0.0, 1.0, easing="ease_in_out"),
        )
    ).animations[0]

    shadow = native_visual_preview_shadow(
        assignment,
        time_seconds=1.5,
        duration_seconds=3.0,
        canvas_width=1920,
        canvas_height=1080,
        animation_keyframe_contract="advanced-v1",
    )
    glow = native_visual_preview_glow(
        assignment,
        time_seconds=1.5,
        duration_seconds=3.0,
        canvas_width=1920,
        canvas_height=1080,
        animation_keyframe_contract="advanced-v1",
    )

    assert shadow == evaluate_assignment_shadow(
        assignment,
        0.5,
        canvas_width=1920,
        canvas_height=1080,
    )
    assert glow == evaluate_assignment_glow(
        assignment,
        0.5,
        canvas_width=1920,
        canvas_height=1080,
    )


def test_k4_compiler_builds_alpha_branches_behind_main_source() -> None:
    assignment = _advanced_project().animations[0]

    clauses = compile_k4_shadow_glow_clauses(
        "input",
        "output",
        assignment,
        duration_seconds=1.0,
        fps=30,
        canvas_width=1920,
        canvas_height=1080,
        instance_id="unit_k4",
    )
    graph = ";".join(clauses)

    assert "[input]format=rgba,split=4" in graph
    assert "alphaextract" in graph
    assert "gblur@unit_k4_shadow_blur" in graph
    assert "gblur@unit_k4_glow_blur" in graph
    assert "lutrgb=r=0:g=0:b=0" in graph
    assert "lutrgb=r=255:g=255:b=255" in graph
    assert "alphamerge" in graph
    assert "colorchannelmixer@unit_k4_shadow_gain=aa=0.2750" in graph
    assert "colorchannelmixer@unit_k4_glow_gain=aa=0.3250" in graph
    assert "12.960000*(" in graph
    assert graph.rfind("[unit_k4_main]overlay") > graph.index("shadow_layer")


def test_k4_stage_is_after_rotation_and_before_group_opacity(tmp_path: Path) -> None:
    project = _advanced_project(
        (
            _track("rotation_degrees", 0.0, 10.0),
            _track("shadow", 0.5),
            _track("glow", 0.5),
            _track("opacity", 0.5),
        )
    )
    graph = _filter_graph(
        build_ffmpeg_command(
            build_render_plan(project, tmp_path / "out.mp4")
        )
    )

    rotate_index = graph.index("rotate=a='")
    k4_index = graph.index("gblur@k4_opacity_0_0_glow_blur")
    opacity_index = graph.index("colorchannelmixer@opacity_0_0")

    assert rotate_index < k4_index < opacity_index
    assert "]null" in graph


def test_k4_v4_preflight_and_validation_are_green(tmp_path: Path) -> None:
    project = _advanced_project()
    plan = build_render_plan(project, tmp_path / "out.mp4")

    assert validate_render_plan(plan).ok
    assert not any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in validate_project(project)
    )


def test_k4_v3_tracks_stay_dormant_and_filtergraph_unchanged(
    tmp_path: Path,
) -> None:
    project = _project()
    scene = project.scenes[0]
    baseline_assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
    )
    k4_assignment = replace(
        baseline_assignment,
        keyframe_tracks=(
            _track("shadow", 0.5),
            _track("glow", 0.5),
        ),
    )
    baseline = replace(project, animations=(baseline_assignment,))
    dormant = replace(project, animations=(k4_assignment,))

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


@pytest.mark.parametrize("property_name", ["shadow", "glow"])
def test_k4_bezier_tracks_remain_blocked_until_k6(
    tmp_path: Path,
    property_name: str,
) -> None:
    project = _advanced_project(
        (_track(property_name, 0.0, 1.0, interpolation="bezier"),)
    )
    plan = build_render_plan(project, tmp_path / f"{property_name}.mp4")
    graph = _filter_graph(build_ffmpeg_command(plan))
    report = validate_render_plan(plan)

    assert "k4_opacity_0_0" not in graph
    assert any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in report.issues
    )
    assert not report.ok


class _K4CapabilityRunner(ProcessRunner):
    def __init__(self, *, k4_ok: bool) -> None:
        self.k4_ok = k4_ok

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
        if "gblur@k3_probe" in joined:
            return ProcessResult(
                0,
                (
                    "0,0,0,1,4096,aaaa\n"
                    "0,1,1,1,4096,bbbb\n"
                    "0,2,2,1,4096,cccc\n"
                    "0,3,3,1,4096,dddd\n"
                ),
                "",
            )
        if "gblur@k4_branch" in joined:
            if not self.k4_ok:
                return ProcessResult(1, "", "alpha branch unavailable")
            return ProcessResult(
                0,
                (
                    "0,0,0,1,4096,aaaa\n"
                    "0,1,1,1,4096,bbbb\n"
                    "0,2,2,1,4096,cccc\n"
                    "0,3,3,1,4096,dddd\n"
                ),
                "",
            )
        return ProcessResult(0, "", "")


def test_k4_capability_gate_fails_closed_when_alpha_branch_probe_fails(
    tmp_path: Path,
) -> None:
    plan = build_render_plan(_advanced_project(), tmp_path / "out.mp4")

    with pytest.raises(RenderError, match="alpha_branch"):
        ensure_advanced_render_capabilities(
            plan,
            ffmpeg_path="fake-ffmpeg",
            runner=_K4CapabilityRunner(k4_ok=False),
        )


def test_k4_capability_gate_accepts_proven_alpha_branch(tmp_path: Path) -> None:
    plan = build_render_plan(_advanced_project(), tmp_path / "out.mp4")

    ensure_advanced_render_capabilities(
        plan,
        ffmpeg_path="fake-ffmpeg",
        runner=_K4CapabilityRunner(k4_ok=True),
    )
