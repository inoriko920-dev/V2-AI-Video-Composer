from dataclasses import replace
from pathlib import Path

from aavc.application.services.vertical_slice import create_project_state
from aavc.presentation.timeline_view import build_timeline_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="timeline-live",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_timeline_plan_uses_project_scene_order_and_cumulative_timing() -> None:
    project = _project()
    first, second, *rest = project.scenes
    project = replace(
        project,
        scenes=(
            replace(first, duration_seconds=4.0),
            replace(second, duration_seconds=6.0),
            *rest,
        ),
    )

    plan = build_timeline_plan(project)

    assert plan.segments[0].scene_number == project.scenes[0].scene_number
    assert plan.segments[0].start_seconds == 0.0
    assert plan.segments[0].end_seconds == 4.0
    assert plan.segments[1].start_seconds == 4.0
    assert plan.segments[1].end_seconds == 10.0
    assert plan.segments[1].mode == project.scenes[1].mode


def test_timeline_segment_fractions_match_scene_durations() -> None:
    project = _project()
    project = replace(
        project,
        scenes=(
            replace(project.scenes[0], duration_seconds=2.0),
            replace(project.scenes[1], duration_seconds=6.0),
        ),
    )

    plan = build_timeline_plan(project)

    assert plan.total_duration_seconds == 8.0
    assert plan.segments[0].fraction == 0.25
    assert plan.segments[1].fraction == 0.75
    assert sum(segment.fraction for segment in plan.segments) == 1.0
