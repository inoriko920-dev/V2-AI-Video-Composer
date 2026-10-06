from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aavc.application.commands import CopySceneAnimations
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="wave-f-copy-animation",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _project_with_compatible_target():
    project = _project()
    source = next(scene for scene in project.scenes if len(scene.asset_ids) == 2)
    target = replace(
        source,
        scene_number=max(scene.scene_number for scene in project.scenes) + 1,
    )
    return replace(project, scenes=(*project.scenes, target)), source, target


def test_copy_scene_animations_maps_by_asset_slot_and_is_undoable(
    tmp_path: Path,
) -> None:
    project, source, target = _project_with_compatible_target()
    track = AnimationKeyframeTrack(
        property_name="position_x",
        keyframes=(
            AnimationKeyframe(time=0.0, value=0.0),
            AnimationKeyframe(time=1.0, value=0.08, easing="ease_out"),
        ),
    )
    source_assignments = (
        AnimationAssignment(
            source.scene_number,
            source.asset_ids[0],
            enter_effect="Pan",
            exit_effect="Fade",
            intensity=0.8,
            keyframe_tracks=(track,),
        ),
        AnimationAssignment(
            source.scene_number,
            source.asset_ids[1],
            enter_effect="Rise",
            exit_effect="Drift",
            intensity=1.1,
        ),
    )
    project = replace(project, animations=source_assignments)

    session = ProjectSession()
    session.start(project, tmp_path / "wave-f-copy.aavcproj")
    changed = session.execute(
        CopySceneAnimations(source.scene_number, (target.scene_number,))
    )

    copied = tuple(
        item
        for item in changed.animations
        if item.scene_number == target.scene_number
    )
    assert len(copied) == 2
    assert copied[0].asset_id == target.asset_ids[0]
    assert copied[1].asset_id == target.asset_ids[1]
    assert copied[0].enter_effect == source_assignments[0].enter_effect
    assert copied[0].keyframe_tracks == source_assignments[0].keyframe_tracks
    assert copied[1].exit_effect == source_assignments[1].exit_effect

    assert session.undo() == project
    assert not session.is_dirty


def test_copy_scene_animations_rejects_slot_count_mismatch() -> None:
    project = _project()
    source = next(scene for scene in project.scenes if len(scene.asset_ids) == 2)
    target = next(scene for scene in project.scenes if len(scene.asset_ids) == 1)
    assignment = AnimationAssignment(
        source.scene_number,
        source.asset_ids[0],
        enter_effect="Pan",
    )
    project = replace(project, animations=(assignment,))

    with pytest.raises(ValueError, match="Jumlah slot aset"):
        CopySceneAnimations(
            source.scene_number,
            (target.scene_number,),
        ).apply(project)


def test_copy_scene_animations_respects_locked_target_atomically(
    tmp_path: Path,
) -> None:
    project, source, target = _project_with_compatible_target()
    source_assignment = AnimationAssignment(
        source.scene_number,
        source.asset_ids[0],
        enter_effect="Pan",
        exit_effect="Fade",
    )
    locked_target = AnimationAssignment(
        target.scene_number,
        target.asset_ids[0],
        enter_effect="Rise",
        exit_effect="Fade",
        locked=True,
    )
    project = replace(
        project,
        animations=(source_assignment, locked_target),
    )
    session = ProjectSession()
    session.start(project, tmp_path / "wave-f-lock.aavcproj")

    with pytest.raises(ValueError, match="terkunci"):
        session.execute(
            CopySceneAnimations(source.scene_number, (target.scene_number,))
        )

    assert session.current == project
    assert not session.can_undo
    assert not session.is_dirty
