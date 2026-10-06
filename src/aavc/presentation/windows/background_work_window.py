from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aavc.application.commands import SetAnimationAssignmentsBatch
from aavc.application.services.ai_animation_service import (
    DEFAULT_GEMINI_ANIMATION_MODEL,
    AiAnimationPlanResult,
    ai_run_status_text,
    plan_gemini_native_motion_detailed,
)
from aavc.application.services.export_service import ExportOptions, render_project
from aavc.application.services.selection_export_service import render_project_selection
from aavc.bootstrap.composition_root import FoundationServices
from aavc.jobs import CancellationToken
from aavc.jobs.background_call import BackgroundCall
from aavc.presentation.dialogs.asset_motion import NATIVE_MOTION_CHOICES
from aavc.presentation.windows.ai_menu_window import configured_gemini_slots
from aavc.presentation.windows.ai_native_motion_window import AiNativeMotionMainWindow


class BackgroundWorkMainWindow(AiNativeMotionMainWindow):
    """Keep blocking provider/render work outside the Qt GUI thread."""

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)
        ai_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "AI":
                ai_menu = menu_action.menu()
                break
        if ai_menu is None:
            return
        ai_menu.addSeparator()
        cancel_action = action_type("Batalkan Pekerjaan Berjalan", self.window)
        cancel_action.setObjectName("CancelBackgroundWorkAction")
        cancel_action.triggered.connect(
            lambda _checked=False: self._cancel_background_from_menu()
        )
        cancel_action.setStatusTip(
            "Minta pembatalan aman untuk Render atau Auto (AI) yang sedang berjalan"
        )
        ai_menu.addAction(cancel_action)
        self._cancel_background_action = cancel_action
        self._refresh_background_action_state()

    def _refresh_background_action_state(self) -> None:
        action = self._cancel_background_action
        if action is not None:
            action.setEnabled(self._background_busy())

    def _cancel_background_from_menu(self) -> None:
        if self.cancel_background_work():
            return
        self._show_project_notice(
            "Tidak ada pekerjaan aktif",
            "Tidak ada pekerjaan background yang sedang berjalan.",
        )

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        self._background_call: BackgroundCall[Any] | None = None
        self._background_timer: Any | None = None
        self._background_success: Callable[[Any], None] | None = None
        self._background_error_title = "Pekerjaan gagal"
        self._background_name = ""
        self._cancel_background_action: Any | None = None
        super().__init__(services, initial_state=initial_state)

    def _background_busy(self) -> bool:
        return self._background_call is not None

    def _start_background_work(
        self,
        *,
        name: str,
        work: Callable[[], Any] | None = None,
        cancellable_work: Callable[
            [CancellationToken, Callable[[float], None]], Any
        ]
        | None = None,
        success: Callable[[Any], None],
        error_title: str,
    ) -> bool:
        from PySide6.QtCore import QTimer

        if self._background_busy():
            self._show_project_notice(
                "Pekerjaan masih berjalan",
                f"Selesaikan '{self._background_name}' terlebih dahulu sebelum memulai pekerjaan lain.",
            )
            return False

        call: BackgroundCall[Any] = BackgroundCall(
            self.services.jobs,
            work,
            cancellable_work=cancellable_work,
            name=name,
        )
        timer = QTimer(self.window)
        timer.setInterval(120)
        timer.timeout.connect(self._poll_background_work)

        self._background_call = call
        self._background_timer = timer
        self._background_success = success
        self._background_error_title = error_title
        self._background_name = name
        self._refresh_background_action_state()
        self.window.statusBar().showMessage(f"{name} sedang berjalan…")
        call.start()
        timer.start()
        return True

    def cancel_background_work(self) -> bool:
        call = self._background_call
        if call is None:
            return False
        cancelled = call.cancel()
        if cancelled:
            if self._cancel_background_action is not None:
                self._cancel_background_action.setEnabled(False)
            self.window.statusBar().showMessage(
                f"Membatalkan {self._background_name}…",
                5000,
            )
        return cancelled

    def _clear_background_work(self) -> None:
        timer = self._background_timer
        if timer is not None:
            timer.stop()
            timer.deleteLater()
        self._background_call = None
        self._background_timer = None
        self._background_success = None
        self._background_error_title = "Pekerjaan gagal"
        self._background_name = ""
        self._refresh_background_action_state()

    def _poll_background_work(self) -> None:
        call = self._background_call
        if call is None:
            return
        snapshot = call.snapshot()
        if not snapshot.done:
            if snapshot.progress is not None:
                percent = round(snapshot.progress * 100)
                self.window.statusBar().showMessage(
                    f"{self._background_name}… {percent}%"
                )
            return

        success = self._background_success
        error_title = self._background_error_title
        name = self._background_name
        self._clear_background_work()

        if snapshot.cancelled:
            self.window.statusBar().showMessage(f"{name} dibatalkan.", 7000)
            return
        if snapshot.error is not None:
            self._show_project_error(error_title, snapshot.error)
            self.window.statusBar().showMessage(f"{name} gagal.", 7000)
            return
        if success is None:
            self.window.statusBar().showMessage(
                f"{name} selesai tanpa callback hasil.",
                7000,
            )
            return
        success(snapshot.result)

    def render_active_project(self, options: ExportOptions) -> bool:
        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Render tidak tersedia",
                "Buat atau buka project terlebih dahulu sebelum render.",
            )
            return False

        def completed(result: Any) -> None:
            output = getattr(result, "output_path", options.output_path)
            self.window.statusBar().showMessage(
                f"Render selesai: {output}",
                9000,
            )
            self._show_project_notice(
                "Render selesai",
                f"Video berhasil dibuat:\n{output}",
            )

        return self._start_background_work(
            name="Render video",
            cancellable_work=lambda token, progress: render_project(
                project,
                options,
                cancellation_token=token,
                progress_callback=progress,
            ),
            success=completed,
            error_title="Render gagal",
        )

    def render_active_selection(
        self,
        options: ExportOptions,
        *,
        start_seconds: float,
        end_seconds: float,
    ) -> bool:
        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Render Selection tidak tersedia",
                "Buat atau buka project terlebih dahulu.",
            )
            return False

        def completed(result: Any) -> None:
            output = getattr(result, "output_path", options.output_path)
            self.window.statusBar().showMessage(
                f"Render Selection selesai: {output}",
                9000,
            )
            self._show_project_notice(
                "Render Selection selesai",
                f"Video range In–Out berhasil dibuat:\n{output}",
            )

        return self._start_background_work(
            name=f"Render Selection {start_seconds:.3f}–{end_seconds:.3f} detik",
            cancellable_work=lambda token, progress: render_project_selection(
                project,
                options,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                cancellation_token=token,
                progress_callback=progress,
            ),
            success=completed,
            error_title="Render Selection gagal",
        )

    def apply_ai_native_motion(self) -> None:
        from PySide6.QtWidgets import QInputDialog, QLineEdit

        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Auto (AI) tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        credentials = self._windows_credential_store()
        if credentials is None:
            return
        try:
            slots = configured_gemini_slots(credentials)
        except OSError as error:
            self._show_project_error("Gagal membaca credential Gemini", error)
            return
        if not slots:
            self._show_project_notice(
                "API key Gemini belum ada",
                "Simpan minimal satu API key melalui menu AI → Simpan / Ganti API Key Gemini… terlebih dahulu.",
            )
            return

        model, accepted = QInputDialog.getText(
            self.window,
            "Auto Animasi Gemini",
            (
                "Model Gemini yang akan memilih animasi native.\n"
                "Request berjalan di background agar UI tetap responsif:"
            ),
            QLineEdit.EchoMode.Normal,
            DEFAULT_GEMINI_ANIMATION_MODEL,
        )
        if not accepted:
            return
        normalized_model = model.strip()
        if not normalized_model:
            self._show_project_notice(
                "Model Gemini kosong",
                "Isi nama model Gemini sebelum menjalankan Auto (AI).",
            )
            return

        def completed(result: Any) -> None:
            if not isinstance(result, AiAnimationPlanResult):
                self._show_project_notice(
                    "Hasil Auto (AI) tidak valid",
                    "Job Auto (AI) selesai tanpa hasil terstruktur; project tidak diubah.",
                )
                return
            assignments = result.assignments
            if session.current != project:
                self._show_project_notice(
                    "Hasil Auto (AI) tidak diterapkan",
                    "Project berubah saat Gemini bekerja. Jalankan Auto (AI) lagi agar hasil sesuai state terbaru.",
                )
                self.window.statusBar().showMessage(
                    "Auto (AI) selesai tetapi project sudah berubah; hasil dibuang.",
                    8000,
                )
                return
            try:
                session.execute(SetAnimationAssignmentsBatch(assignments))
            except ValueError as error:
                self._show_project_error("Auto (AI) gagal diterapkan", error)
                return
            self._refresh_window_title()
            self._refresh_validation_badge()
            self.refresh_editor_overview()
            self._refresh_animation_menu_state()
            diagnostics_text = ai_run_status_text(result.diagnostics)
            self.window.statusBar().showMessage(
                f"Auto (AI) menerapkan {len(assignments)} assignment melalui "
                f"{normalized_model}; {diagnostics_text}. "
                "Gunakan Undo untuk membatalkan atau Simpan untuk menyimpan project.",
                12000,
            )

        self._start_background_work(
            name=f"Auto (AI) — {normalized_model}",
            cancellable_work=lambda token, progress: plan_gemini_native_motion_detailed(
                project,
                credentials=credentials,
                credential_slots=slots,
                model=normalized_model,
                allowed_effects=NATIVE_MOTION_CHOICES,
                cancel_requested=lambda: token.is_cancelled,
                progress_callback=progress,
            ),
            success=completed,
            error_title="Auto (AI) gagal",
        )


def create_background_work_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> BackgroundWorkMainWindow:
    return BackgroundWorkMainWindow(services, initial_state=initial_state)
