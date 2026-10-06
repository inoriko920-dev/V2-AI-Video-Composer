from pathlib import Path

import pytest

from aavc.application.commands import SetSceneDuration
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.presentation.timeline_view import build_timeline_plan
from aavc.rendering import build_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="timeline-resize-duration",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_timeline_resize_duration_is_one_history_step_and_updates_plans(
    tmp_path: Path,
) -> None:
    project = _project()
    scene = project.scenes[0]
    original_duration = scene.duration_seconds
    resized_duration = round(original_duration + 1.25, 3)

    session = ProjectSession()
    session.start(project, tmp_path / "timeline-resize.aavcproj")

    resized = session.execute(SetSceneDuration(scene.scene_number, resized_duration))
    assert resized.scenes[0].duration_seconds == resized_duration
    assert session.is_dirty
    assert session.can_undo

    timeline = build_timeline_plan(resized)
    assert timeline.segments[0].duration_seconds == resized_duration
    expected_total = (
        build_timeline_plan(project).total_duration_seconds
        - original_duration
        + resized_duration
    )
    assert timeline.total_duration_seconds == pytest.approx(expected_total)

    render_plan = build_render_plan(resized, tmp_path / "timeline-resize.mp4")
    assert render_plan.scenes[0].duration_seconds == resized_duration

    undone = session.undo()
    assert undone.scenes[0].duration_seconds == original_duration
    assert not session.is_dirty

    redone = session.redo()
    assert redone.scenes[0].duration_seconds == resized_duration
    assert session.is_dirty
