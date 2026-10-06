import json
from pathlib import Path

import pytest

from aavc.application.commands import SetSceneDuration
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import ProjectState
from aavc.persistence.project_repository import ProjectRepository

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project(title: str = "demo-session") -> ProjectState:
    return create_project_state(
        title=title,
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


class FailingSaveRepository(ProjectRepository):
    def save(self, project: ProjectState, path: str | Path) -> Path:
        raise OSError("disk penuh")


def test_session_start_save_and_reopen(tmp_path: Path) -> None:
    destination = tmp_path / "demo.aavcproj"
    session = ProjectSession()
    session.start(_project(), destination)
    assert not session.is_dirty

    saved = session.save()
    assert saved == destination.resolve()
    assert destination.is_file()
    assert not session.is_dirty

    reopened = ProjectSession()
    project = reopened.open(destination)
    assert project.title == "demo-session"
    assert reopened.current == project
    assert reopened.path == destination.resolve()
    assert not reopened.is_dirty


def test_create_persists_project_before_activating_session(tmp_path: Path) -> None:
    destination = tmp_path / "created.aavcproj"
    project = _project("project-baru")
    session = ProjectSession()

    created = session.create(project, destination)

    assert destination.is_file()
    assert created == project
    assert session.current == project
    assert session.path == destination.resolve()
    assert not session.is_dirty


def test_failed_create_preserves_previous_session(tmp_path: Path) -> None:
    previous = _project("project-lama")
    previous_path = tmp_path / "previous.aavcproj"
    session = ProjectSession(FailingSaveRepository())
    session.start(previous, previous_path)

    with pytest.raises(OSError, match="disk penuh"):
        session.create(_project("project-baru"), tmp_path / "new.aavcproj")

    assert session.current == previous
    assert session.path == previous_path.resolve()
    assert not session.is_dirty


def test_session_execute_undo_redo_uses_project_history() -> None:
    session = ProjectSession()
    session.start(_project())
    assert session.is_dirty

    changed = session.execute(SetSceneDuration(1, 4.5))
    assert changed.scenes[0].duration_seconds == 4.5
    assert session.can_undo
    assert session.is_dirty

    undone = session.undo()
    assert undone.scenes[0].duration_seconds == 3.0
    assert session.can_redo
    assert session.is_dirty

    redone = session.redo()
    assert redone.scenes[0].duration_seconds == 4.5
    assert session.is_dirty


def test_dirty_state_tracks_saved_baseline_through_undo_redo(tmp_path: Path) -> None:
    destination = tmp_path / "dirty.aavcproj"
    session = ProjectSession()
    session.create(_project(), destination)
    assert not session.is_dirty

    session.execute(SetSceneDuration(1, 4.5))
    assert session.is_dirty

    session.undo()
    assert not session.is_dirty

    session.redo()
    assert session.is_dirty

    session.save()
    assert not session.is_dirty

    session.undo()
    assert session.is_dirty

    session.redo()
    assert not session.is_dirty


def test_failed_save_does_not_advance_saved_baseline(tmp_path: Path) -> None:
    destination = tmp_path / "failing.aavcproj"
    session = ProjectSession(FailingSaveRepository())
    session.start(_project(), destination)
    session.execute(SetSceneDuration(1, 4.5))
    assert session.is_dirty

    with pytest.raises(OSError, match="disk penuh"):
        session.save()

    assert session.is_dirty
    assert session.current is not None
    assert session.current.scenes[0].duration_seconds == 4.5


def test_failed_open_preserves_existing_session(tmp_path: Path) -> None:
    destination = tmp_path / "good.aavcproj"
    session = ProjectSession()
    session.start(_project(), destination)
    session.save()
    session.open(destination)
    previous_project = session.current
    previous_path = session.path

    broken = tmp_path / "broken.aavcproj"
    broken.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ValueError):
        session.open(broken)

    assert session.current == previous_project
    assert session.path == previous_path
    assert not session.is_dirty


def test_save_requires_active_project() -> None:
    session = ProjectSession()
    assert not session.is_dirty
    with pytest.raises(ValueError, match="Tidak ada proyek aktif"):
        session.save()



def test_future_schema_open_preserves_existing_session(tmp_path: Path) -> None:
    previous = _project("project-lama")
    previous_path = tmp_path / "previous.aavcproj"
    session = ProjectSession()
    session.create(previous, previous_path)

    future = tmp_path / "future.aavcproj"
    payload = previous.to_dict()
    payload["schema_version"] = 99
    future.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="lebih baru"):
        session.open(future)

    assert session.current == previous
    assert session.path == previous_path.resolve()
    assert not session.is_dirty
