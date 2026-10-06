from __future__ import annotations

from typing import Any

from aavc.application.commands import SetAnimationAssignmentsBatch
from aavc.application.services.ai_animation_service import (
    DEFAULT_GEMINI_ANIMATION_MODEL,
    plan_gemini_native_motion,
)
from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.dialogs.asset_motion import NATIVE_MOTION_CHOICES
from aavc.presentation.windows.ai_menu_window import configured_gemini_slots
from aavc.presentation.windows.narration_recording_window import (
    NarrationRecordingMainWindow,
)


class AiNativeMotionMainWindow(NarrationRecordingMainWindow):
    """Use the secure Gemini pool to plan only native render-backed asset motion."""

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        ai_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "AI":
                ai_menu = menu_action.menu()
                break
        if ai_menu is None:
            return

        auto_action = action_type("Auto Animasi Gemini…", self.window)
        auto_action.setObjectName("GeminiAutoAnimationAction")
        auto_action.triggered.connect(
            lambda _checked=False: self.apply_ai_native_motion()
        )
        ai_menu.insertAction(
            ai_menu.actions()[0] if ai_menu.actions() else None,
            auto_action,
        )
        separator = ai_menu.insertSeparator(
            ai_menu.actions()[1] if len(ai_menu.actions()) > 1 else None
        )
        separator.setObjectName("GeminiAutoAnimationSeparator")

    def _build_toolbar(self, toolbar_type: Any, action_type: Any) -> None:
        super()._build_toolbar(toolbar_type, action_type)
        combo = self._animation_mode_combo
        if combo is not None:
            combo.setToolTip(
                "Auto (AI): Gemini memilih animasi native render-backed. "
                "Random App: Auto Motion deterministik. Manual: editor aset Scene terpilih."
            )

    def _activate_animation_mode(self, mode: str) -> None:
        if mode == "Auto (AI)":
            self.apply_ai_native_motion()
            return
        super()._activate_animation_mode(mode)

    def apply_ai_native_motion(self) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QCursor
        from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit

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
                "Hanya Scene/aset project dan efek render-backed yang boleh digunakan:"
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

        self.window.statusBar().showMessage(
            f"Gemini sedang memilih animasi dengan {normalized_model}…"
        )
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        QApplication.processEvents()
        try:
            assignments = plan_gemini_native_motion(
                project,
                credentials=credentials,
                credential_slots=slots,
                model=normalized_model,
                allowed_effects=NATIVE_MOTION_CHOICES,
            )
            session.execute(SetAnimationAssignmentsBatch(assignments))
        except (OSError, RuntimeError, ValueError) as error:
            self._show_project_error("Auto (AI) gagal", error)
            self.window.statusBar().showMessage(
                "Auto (AI) gagal; project tidak diubah.",
                7000,
            )
            return
        finally:
            QApplication.restoreOverrideCursor()

        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self._refresh_animation_menu_state()
        self.window.statusBar().showMessage(
            f"Auto (AI) menerapkan {len(assignments)} assignment native melalui {normalized_model}. "
            "Gunakan Undo untuk membatalkan atau Simpan untuk menyimpan project.",
            9000,
        )


def create_ai_native_motion_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> AiNativeMotionMainWindow:
    return AiNativeMotionMainWindow(services, initial_state=initial_state)
