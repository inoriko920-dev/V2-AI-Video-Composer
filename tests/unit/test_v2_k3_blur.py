from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation import (
    blur_sigma_limit,
    evaluate_assignment_blur,
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
from aavc.presentation.motion_preview import native_visual_preview_blur_sigma
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan
from aavc.rendering.advanced_filters import compile_k3_blur_filters

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="k3-blur",
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
        property_name="blur",
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
        keyframe_tracks=tracks or (_track(),),
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


def test_k3_blur_sigma_mapping_matches_locked_resolution_contract() -> None:
    assert blur_sigma_limit(1280, 720) == pytest.approx(15.99984)
    assert blur_sigma_limit(1920, 1080) == pytest.approx(23.99976)
    assert blur_sigma_limit(3840, 2160) == pytest.approx(47.99952)
    assert blur_sigma_limit(320, 180) == pytest.approx(8.0)


def test_k3_blur_evaluator_and_preview_share_sigma_mapping() -> None:
    assignment = _advanced_project((_track(0.0, 1.0, easing="ease_in_out"),)).animations[0]

    state = evaluate_assignment_blur(
        assignment,
        0.5,
        canvas_width=1920,
        canvas_height=1080,
    )
    preview_sigma = native_visual_preview_blur_sigma(
        assignment,
        time_seconds=1.5,
        duration_seconds=3.0,
        canvas_width=1920,
        canvas_height=1080,
        animation_keyframe_contract="advanced-v1",
    )

    assert state.intensity == pytest.approx(0.5)
    assert state.sigma == pytest.approx(11.99988)
    assert preview_sigma == pytest.approx(state.sigma)


def test_k3_compiler_samples_output_frames_rounds_and_deduplicates() -> None:
    assignment = _advanced_project((_track(0.0, 1.0),)).animations[0]

    filters = compile_k3_blur_filters(
        assignment,
        duration_seconds=1.0,
        fps=4,
        canvas_width=320,
        canvas_height=180,
        instance_id="unit_blur",
    )
    joined = ",".join(filters)

    assert filters[0] == "format=rgba"
    assert filters[1] == "premultiply=inplace=1"
    assert "sendcmd=c='" in joined
    assert "0.250000 gblur@unit_blur sigma 2.00" in joined
    assert "0.250000 gblur@unit_blur sigmaV 2.00" in joined
    assert "0.500000 gblur@unit_blur sigma 4.00" in joined
    assert "0.500000 gblur@unit_blur sigmaV 4.00" in joined
    assert "0.750000 gblur@unit_blur sigma 6.00" in joined
    assert "0.750000 gblur@unit_blur sigmaV 6.00" in joined
    assert "1.000000 gblur@unit_blur sigma 8.00" in joined
    assert "1.000000 gblur@unit_blur sigmaV 8.00" in joined
    assert "gblur@unit_blur=sigma=0.00:sigmaV=0.00:steps=2" in joined
    assert filters[-1] == "unpremultiply=inplace=1"


def test_k3_blur_is_after_crop_and_before_scale_rotation(tmp_path: Path) -> None:
    crop_left = AnimationKeyframeTrack(
        property_name="crop_left",
        keyframes=(
            AnimationKeyframe(time=0.0, value=0.1),
            AnimationKeyframe(time=1.0, value=0.2),
        ),
    )
    scale = AnimationKeyframeTrack(
        property_name="scale",
        keyframes=(
            AnimationKeyframe(time=0.0, value=1.0),
            AnimationKeyframe(time=1.0, value=1.2),
        ),
    )
    rotation = AnimationKeyframeTrack(
        property_name="rotation_degrees",
        keyframes=(
            AnimationKeyframe(time=0.0, value=0.0),
            AnimationKeyframe(time=1.0, value=10.0),
        ),
    )
    project = _advanced_project((crop_left, _track(0.2, 0.6), scale, rotation))
    graph = _filter_graph(
        build_ffmpeg_command(build_render_plan(project, tmp_path / "out.mp4"))
    )

    pre_crop = graph.index("drawbox@crop_opacity_0_0_left")
    blur = graph.index("gblur@blur_opacity_0_0")
    post_crop = graph.index("drawbox@crop_post_opacity_0_0_left")
    scale_index = graph.index("scale=w='", blur)
    rotate_index = graph.index("rotate=a='", scale_index)

    assert pre_crop < blur < post_crop < scale_index < rotate_index


def test_k3_v4_blur_preflight_and_validation_are_green(tmp_path: Path) -> None:
    project = _advanced_project()
    plan = build_render_plan(project, tmp_path / "blur.mp4")

    assert validate_render_plan(plan).ok
    assert not any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in validate_project(project)
    )


def test_k3_v3_blur_stays_dormant_and_filtergraph_unchanged(
    tmp_path: Path,
) -> None:
    project = _project()
    scene = project.scenes[0]
    baseline_assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
    )
    blur_assignment = replace(
        baseline_assignment,
        keyframe_tracks=(_track(),),
    )
    baseline = replace(project, animations=(baseline_assignment,))
    dormant = replace(project, animations=(blur_assignment,))

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


def test_k6_bezier_blur_is_active_in_advanced_v1(tmp_path: Path) -> None:
    project = _advanced_project((_track(interpolation="bezier"),))
    plan = build_render_plan(project, tmp_path / "bezier.mp4")
    graph = _filter_graph(build_ffmpeg_command(plan))
    report = validate_render_plan(plan)

    assert "gblur@blur_opacity_0_0" in graph
    assert not any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in report.issues
    )
    assert report.ok


class _BlurCapabilityRunner(ProcessRunner):
    def __init__(self, *, blur_ok: bool) -> None:
        self.blur_ok = blur_ok

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
            if not self.blur_ok:
                return ProcessResult(1, "", "runtime gblur unavailable")
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


def test_k3_capability_gate_fails_closed_when_runtime_gblur_probe_fails(
    tmp_path: Path,
) -> None:
    plan = build_render_plan(_advanced_project(), tmp_path / "out.mp4")

    with pytest.raises(RenderError, match="named_gblur"):
        ensure_advanced_render_capabilities(
            plan,
            ffmpeg_path="fake-ffmpeg",
            runner=_BlurCapabilityRunner(blur_ok=False),
        )


def test_k3_capability_gate_accepts_proven_runtime_gblur(tmp_path: Path) -> None:
    plan = build_render_plan(_advanced_project(), tmp_path / "out.mp4")

    ensure_advanced_render_capabilities(
        plan,
        ffmpeg_path="fake-ffmpeg",
        runner=_BlurCapabilityRunner(blur_ok=True),
    )
