from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation.compiler import compile_motion_overlay_position
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment
from aavc.rendering import build_ffmpeg_command, build_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="wave-d-keyframes",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_keyframe_model_requires_normalized_ordered_time() -> None:
    with pytest.raises(ValueError, match="rentang 0–1"):
        AnimationKeyframe(time=1.1, value=1.0)

    first = AnimationKeyframe(time=0.5, value=1.0)
    second = AnimationKeyframe(time=0.5, value=2.0)
    with pytest.raises(ValueError, match="unik dan meningkat"):
        AnimationKeyframeTrack(
            property_name="scale",
            keyframes=(first, second),
        )


def test_assignment_rejects_duplicate_transform_tracks() -> None:
    track = AnimationKeyframeTrack(
        property_name="opacity",
        keyframes=(AnimationKeyframe(time=0.0, value=0.0),),
    )
    with pytest.raises(ValueError, match="property duplikat"):
        AnimationAssignment(
            scene_number=1,
            asset_id="A001",
            keyframe_tracks=(track, track),
        )


def test_legacy_assignment_defaults_to_no_keyframe_tracks() -> None:
    assignment = AnimationAssignment(scene_number=1, asset_id="A001")
    assert assignment.keyframe_tracks == ()


def test_wave_e_keeps_legacy_effect_semantics_when_tracks_are_absent(
    tmp_path: Path,
) -> None:
    project = _project()
    scene = project.scenes[0]
    legacy = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        enter_effect="Pan",
        exit_effect="Fade",
        intensity=1.25,
    )
    same_legacy = replace(legacy, keyframe_tracks=())

    baseline = replace(project, animations=(legacy,))
    candidate = replace(project, animations=(same_legacy,))

    baseline_command = build_ffmpeg_command(
        build_render_plan(baseline, tmp_path / "baseline.mp4")
    )
    candidate_command = build_ffmpeg_command(
        build_render_plan(candidate, tmp_path / "candidate.mp4")
    )

    baseline_graph = baseline_command[baseline_command.index("-filter_complex") + 1]
    candidate_graph = candidate_command[candidate_command.index("-filter_complex") + 1]
    assert candidate_graph == baseline_graph
    assert "W*0.075000" in baseline_graph
    assert "fade=t=out:st=2.750000:d=0.250000:alpha=1" in baseline_graph

    baseline_xy = compile_motion_overlay_position(
        base_x="(W-w)/2",
        base_y="(H-h)/2",
        assignment=legacy,
        duration_seconds=3.0,
    )
    candidate_xy = compile_motion_overlay_position(
        base_x="(W-w)/2",
        base_y="(H-h)/2",
        assignment=same_legacy,
        duration_seconds=3.0,
    )
    assert candidate_xy == baseline_xy
