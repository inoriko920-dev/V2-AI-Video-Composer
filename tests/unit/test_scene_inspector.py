from pathlib import Path

from aavc.application.services.vertical_slice import create_project_state
from aavc.presentation.scene_inspector import (
    build_scene_inspector_view,
    scene_index_for_number,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="scene-inspector",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_scene_inspector_maps_selected_scene() -> None:
    project = _project()
    target = project.scenes[-1]

    view = build_scene_inspector_view(project, target.scene_number)

    assert view.scene_number == target.scene_number
    assert view.mode == target.mode
    assert view.asset_ids == target.asset_ids
    assert view.duration_seconds == target.duration_seconds


def test_scene_index_preserves_selection_when_scene_exists() -> None:
    project = _project()
    target = project.scenes[-1]

    assert scene_index_for_number(project, target.scene_number) == len(project.scenes) - 1


def test_scene_index_falls_back_to_first_scene() -> None:
    project = _project()

    assert scene_index_for_number(project, None) == 0
    assert scene_index_for_number(project, 9999) == 0
