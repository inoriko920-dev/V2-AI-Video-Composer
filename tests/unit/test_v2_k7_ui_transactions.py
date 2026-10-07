from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation.contract import (
    ADVANCED_KEYFRAME_CONTRACT,
    ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY,
)
from aavc.application.commands import (
    AdvancedAnimationActivationRequired,
    ApplyAnimationKeyframeEdit,
    RemoveAnimationKeyframeTrack,
)
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.animation import (
    AnimationKeyframe,
    AnimationKeyframeTrack,
    KeyframeInterpolation,
    TransformProperty,
)
from aavc.domain.project.models import AnimationAssignment, ProjectState
from aavc.presentation.dialogs.asset_motion import build_asset_motion_assignment

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project() -> ProjectState:
    return create_project_state(
        title="v0.2.1-k7",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _track(
    property_name: TransformProperty,
    *,
    interpolation: KeyframeInterpolation = "linear",
) -> AnimationKeyframeTrack:
    values = {
        "scale": (1.0, 1.2),
        "opacity": (0.2, 1.0),
        "mask_progress": (0.0, 1.0),
        "blur": (0.0, 0.5),
    }
    start, end = values[property_name]
    return AnimationKeyframeTrack(
        property_name=property_name,
        keyframes=(
            AnimationKeyframe(
                time=0.0,
                value=start,
                interpolation=interpolation,
                velocity=1.0 if interpolation == "bezier" else None,
                overshoot=0.15 if interpolation == "bezier" else None,
            ),
            AnimationKeyframe(time=1.0, value=end),
        ),
    )


def _target(project: ProjectState, index: int = 0) -> tuple[int, str]:
    targets = [
        (scene.scene_number, asset_id)
        for scene in project.scenes
        for asset_id in scene.asset_ids
    ]
    return targets[index]


def test_preset_edit_preserves_dormant_tracks_without_promoting_v3(
    tmp_path: Path,
) -> None:
    project = _project()
    scene_number, asset_id = _target(project)
    existing = AnimationAssignment(
        scene_number=scene_number,
        asset_id=asset_id,
        enter_effect="Fade",
        exit_effect="Fade",
        keyframe_tracks=(_track("opacity"),),
    )
    project = replace(project, animations=(existing,))
    candidate = build_asset_motion_assignment(
        scene_number=scene_number,
        asset_id=asset_id,
        enter_effect="Rise",
        exit_effect="Drift",
        intensity=1.25,
        locked=True,
        existing_assignment=existing,
    )
    session = ProjectSession()
    session.start(project, tmp_path / "preset-preserve.aavcproj")

    changed = session.execute(ApplyAnimationKeyframeEdit(candidate))

    assert changed.schema_version == 3
    assert ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY not in changed.metadata
    assert changed.animations[0].keyframe_tracks == existing.keyframe_tracks
    assert changed.animations[0].locked
    assert session.undo() == project


def test_foundational_linear_edit_stays_v3_and_is_one_history_entry(
    tmp_path: Path,
) -> None:
    project = _project()
    scene_number, asset_id = _target(project)
    candidate = AnimationAssignment(
        scene_number=scene_number,
        asset_id=asset_id,
        keyframe_tracks=(_track("scale"),),
    )
    session = ProjectSession()
    session.start(project, tmp_path / "foundation.aavcproj")

    changed = session.execute(ApplyAnimationKeyframeEdit(candidate))

    assert changed.schema_version == 3
    assert changed.animations[0].keyframe_tracks == candidate.keyframe_tracks
    assert session.can_undo
    assert session.undo() == project
    assert not session.can_undo
    assert session.can_redo


def test_advanced_edit_requires_confirmation_before_any_mutation(
    tmp_path: Path,
) -> None:
    project = _project()
    scene_number, asset_id = _target(project)
    candidate = AnimationAssignment(
        scene_number=scene_number,
        asset_id=asset_id,
        keyframe_tracks=(_track("opacity"),),
    )
    session = ProjectSession()
    session.start(project, tmp_path / "activation.aavcproj")

    with pytest.raises(AdvancedAnimationActivationRequired) as captured:
        session.execute(ApplyAnimationKeyframeEdit(candidate))

    assert captured.value.changed_properties == ("opacity",)
    assert not captured.value.requires_dormant_acknowledgement
    assert session.current == project
    assert not session.can_undo

    promoted = session.execute(
        ApplyAnimationKeyframeEdit(candidate, activate_advanced=True)
    )

    assert promoted.schema_version == 4
    assert (
        promoted.metadata[ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY]
        == ADVANCED_KEYFRAME_CONTRACT
    )
    assert promoted.animations[0] == candidate
    assert session.undo() == project


def test_unrelated_dormant_tracks_require_explicit_acknowledgement(
    tmp_path: Path,
) -> None:
    project = _project()
    first_scene, first_asset = _target(project, 0)
    second_scene, second_asset = _target(project, 1)
    dormant = AnimationAssignment(
        scene_number=first_scene,
        asset_id=first_asset,
        keyframe_tracks=(_track("opacity"),),
    )
    project = replace(project, animations=(dormant,))
    candidate = AnimationAssignment(
        scene_number=second_scene,
        asset_id=second_asset,
        keyframe_tracks=(_track("mask_progress"),),
    )
    session = ProjectSession()
    session.start(project, tmp_path / "dormant-ack.aavcproj")

    with pytest.raises(AdvancedAnimationActivationRequired) as captured:
        session.execute(
            ApplyAnimationKeyframeEdit(
                candidate,
                activate_advanced=True,
            )
        )

    assert captured.value.requires_dormant_acknowledgement
    assert captured.value.dormant_locations == (
        (first_scene, first_asset, "opacity"),
    )
    assert session.current == project
    assert not session.can_undo

    promoted = session.execute(
        ApplyAnimationKeyframeEdit(
            candidate,
            activate_advanced=True,
            acknowledge_dormant=True,
        )
    )
    assert promoted.schema_version == 4
    assert len(promoted.animations) == 2
    assert session.undo() == project


def test_remove_dormant_advanced_track_does_not_promote_or_demote(
    tmp_path: Path,
) -> None:
    project = _project()
    scene_number, asset_id = _target(project)
    existing = AnimationAssignment(
        scene_number=scene_number,
        asset_id=asset_id,
        keyframe_tracks=(_track("opacity"),),
    )
    project = replace(project, animations=(existing,))
    session = ProjectSession()
    session.start(project, tmp_path / "remove-track.aavcproj")

    changed = session.execute(
        RemoveAnimationKeyframeTrack(
            scene_number=scene_number,
            asset_id=asset_id,
            property_name="opacity",
        )
    )

    assert changed.schema_version == 3
    assert changed.animations[0].keyframe_tracks == ()
    assert session.undo() == project


def test_existing_v4_project_does_not_prompt_again_for_advanced_edit(
    tmp_path: Path,
) -> None:
    project = _project()
    scene_number, asset_id = _target(project)
    first = AnimationAssignment(
        scene_number=scene_number,
        asset_id=asset_id,
        keyframe_tracks=(_track("opacity"),),
    )
    session = ProjectSession()
    session.start(project, tmp_path / "already-v4.aavcproj")
    advanced = session.execute(
        ApplyAnimationKeyframeEdit(first, activate_advanced=True)
    )

    second = replace(
        advanced.animations[0],
        keyframe_tracks=(
            _track("opacity"),
            _track("blur", interpolation="bezier"),
        ),
    )
    changed = session.execute(ApplyAnimationKeyframeEdit(second))

    assert changed.schema_version == 4
    assert len(changed.animations[0].keyframe_tracks) == 2
