from pathlib import Path

import pytest

from aavc.application.commands import SetProjectTitle
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.persistence.project_repository import ProjectRepository

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="Nama Lama",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_project_rename_uses_history_and_keeps_same_path(tmp_path: Path) -> None:
    path = tmp_path / "project-file.aavcproj"
    session = ProjectSession()
    session.create(_project(), path)

    renamed = session.execute(SetProjectTitle("  Nama Baru  "))
    assert renamed.title == "Nama Baru"
    assert session.path == path.resolve()
    assert session.is_dirty

    undone = session.undo()
    assert undone.title == "Nama Lama"
    assert not session.is_dirty

    redone = session.redo()
    assert redone.title == "Nama Baru"
    assert session.is_dirty

    saved = session.save()
    assert saved == path.resolve()
    assert session.path == path.resolve()
    assert not session.is_dirty
    assert ProjectRepository().load(path).title == "Nama Baru"


def test_project_rename_rejects_invalid_title_without_history(tmp_path: Path) -> None:
    path = tmp_path / "project-file.aavcproj"
    session = ProjectSession()
    session.create(_project(), path)

    with pytest.raises(ValueError, match="tidak boleh kosong"):
        session.execute(SetProjectTitle("   "))
    assert not session.is_dirty
    assert not session.can_undo

    with pytest.raises(ValueError, match="maksimal 200"):
        session.execute(SetProjectTitle("x" * 201))
    assert not session.is_dirty
    assert not session.can_undo
