"""W06-D: UI-neutral recovery transactions bound to the existing editor shell.

The original editor pages/menu/timeline remain unchanged. A parent-owned Qt
timer observes canonical ProjectSession changes and drains completed one-writer
snapshot tasks. All widgets stay on Qt's main thread; the worker only does IO.
"""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path
from typing import Any

from aavc.application.services.recovery_coordinator import RecoveryCoordinator, SnapshotRequest
from aavc.application.services.recovery_transactions import (
    GuardRequired,
    RecoveryCommitPartial,
    RecoveryTransactions,
)
from aavc.bootstrap.composition_root import FoundationServices
from aavc.domain.errors import AAVCError
from aavc.persistence.snapshot_provenance import ProvenanceStore, RecoveryRaceChanged
from aavc.presentation.dialogs.recovery_choice import choose_recovery
from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.background_work_window import BackgroundWorkMainWindow


class RecoveryMainWindow(BackgroundWorkMainWindow):
    """Only three approved recovery dialogs added over existing frozen shell."""

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        self._recovery_clock: Any = None
        self._recovery_coordinator = RecoveryCoordinator()
        self._recovery_store = ProvenanceStore()
        self._recovery_transactions = RecoveryTransactions(
            services.project_session,
            store=self._recovery_store,
            coordinator=self._recovery_coordinator,
        )
        self._recovery_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="aavc-recovery-snapshot"
        )
        self._recovery_future: Future[bool] | None = None
        self._recovery_request: SnapshotRequest | None = None
        self._recovery_is_shutdown = False
        self._recovery_status = ""
        self._recovery_modal_active = False
        super().__init__(services, initial_state=initial_state)

        timer = QTimer(self.window)
        timer.setObjectName("AAVCRecoveryScheduler")
        timer.setInterval(250)
        timer.timeout.connect(self._recovery_poll)
        self._recovery_timer = timer
        timer.start()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.shutdown_recovery)

    def _background_busy(self) -> bool:
        recovery_busy = (
            self._recovery_future is not None and not self._recovery_future.done()
        )
        return recovery_busy or super()._background_busy()

    def _status(self, message: str) -> None:
        if self._recovery_status != message:
            self._recovery_status = message
            self.window.statusBar().showMessage(message, 5000)

    def _write_snapshot_task(self, request: SnapshotRequest, baseline: str) -> bool:
        """Worker thread: no access to QWidget/QObject and no Qt callbacks."""
        with self._recovery_store.locked_transaction():
            session = self.services.project_session
            if (
                self._recovery_coordinator.epoch != request.epoch
                or session.path != request.path
                or session.saved_disk_sha256 != baseline
                or not session.is_dirty
            ):
                return False
            self._recovery_store.write_snapshot(
                request.project_state,
                request.path,
                saved_baseline_sha256=baseline,
            )
            return True

    def _drain_snapshot(self) -> bool:
        """Qt thread only: apply worker result to canonical scheduler."""
        future = self._recovery_future
        request = self._recovery_request
        if future is None or not future.done() or request is None:
            return future is None
        self._recovery_future = None
        self._recovery_request = None
        try:
            success = future.result()
        except (OSError, ValueError, RuntimeError):
            success = False
        accepted = self._recovery_coordinator.complete(request, success=success)
        if accepted:
            if success:
                self._status("Cadangan otomatis dibuat")
            else:
                self._status("Cadangan otomatis gagal — simpan manual tersedia")
        return True

    def _recovery_poll(self) -> None:
        """Timer callback is bounded and does not perform filesystem IO."""
        if self._recovery_is_shutdown:
            return
        if not self._drain_snapshot():
            # Observe new canonical edits while the serial worker owns the slot.
            self._recovery_coordinator.tick(self.services.project_session)
            return

        session = self.services.project_session
        request = self._recovery_coordinator.tick(session)
        if request is None:
            if session.is_dirty and session.path is None:
                self._status("Simpan proyek untuk mengaktifkan cadangan otomatis")
            elif session.is_dirty and self._recovery_coordinator.next_due_at is not None:
                self._status("Cadangan otomatis menunggu jeda")
            return

        baseline = session.saved_disk_sha256
        if baseline is None:
            self._recovery_coordinator.complete(request, success=False)
            self._status("Cadangan otomatis gagal — simpan manual tersedia")
            return

        self._recovery_request = request
        self._status("Membuat cadangan otomatis…")
        try:
            self._recovery_future = self._recovery_executor.submit(
                self._write_snapshot_task, request, baseline
            )
        except RuntimeError:
            self._recovery_request = None
            self._recovery_coordinator.complete(request, success=False)
            self._status("Cadangan otomatis gagal — simpan manual tersedia")

    def _finish_active_snapshot(self) -> bool:
        """Before a manual transaction, wait for the *one* old writer.

        Timeout is fail-closed: no Save/Open is attempted while a stale worker
        might still have an in-progress filesystem operation.
        """
        future = self._recovery_future
        if future is None:
            return True
        try:
            future.result(timeout=10)
        except FutureTimeout:
            self._status("Cadangan otomatis masih berjalan; coba lagi setelah selesai")
            return False
        except (OSError, ValueError, RuntimeError):
            pass
        self._drain_snapshot()
        return True

    def _show_recovery_failure(self, partial: bool = False) -> None:
        from PySide6.QtWidgets import QMessageBox

        box = QMessageBox(self.window)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Pemulihan belum selesai")
        box.setText(
            "Proyek pada disk mungkin sudah berubah. Simpan berkas cadangan "
            "dan periksa sebelum melanjutkan."
            if partial
            else "Pemulihan belum selesai. Jangan hapus berkas cadangan."
        )
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()

    def _refresh_after_open(self, project: Any) -> None:
        self._selected_scene_number = (
            project.scenes[0].scene_number if project.scenes else None
        )
        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.show_route(UiRoute.EDITOR)

    def open_project(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        chosen, _ = QFileDialog.getOpenFileName(
            self.window, "Buka Proyek AAVC", "",
            "AAVC Project (*.aavcproj);;Semua File (*.*)",
        )
        if not chosen:
            return
        if not self._confirm_unsaved_changes("membuka project lain"):
            return
        if not self._finish_active_snapshot():
            return
        self._recovery_modal_active = True
        self._recovery_coordinator.set_paused(True)
        try:
            plan = self._recovery_transactions.probe_open(
                chosen, guard_approved=True,
            )
            choice = choose_recovery(
                self.window, plan.candidate.status, Path(chosen).name
            )
            if choice == "cancel":
                self._recovery_transactions.cancel(plan)
                return
            if choice == "restore":
                outcome = self._recovery_transactions.restore(
                    plan, confirm_conflict=(plan.candidate.status == "UNCERTAIN"),
                )
                self._status("Cadangan proyek berhasil dipulihkan")
                del outcome
            else:
                self._recovery_transactions.use_saved(plan)
                self._status("Proyek tersimpan berhasil dibuka")
            project = self.services.project_session.current
            if project is not None:
                self._refresh_after_open(project)
        except RecoveryCommitPartial:
            self._show_recovery_failure(partial=True)
        except (GuardRequired, RecoveryRaceChanged):
            self._status("Data proyek berubah. Periksa ulang.")
            self._show_recovery_failure()
        except (AAVCError, OSError, ValueError, KeyError, TypeError):
            self._show_recovery_failure()
        finally:
            self._recovery_coordinator.set_paused(False)
            self._recovery_modal_active = False

    def save_project(self) -> None:
        if not self._finish_active_snapshot():
            return
        self._recovery_coordinator.set_paused(True)
        try:
            self._recovery_transactions.save()
        except RecoveryCommitPartial:
            self._show_recovery_failure(partial=True)
        except (AAVCError, OSError, ValueError, RecoveryRaceChanged):
            self._show_recovery_failure()
        else:
            self._refresh_window_title()
            self._status("Proyek disimpan")
        finally:
            self._recovery_coordinator.set_paused(False)

    def save_project_as(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Simpan Sebagai tidak tersedia", "Buat atau buka proyek terlebih dahulu."
            )
            return
        current = session.path
        default = (
            str(current)
            if current is not None
            else str(Path(project.source_docx).resolve().parent / f"{project.title}.aavcproj")
        )
        chosen, _ = QFileDialog.getSaveFileName(
            self.window, "Simpan Proyek AAVC Sebagai", default,
            "AAVC Project (*.aavcproj)",
        )
        if not chosen:
            return
        from aavc.presentation.windows.main_window import ensure_project_suffix

        if not self._finish_active_snapshot():
            return
        self._recovery_coordinator.set_paused(True)
        try:
            self._recovery_transactions.save_as(ensure_project_suffix(chosen))
        except RecoveryCommitPartial:
            self._show_recovery_failure(partial=True)
        except (AAVCError, OSError, ValueError, RecoveryRaceChanged):
            self._show_recovery_failure()
        else:
            self._refresh_window_title()
            self._status("Proyek disimpan sebagai")
        finally:
            self._recovery_coordinator.set_paused(False)

    def create_project_from_docx(self, scene_docx: str) -> None:
        if not self._finish_active_snapshot():
            return
        self._recovery_coordinator.set_paused(True)
        try:
            super().create_project_from_docx(scene_docx)
            # Create may be canceled. Reset is always safe: the coordinator
            # will reacquire the canonical baseline on its next observation.
            self._recovery_coordinator.reset_session()
        finally:
            self._recovery_coordinator.set_paused(False)

    def shutdown_recovery(self) -> None:
        if self._recovery_is_shutdown:
            return
        self._recovery_is_shutdown = True
        self._recovery_timer.stop()
        self._recovery_coordinator.close()
        self._recovery_executor.shutdown(wait=False, cancel_futures=True)


def create_recovery_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> RecoveryMainWindow:
    return RecoveryMainWindow(services, initial_state=initial_state)
