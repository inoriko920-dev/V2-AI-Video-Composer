from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation.randomizer import randomize_project_animations
from aavc.application.commands import RandomizeAnimationAssignments
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.dialogs.asset_motion import NATIVE_MOTION_CHOICES
from aavc.presentation.windows.native_motion_window import _stored_animation_seed

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    project = create_project_state(
        title="native-auto-motion",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )
    first = project.scenes[0]
    second = replace(first, scene_number=max(scene.scene_number for scene in project.scenes) + 100)
    return replace(project, scenes=(first, second), animations=(), metadata={})


def test_native_effect_pool_is_deterministic_and_render_backed() -> None:
    project = _project()

    first = randomize_project_animations(
        project,
        seed=42,
        effect_pool=NATIVE_MOTION_CHOICES,
    )
    second = randomize_project_animations(
        project,
        seed=42,
        effect_pool=NATIVE_MOTION_CHOICES,
    )

    assert first.animations == second.animations
    assert first.metadata["animation_seed"] == "42"
    assert first.animations
    assert {
        effect
        for assignment in first.animations
        for effect in (assignment.enter_effect, assignment.exit_effect)
    } <= set(NATIVE_MOTION_CHOICES)


def test_selected_scene_randomization_preserves_other_scene_assignment() -> None:
    project = _project()
    first, second = project.scenes
    preserved = AnimationAssignment(
        scene_number=second.scene_number,
        asset_id=second.asset_ids[0],
        enter_effect="Fade",
        exit_effect="Pop",
        intensity=0.7,
    )
    project = replace(project, animations=(preserved,))

    updated = randomize_project_animations(
        project,
        seed=9,
        scene_numbers=(first.scene_number,),
        effect_pool=NATIVE_MOTION_CHOICES,
    )

    other = next(
        assignment
        for assignment in updated.animations
        if assignment.scene_number == second.scene_number
    )
    assert other == preserved
    selected = [
        assignment
        for assignment in updated.animations
        if assignment.scene_number == first.scene_number
    ]
    assert selected
    assert all(
        assignment.enter_effect in NATIVE_MOTION_CHOICES
        and assignment.exit_effect in NATIVE_MOTION_CHOICES
        for assignment in selected
    )


def test_locked_assignment_survives_native_randomization() -> None:
    project = _project()
    first = project.scenes[0]
    locked = AnimationAssignment(
        scene_number=first.scene_number,
        asset_id=first.asset_ids[0],
        enter_effect="Fade",
        exit_effect="Pop",
        intensity=0.5,
        locked=True,
    )
    project = replace(project, animations=(locked,))

    updated = randomize_project_animations(
        project,
        seed=5,
        scene_numbers=(first.scene_number,),
        effect_pool=NATIVE_MOTION_CHOICES,
    )

    target = next(
        assignment
        for assignment in updated.animations
        if assignment.scene_number == first.scene_number
        and assignment.asset_id == first.asset_ids[0]
    )
    assert target == locked


def test_auto_motion_is_one_history_entry_and_undo_restores_project(tmp_path: Path) -> None:
    project = _project()
    session = ProjectSession()
    session.start(project, tmp_path / "auto-motion.aavcproj")

    updated = session.execute(
        RandomizeAnimationAssignments(
            seed=17,
            effect_pool=NATIVE_MOTION_CHOICES,
        )
    )

    assert session.is_dirty
    assert session.can_undo
    assert updated.animations
    assert updated.metadata["animation_seed"] == "17"

    restored = session.undo()
    assert restored.animations == project.animations
    assert restored.metadata == project.metadata
    assert not session.can_undo


def test_invalid_effect_pool_and_unknown_scene_are_rejected() -> None:
    project = _project()

    with pytest.raises(ValueError, match="minimal dua"):
        randomize_project_animations(project, seed=1, effect_pool=("Rise",))

    with pytest.raises(ValueError):
        randomize_project_animations(
            project,
            seed=1,
            effect_pool=("Rise", "Tidak Ada"),
        )

    command = RandomizeAnimationAssignments(
        seed=1,
        scene_numbers=(999999,),
        effect_pool=NATIVE_MOTION_CHOICES,
    )
    with pytest.raises(ValueError, match="Scene tidak ditemukan"):
        command.apply(project)


def test_stored_seed_is_resilient_and_qt_safe() -> None:
    assert _stored_animation_seed({}) == 1
    assert _stored_animation_seed({"animation_seed": "12"}) == 12
    assert _stored_animation_seed({"animation_seed": "not-a-number"}) == 1
    assert _stored_animation_seed({"animation_seed": "999999999999"}) == 2147483647
