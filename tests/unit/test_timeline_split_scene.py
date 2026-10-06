from dataclasses import replace
from pathlib import Path

import pytest

from aavc.application.commands import SplitScene
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.timeline_view import build_timeline_plan
from aavc.presentation.windows.native_motion_preview_window import (
    scene_split_seconds_from_slider,
)
from aavc.rendering import build_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="timeline-split-scene",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_scene_split_seconds_from_slider_maps_scene_local_playhead() -> None:
    assert scene_split_seconds_from_slider(0, 1000, 8.0) == 0.0
    assert scene_split_seconds_from_slider(250, 1000, 8.0) == 2.0
    assert scene_split_seconds_from_slider(500, 1000, 8.0) == 4.0
    assert scene_split_seconds_from_slider(1000, 1000, 8.0) == 8.0


def test_split_scene_preserves_total_assets_animation_and_history(tmp_path: Path) -> None:
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
    original_total = build_timeline_plan(project).total_duration_seconds
    split_seconds = round(source.duration_seconds * 0.4, 3)
    expected_new_number = max(scene.scene_number for scene in project.scenes) + 1

    session = ProjectSession()
    session.start(project, tmp_path / "split-scene.aavcproj")

    split = session.execute(SplitScene(source.scene_number, split_seconds))
    assert len(split.scenes) == len(project.scenes) + 1
    first = split.scenes[0]
    second = split.scenes[1]
    assert first.scene_number == source.scene_number
    assert second.scene_number == expected_new_number
    assert first.duration_seconds == split_seconds
    assert second.duration_seconds == pytest.approx(source.duration_seconds - split_seconds)
    assert first.asset_ids == source.asset_ids
    assert second.asset_ids == source.asset_ids
    assert first.source_quotes == source.source_quotes
    assert second.source_quotes == source.source_quotes
    assert split.bindings == project.bindings

    cloned = next(
        item for item in split.animations if item.scene_number == expected_new_number
    )
    assert replace(cloned, scene_number=source.scene_number) == assignment

    timeline = build_timeline_plan(split)
    assert timeline.total_duration_seconds == pytest.approx(original_total)
    render_plan = build_render_plan(split, tmp_path / "split-scene.mp4")
    assert render_plan.duration_seconds == pytest.approx(original_total)
    assert render_plan.scenes[0].scene_number == source.scene_number
    assert render_plan.scenes[1].scene_number == expected_new_number

    undone = session.undo()
    assert undone == project
    assert not session.is_dirty

    redone = session.redo()
    assert len(redone.scenes) == len(project.scenes) + 1
    assert session.is_dirty


def test_split_scene_rejects_playhead_at_scene_boundaries_without_history(
    tmp_path: Path,
) -> None:
    project = _project()
    source = project.scenes[0]
    session = ProjectSession()
    session.start(project, tmp_path / "split-boundary.aavcproj")

    with pytest.raises(ValueError, match="awal Scene"):
        session.execute(SplitScene(source.scene_number, 0.0))
    assert not session.can_undo
    assert not session.is_dirty

    with pytest.raises(ValueError, match="akhir Scene"):
        session.execute(SplitScene(source.scene_number, source.duration_seconds))
    assert not session.can_undo
    assert not session.is_dirty


def test_split_scene_rejects_unknown_scene() -> None:
    project = _project()

    with pytest.raises(ValueError, match="tidak ditemukan"):
        SplitScene(999999, 1.0).apply(project)
