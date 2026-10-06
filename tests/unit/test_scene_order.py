from dataclasses import replace
from pathlib import Path

import pytest

from aavc.application.commands.scene_order import DeleteScene, DuplicateScene, MoveScene
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment
from aavc.rendering import build_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="scene-order",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _numbers(project):
    return tuple(scene.scene_number for scene in project.scenes)


def test_move_scene_updates_history_timeline_source_and_render_order(tmp_path: Path) -> None:
    project = _project()
    first, second, *_ = project.scenes
    original_order = _numbers(project)
    expected_order = (second.scene_number, first.scene_number, *original_order[2:])

    session = ProjectSession()
    session.start(project, tmp_path / "scene-order.aavcproj")

    moved = session.execute(MoveScene(second.scene_number, -1))
    assert _numbers(moved) == expected_order
    assert session.is_dirty

    render_plan = build_render_plan(moved, tmp_path / "scene-order.mp4")
    assert tuple(scene.scene_number for scene in render_plan.scenes) == expected_order

    undone = session.undo()
    assert _numbers(undone) == original_order
    assert not session.is_dirty

    redone = session.redo()
    assert _numbers(redone) == expected_order
    assert session.is_dirty


def test_move_scene_rejects_boundary_without_history_entry(tmp_path: Path) -> None:
    project = _project()
    first = project.scenes[0]
    session = ProjectSession()
    session.start(project, tmp_path / "scene-order.aavcproj")

    with pytest.raises(ValueError, match="paling atas"):
        session.execute(MoveScene(first.scene_number, -1))

    assert _numbers(session.current) == _numbers(project)
    assert not session.is_dirty
    assert not session.can_undo


def test_move_scene_requires_single_step_offset() -> None:
    project = _project()
    with pytest.raises(ValueError, match="-1 atau 1"):
        MoveScene(project.scenes[0].scene_number, 2).apply(project)


def test_delete_scene_updates_history_render_and_cleans_orphans(tmp_path: Path) -> None:
    project = _project()
    first, second, *_ = project.scenes
    project = replace(
        project,
        animations=(
            AnimationAssignment(first.scene_number, first.asset_ids[0]),
            AnimationAssignment(second.scene_number, second.asset_ids[0]),
        ),
    )
    original_order = _numbers(project)

    session = ProjectSession()
    session.start(project, tmp_path / "scene-delete.aavcproj")

    deleted = session.execute(DeleteScene(first.scene_number))
    assert first.scene_number not in _numbers(deleted)
    assert session.is_dirty

    used_asset_ids = {
        asset_id
        for scene in deleted.scenes
        for asset_id in scene.asset_ids
    }
    assert {binding.asset_id for binding in deleted.bindings} == used_asset_ids
    assert all(
        assignment.scene_number != first.scene_number
        for assignment in deleted.animations
    )

    render_plan = build_render_plan(deleted, tmp_path / "scene-delete.mp4")
    assert tuple(scene.scene_number for scene in render_plan.scenes) == _numbers(deleted)

    undone = session.undo()
    assert _numbers(undone) == original_order
    assert undone.bindings == project.bindings
    assert undone.animations == project.animations
    assert not session.is_dirty

    redone = session.redo()
    assert first.scene_number not in _numbers(redone)
    assert session.is_dirty


def test_delete_scene_keeps_shared_binding() -> None:
    project = _project()
    first, second, *rest = project.scenes
    shared_asset = first.asset_ids[0]
    second_with_shared = replace(
        second,
        asset_ids=(shared_asset,),
        source_quotes=(second.source_quotes[0],),
    )
    project = replace(project, scenes=(first, second_with_shared, *rest))

    deleted = DeleteScene(first.scene_number).apply(project)

    assert any(binding.asset_id == shared_asset for binding in deleted.bindings)


def test_delete_scene_rejects_last_scene_without_history_entry(tmp_path: Path) -> None:
    project = _project()
    only_scene = project.scenes[0]
    project = replace(project, scenes=(only_scene,))
    session = ProjectSession()
    session.start(project, tmp_path / "single-scene.aavcproj")

    with pytest.raises(ValueError, match="terakhir"):
        session.execute(DeleteScene(only_scene.scene_number))

    assert _numbers(session.current) == (only_scene.scene_number,)
    assert not session.is_dirty
    assert not session.can_undo


def test_duplicate_scene_updates_history_render_and_clones_animation(tmp_path: Path) -> None:
    project = _project()
    source = project.scenes[0]
    assignment = AnimationAssignment(
        source.scene_number,
        source.asset_ids[0],
        enter_effect="Pop",
        exit_effect="Fade",
        intensity=0.8,
        locked=True,
    )
    project = replace(project, animations=(assignment,))
    original_order = _numbers(project)
    expected_number = max(original_order) + 1
    expected_order = (
        original_order[0],
        expected_number,
        *original_order[1:],
    )

    session = ProjectSession()
    session.start(project, tmp_path / "scene-duplicate.aavcproj")

    duplicated = session.execute(DuplicateScene(source.scene_number))
    assert _numbers(duplicated) == expected_order
    assert duplicated.bindings == project.bindings
    assert session.is_dirty

    clone = duplicated.scenes[1]
    assert clone.scene_number == expected_number
    assert clone.asset_ids == source.asset_ids
    assert clone.source_quotes == source.source_quotes
    assert clone.duration_seconds == source.duration_seconds

    cloned_assignment = next(
        item for item in duplicated.animations if item.scene_number == expected_number
    )
    assert replace(cloned_assignment, scene_number=source.scene_number) == assignment

    render_plan = build_render_plan(duplicated, tmp_path / "scene-duplicate.mp4")
    assert tuple(scene.scene_number for scene in render_plan.scenes) == expected_order

    undone = session.undo()
    assert undone == project
    assert not session.is_dirty

    redone = session.redo()
    assert _numbers(redone) == expected_order
    assert session.is_dirty


def test_duplicate_scene_rejects_unknown_scene_without_history_entry(tmp_path: Path) -> None:
    project = _project()
    session = ProjectSession()
    session.start(project, tmp_path / "scene-duplicate-missing.aavcproj")

    with pytest.raises(ValueError, match="tidak ditemukan"):
        session.execute(DuplicateScene(999999))

    assert session.current == project
    assert not session.is_dirty
    assert not session.can_undo
