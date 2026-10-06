from pathlib import Path

import pytest

from aavc.application.commands import SetSceneDuration
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import ProjectState
from aavc.persistence.project_repository import ProjectRepository

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project() -> ProjectState:
    return create_project_state(
        title="save-as",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


class SelectiveFailRepository(ProjectRepository):
    def save(self, project: ProjectState, path: str | Path) -> Path:
        if Path(path).name == "failed.aavcproj":
            raise OSError("disk penuh")
        return super().save(project, path)


def test_save_as_switches_active_path_and_future_save_target(tmp_path: Path) -> None:
    original = tmp_path / "original.aavcproj"
    copied = tmp_path / "copied.aavcproj"
    session = ProjectSession()
    session.create(_project(), original)

    session.execute(SetSceneDuration(1, 4.5))
    assert session.is_dirty

    saved = session.save(copied)
    assert saved == copied.resolve()
    assert session.path == copied.resolve()
    assert not session.is_dirty
    assert original.is_file()
    assert copied.is_file()

    session.execute(SetSceneDuration(1, 6.0))
    session.save()

    repository = ProjectRepository()
    copied_state = repository.load(copied)
    original_state = repository.load(original)
    assert copied_state.scenes[0].duration_seconds == 6.0
    assert original_state.scenes[0].duration_seconds == 3.0
    assert not session.is_dirty


def test_failed_save_as_preserves_old_path_and_dirty_state(tmp_path: Path) -> None:
    original = tmp_path / "original.aavcproj"
    failed = tmp_path / "failed.aavcproj"
    session = ProjectSession(SelectiveFailRepository())
    session.create(_project(), original)
    session.execute(SetSceneDuration(1, 4.5))

    with pytest.raises(OSError, match="disk penuh"):
        session.save(failed)

    assert session.path == original.resolve()
    assert session.is_dirty
    assert not failed.exists()
