from pathlib import Path

from aavc.application.commands import RelinkAsset, SetAnimationAssignment, SetSceneDuration
from aavc.application.services.history import ProjectHistory
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="demo",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_history_undo_redo_changes_model_not_only_ui() -> None:
    history = ProjectHistory(_project())
    history.execute(SetSceneDuration(1, 4.5))
    assert history.current.scenes[0].duration_seconds == 4.5
    history.undo()
    assert history.current.scenes[0].duration_seconds == 3.0
    history.redo()
    assert history.current.scenes[0].duration_seconds == 4.5


def test_relink_asset_validates_file() -> None:
    history = ProjectHistory(_project())
    result = history.execute(RelinkAsset("A001", str(FIXTURE / "assets" / "A001.png")))
    assert result.bindings[0].status == "READY"


def test_animation_command_validates_registry() -> None:
    history = ProjectHistory(_project())
    assignment = AnimationAssignment(1, "A001", "Fade", "Pop", 1.0, True)
    result = history.execute(SetAnimationAssignment(assignment))
    assert result.animations == (assignment,)
