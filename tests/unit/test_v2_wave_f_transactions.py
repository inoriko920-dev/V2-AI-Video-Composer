from __future__ import annotations

from pathlib import Path

import pytest

from aavc.application.commands import (
    ProjectTransaction,
    SetSceneDuration,
    SetSceneDurationsBatch,
)
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="wave-f-transaction",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_execute_many_is_one_undo_redo_history_entry(tmp_path: Path) -> None:
    project = _project()
    first, second, *_ = project.scenes
    session = ProjectSession()
    session.start(project, tmp_path / "wave-f.aavcproj")

    changed = session.execute_many(
        (
            SetSceneDuration(first.scene_number, 4.25),
            SetSceneDuration(second.scene_number, 5.5),
        ),
        description="Ubah dua durasi Scene",
    )

    assert changed.scenes[0].duration_seconds == 4.25
    assert changed.scenes[1].duration_seconds == 5.5
    assert session.can_undo

    undone = session.undo()
    assert undone == project
    assert not session.is_dirty
    assert not session.can_undo
    assert session.can_redo

    redone = session.redo()
    assert redone.scenes[0].duration_seconds == 4.25
    assert redone.scenes[1].duration_seconds == 5.5


def test_failed_transaction_is_atomic_and_does_not_enter_history(tmp_path: Path) -> None:
    project = _project()
    first = project.scenes[0]
    session = ProjectSession()
    session.start(project, tmp_path / "wave-f-atomic.aavcproj")

    with pytest.raises(ValueError, match="tidak ditemukan"):
        session.execute(
            ProjectTransaction(
                (
                    SetSceneDuration(first.scene_number, 4.5),
                    SetSceneDuration(999999, 2.0),
                ),
                "Transaksi gagal",
            )
        )

    assert session.current == project
    assert not session.is_dirty
    assert not session.can_undo


def test_batch_scene_duration_updates_validate_before_mutation(tmp_path: Path) -> None:
    project = _project()
    first, second, *_ = project.scenes
    session = ProjectSession()
    session.start(project, tmp_path / "wave-f-batch.aavcproj")

    changed = session.execute(
        SetSceneDurationsBatch(
            (
                (first.scene_number, 1.25),
                (second.scene_number, 6.75),
            )
        )
    )

    assert changed.scenes[0].duration_seconds == 1.25
    assert changed.scenes[1].duration_seconds == 6.75
    assert session.undo() == project

    with pytest.raises(ValueError, match="muncul dua kali"):
        SetSceneDurationsBatch(
            (
                (first.scene_number, 2.0),
                (first.scene_number, 3.0),
            )
        ).apply(project)

    with pytest.raises(ValueError, match="finite"):
        SetSceneDurationsBatch(((first.scene_number, float("inf")),)).apply(project)
