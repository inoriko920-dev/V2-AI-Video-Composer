from pathlib import Path

import pytest

from aavc.application.commands import MoveSceneToIndex
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.rendering import build_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="timeline-drag-reorder",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _numbers(project):
    return tuple(scene.scene_number for scene in project.scenes)


def test_move_scene_to_index_is_one_history_step_and_updates_render_order(
    tmp_path: Path,
) -> None:
    project = _project()
    assert len(project.scenes) >= 2
    source = project.scenes[0]
    original_order = _numbers(project)
    target_index = len(project.scenes) - 1
    expected_order = (*original_order[1:], original_order[0])

    session = ProjectSession()
    session.start(project, tmp_path / "timeline-drag.aavcproj")

    moved = session.execute(MoveSceneToIndex(source.scene_number, target_index))
    assert _numbers(moved) == expected_order
    assert session.is_dirty
    assert session.can_undo

    render_plan = build_render_plan(moved, tmp_path / "timeline-drag.mp4")
    assert tuple(scene.scene_number for scene in render_plan.scenes) == expected_order

    undone = session.undo()
    assert _numbers(undone) == original_order
    assert not session.is_dirty

    redone = session.redo()
    assert _numbers(redone) == expected_order
    assert session.is_dirty


def test_move_scene_to_index_rejects_same_target_without_history_entry(
    tmp_path: Path,
) -> None:
    project = _project()
    scene = project.scenes[0]
    session = ProjectSession()
    session.start(project, tmp_path / "same-target.aavcproj")

    with pytest.raises(ValueError, match="posisi target"):
        session.execute(MoveSceneToIndex(scene.scene_number, 0))

    assert session.current == project
    assert not session.is_dirty
    assert not session.can_undo


def test_move_scene_to_index_rejects_invalid_target_and_unknown_scene() -> None:
    project = _project()

    with pytest.raises(ValueError, match="Posisi target"):
        MoveSceneToIndex(project.scenes[0].scene_number, len(project.scenes)).apply(project)

    with pytest.raises(ValueError, match="tidak ditemukan"):
        MoveSceneToIndex(999999, 0).apply(project)
