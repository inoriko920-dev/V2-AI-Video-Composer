"""W06-D: accepted recovery UI, Qt lifetime, and transaction routing.

Synthetic-only. QT_QPA_PLATFORM=offscreen in CI. All candidate writes in tmp_path.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from aavc.application.commands import SetSceneDuration
from aavc.bootstrap.composition_root import build_foundation_services
from aavc.domain.project.models import AssetBinding, ProjectState, Scene
from aavc.persistence.serializer import load_project, save_project
from aavc.persistence.snapshot_provenance import ProvenanceStore
from aavc.presentation.dialogs.recovery_choice import RecoveryChoiceDialog, choose_recovery
from aavc.presentation.windows.recovery_main_window import RecoveryMainWindow


@pytest.fixture(scope="module")
def app() -> QApplication:
    existing = QApplication.instance()
    return existing if isinstance(existing, QApplication) else QApplication([])


def project(title: str = "Suez") -> ProjectState:
    return ProjectState(
        schema_version=3, title=title, source_docx="synthetic.docx",
        asset_directory="synthetic-assets",
        scenes=(Scene(1, ("asset",), ("fixture",), 3.0),),
        bindings=(), metadata={"fixture": "W06-D"},
    )


def target_with_snapshot(tmp_path: Path) -> tuple[Path, ProvenanceStore]:
    path = save_project(project(), tmp_path / "suez.aavcproj")
    store = ProvenanceStore()
    edited = replace(project(), title="Recovered Suez")
    store.write_snapshot(edited, path, saved_baseline_sha256=sha256(path.read_bytes()).hexdigest())
    return path, store


def test_ui_01_approved_normal_choice_and_safe_default(app: QApplication) -> None:
    dialog = RecoveryChoiceDialog("VERIFIED", "suez.aavcproj")
    assert dialog.windowTitle() == "Cadangan Proyek Ditemukan"
    assert dialog.restore_button.text() == "Pulihkan Cadangan"
    assert dialog.saved_button.text() == "Gunakan Proyek Tersimpan"
    assert dialog.cancel_button.text() == "Batal"
    assert dialog.cancel_button.isDefault()
    assert dialog.result_action == "cancel"
    dialog.reject()
    assert dialog.result_action == "cancel"
    dialog.deleteLater()


def test_ui_02_conflict_requires_second_click_same_modal(app: QApplication) -> None:
    dialog = RecoveryChoiceDialog("UNCERTAIN", "suez.aavcproj")
    assert dialog.windowTitle() == "Cadangan Perlu Diperiksa"
    assert dialog.restore_button.text() == "Periksa dan Pulihkan"
    dialog.restore_button.click()
    assert dialog.conflict_confirmation_visible
    assert dialog.restore_button.text() == "Ya, Pulihkan Cadangan"
    assert not dialog.saved_button.isVisible()
    assert dialog.result_action == "cancel"
    dialog.restore_button.click()
    assert dialog.result_action == "restore"
    dialog.deleteLater()


def test_ui_03_invalid_offer_only_saved_or_cancel(
    app: QApplication, monkeypatch: pytest.MonkeyPatch,
) -> None:
    checked: list[tuple[str, list[str]]] = []
    original_exec = QMessageBox.exec

    def observe(self: QMessageBox) -> int:
        buttons = [b.text() for b in self.buttons()]
        checked.append((self.windowTitle(), buttons))
        assert "Pulihkan Cadangan" not in buttons
        for button in self.buttons():
            if button.text() == "Batal":
                button.click()
                break
        return int(QMessageBox.StandardButton.Cancel)

    monkeypatch.setattr(QMessageBox, "exec", observe)
    assert choose_recovery(None, "INVALID", "suez.aavcproj") == "cancel"
    assert checked == [("Cadangan Tidak Dapat Dibaca", ["Buka Proyek Tersimpan", "Batal"])]
    monkeypatch.setattr(QMessageBox, "exec", original_exec)


def test_qt_01_recovery_window_preserves_old_shell(app: QApplication) -> None:
    services = build_foundation_services()
    window = RecoveryMainWindow(services, initial_state="UI-013")
    assert window.window.objectName() == "AAVCMainWindow"
    assert window._recovery_timer.parent() is window.window
    assert window._recovery_timer.isActive()
    assert window._recovery_timer.interval() <= 1000
    window.shutdown_recovery()
    assert not window._recovery_timer.isActive()
    window.window.deleteLater()
    services.jobs.shutdown(wait=False)


def test_qt_02_open_cancel_preserves_session_disk_and_candidate(
    app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    target, store = target_with_snapshot(tmp_path)
    services = build_foundation_services()
    services.project_session.create(project("Active"), tmp_path / "active.aavcproj")
    window = RecoveryMainWindow(services, initial_state="UI-002")
    current = services.project_session.current
    old_path = services.project_session.path
    disk = target.read_bytes()
    snap = store.snapshot_path(target).read_bytes()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(target), ""))
    monkeypatch.setattr(
        "aavc.presentation.windows.recovery_main_window.choose_recovery",
        lambda *_a: "cancel",
    )
    window.open_project()
    assert services.project_session.path == old_path
    assert services.project_session.current == current
    assert target.read_bytes() == disk
    assert store.snapshot_path(target).read_bytes() == snap
    window.shutdown_recovery()
    window.window.deleteLater()
    services.jobs.shutdown(wait=False)


def test_qt_03_verified_restore_requires_user_decision(
    app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    target, store = target_with_snapshot(tmp_path)
    old_disk = target.read_bytes()
    services = build_foundation_services()
    window = RecoveryMainWindow(services)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(target), ""))
    monkeypatch.setattr(
        "aavc.presentation.windows.recovery_main_window.choose_recovery",
        lambda *_a: "restore",
    )
    window.open_project()
    assert services.project_session.path == target.resolve()
    assert services.project_session.current is not None
    assert services.project_session.current.title == "Recovered Suez"
    assert not services.project_session.is_dirty
    assert target.read_bytes() != old_disk
    backups = list(tmp_path.glob("*.pre-recovery.bak"))
    assert len(backups) == 1 and backups[0].read_bytes() == old_disk
    window.shutdown_recovery()
    window.window.deleteLater()
    services.jobs.shutdown(wait=False)


def test_qt_04_poll_autosave_is_nonblocking_and_does_not_clean(
    app: QApplication, tmp_path: Path,
) -> None:
    services = build_foundation_services()
    services.project_session.create(project(), tmp_path / "edited.aavcproj")
    clock = [0.0]
    window = RecoveryMainWindow(services)
    window._recovery_clock = lambda: clock[0]
    # Test directly swaps the clock before first observed edit.
    window._recovery_coordinator._clock = window._recovery_clock
    services.project_session.execute(SetSceneDuration(1, 5))
    window._recovery_poll()
    clock[0] = 20.0
    window._recovery_poll()
    task = window._recovery_future
    assert task is not None
    assert services.project_session.is_dirty
    task.result(timeout=15)
    window._recovery_poll()
    path = services.project_session.path
    assert path is not None
    assert ProvenanceStore().inspect(path).status == "VERIFIED"
    assert services.project_session.is_dirty and services.project_session.can_undo
    window.shutdown_recovery()
    window.window.deleteLater()
    services.jobs.shutdown(wait=False)


def test_qt_05_manual_save_fences_stale_snapshot_and_clears_dirty(
    app: QApplication, tmp_path: Path,
) -> None:
    services = build_foundation_services()
    services.project_session.create(project(), tmp_path / "edited.aavcproj")
    window = RecoveryMainWindow(services)
    services.project_session.execute(SetSceneDuration(1, 5))
    window.save_project()
    assert not services.project_session.is_dirty
    assert services.project_session.path is not None
    assert load_project(services.project_session.path).scenes[0].duration_seconds == 5
    window.shutdown_recovery()
    window.window.deleteLater()
    services.jobs.shutdown(wait=False)
