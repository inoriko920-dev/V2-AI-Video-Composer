from __future__ import annotations

from pathlib import Path

from aavc.application.commands import (
    SetSubtitleAnimation,
    SetSubtitleSource,
    SetSubtitleStyle,
)
from aavc.bootstrap.composition_root import FoundationServices
from aavc.domain.errors import AAVCError
from aavc.domain.project.models import SubtitleAnimationSettings, SubtitleStyle
from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.main_window import format_window_title
from aavc.presentation.windows.native_motion_preview_window import NativeMotionPreviewMainWindow
from aavc.subtitles import SubtitleCue, write_srt_atomic


def resolve_subtitle_working_copy_leave(
    is_dirty: bool,
    *,
    discard_confirmed: bool,
) -> bool:
    """Return whether an action may leave a local subtitle working copy."""

    return not is_dirty or discard_confirmed


def subtitle_editor_should_leave_for_missing_source(
    *,
    editor_active: bool,
    subtitle_source: str | None,
) -> bool:
    """Return whether an active Subtitle Editor no longer has a backing project source."""

    return editor_active and not subtitle_source


class SubtitleEditMainWindow(NativeMotionPreviewMainWindow):
    """Main window with safe selected-cue editing through copied SRT sources."""

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        self._subtitle_working_copy_dirty = False
        self._subtitle_leave_bypass = False
        super().__init__(services, initial_state=initial_state)

    def _subtitle_editor_is_active(self) -> bool:
        return str(self.window.property("ui_state") or "") == UiRoute.SUBTITLE_EDITOR.value

    def _set_subtitle_working_copy_dirty(self, is_dirty: bool) -> None:
        self._subtitle_working_copy_dirty = is_dirty
        self._refresh_window_title()

    def _refresh_window_title(self) -> None:
        session = self.services.project_session
        project = session.current
        self.window.setWindowTitle(
            format_window_title(
                self.services.app_name,
                project.title if project is not None else None,
                is_dirty=session.is_dirty or self._subtitle_working_copy_dirty,
            )
        )

    def _confirm_subtitle_working_copy_discard(self, action_label: str) -> bool:
        from PySide6.QtWidgets import QMessageBox

        if not self._subtitle_working_copy_dirty:
            return True
        answer = QMessageBox.question(
            self.window,
            "Buang edit working copy subtitle?",
            "Working copy subtitle atau form cue aktif memiliki perubahan yang belum "
            f"disimpan sebagai salinan. Buang perubahan sebelum {action_label}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return resolve_subtitle_working_copy_leave(
            True,
            discard_confirmed=answer == QMessageBox.StandardButton.Yes,
        )

    def _confirm_unsaved_changes(self, action_label: str) -> bool:
        if not super()._confirm_unsaved_changes(action_label):
            return False
        if self._subtitle_leave_bypass:
            return True
        return self._confirm_subtitle_working_copy_discard(action_label)

    def show_route(self, route: UiRoute) -> None:
        leaving_subtitle = (
            self._subtitle_editor_is_active()
            and route is not UiRoute.SUBTITLE_EDITOR
            and self._subtitle_working_copy_dirty
        )
        if (
            leaving_subtitle
            and not self._subtitle_leave_bypass
            and not self._confirm_subtitle_working_copy_discard(
                f"membuka {route.value}"
            )
        ):
            return
        super().show_route(route)
        if leaving_subtitle:
            self._set_subtitle_working_copy_dirty(False)

    def open_project(self) -> None:
        if self._subtitle_editor_is_active() and self._subtitle_working_copy_dirty:
            if not self._confirm_subtitle_working_copy_discard("membuka project lain"):
                return
            self._subtitle_leave_bypass = True
        try:
            super().open_project()
        finally:
            self._subtitle_leave_bypass = False

    def create_project_from_docx(self, scene_docx: str) -> None:
        if self._subtitle_editor_is_active() and self._subtitle_working_copy_dirty:
            if not self._confirm_subtitle_working_copy_discard("membuat project baru"):
                return
            self._subtitle_leave_bypass = True
        try:
            super().create_project_from_docx(scene_docx)
        finally:
            self._subtitle_leave_bypass = False

    def _reconcile_subtitle_editor_after_project_history(self) -> None:
        project = self.services.project_session.current
        subtitle_source = project.subtitle_source if project is not None else None
        if not subtitle_editor_should_leave_for_missing_source(
            editor_active=self._subtitle_editor_is_active(),
            subtitle_source=subtitle_source,
        ):
            return

        self._set_subtitle_working_copy_dirty(False)
        self.show_route(UiRoute.EDITOR)
        self.window.statusBar().showMessage(
            "Subtitle Editor ditutup karena snapshot project tidak memiliki source subtitle.",
            6000,
        )

    def undo_project(self) -> None:
        session = self.services.project_session
        if (
            session.can_undo
            and self._subtitle_editor_is_active()
            and self._subtitle_working_copy_dirty
        ):
            if not self._confirm_subtitle_working_copy_discard("menjalankan Undo project"):
                return
            self._subtitle_leave_bypass = True
        try:
            super().undo_project()
            self._reconcile_subtitle_editor_after_project_history()
        finally:
            self._subtitle_leave_bypass = False

    def redo_project(self) -> None:
        session = self.services.project_session
        if (
            session.can_redo
            and self._subtitle_editor_is_active()
            and self._subtitle_working_copy_dirty
        ):
            if not self._confirm_subtitle_working_copy_discard("menjalankan Redo project"):
                return
            self._subtitle_leave_bypass = True
        try:
            super().redo_project()
            self._reconcile_subtitle_editor_after_project_history()
        finally:
            self._subtitle_leave_bypass = False

    def set_subtitle_style(self, style: SubtitleStyle) -> None:
        """Apply render-backed style without rebuilding and discarding local cue edits."""

        try:
            self.services.project_session.execute(SetSubtitleStyle(style))
        except (AAVCError, ValueError) as error:
            self._show_project_error("Gagal mengubah gaya subtitle", error)
            return
        self._refresh_window_title()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"Gaya subtitle diterapkan: {style.preset_name}. "
            "Working copy Edit Cue tetap dipertahankan; klik Simpan untuk menyimpan project.",
            7000,
        )

    def set_subtitle_animation(self, animation: SubtitleAnimationSettings) -> None:
        """Apply render-backed animation without rebuilding the subtitle editor route."""

        try:
            self.services.project_session.execute(SetSubtitleAnimation(animation))
        except (AAVCError, ValueError) as error:
            self._show_project_error("Gagal mengubah animasi subtitle", error)
            return
        self._refresh_window_title()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"Animasi subtitle diterapkan: {animation.preset}. "
            "Working copy Edit Cue tetap dipertahankan; klik Simpan untuk menyimpan project.",
            7000,
        )

    def _rebuild_subtitle_editor_after_discard_authorized(self) -> None:
        self._subtitle_leave_bypass = True
        try:
            self.open_subtitle_editor()
        finally:
            self._subtitle_leave_bypass = False

    def save_subtitle_copy(self, cues: tuple[SubtitleCue, ...]) -> None:
        from PySide6.QtWidgets import QFileDialog

        project = self.services.project_session.current
        if project is None or not project.subtitle_source:
            self._show_project_notice(
                "Subtitle tidak tersedia",
                "Project aktif belum memiliki source subtitle SRT.",
            )
            return

        source = Path(project.subtitle_source).expanduser().resolve()
        default_destination = source.with_name(f"{source.stem}.edited.srt")
        chosen, _ = QFileDialog.getSaveFileName(
            self.window,
            "Simpan Salinan Subtitle SRT",
            str(default_destination),
            "Subtitle SRT (*.srt)",
        )
        if not chosen:
            return

        destination = Path(chosen).expanduser()
        if destination.suffix.lower() != ".srt":
            destination = destination.with_suffix(".srt")
        try:
            destination_resolved = destination.resolve()
        except OSError as error:
            self._show_project_error("Lokasi subtitle tidak valid", error)
            return
        if destination_resolved == source:
            self._show_project_notice(
                "Source asli dilindungi",
                "Pilih nama atau lokasi file lain. Flow Edit Cue tidak menimpa SRT source asli.",
            )
            return

        try:
            saved = write_srt_atomic(destination_resolved, cues)
            self.services.project_session.execute(SetSubtitleSource(str(saved)))
        except (AAVCError, OSError, ValueError) as error:
            self._show_project_error("Gagal menyimpan salinan subtitle", error)
            return

        self._refresh_window_title()
        self.refresh_editor_overview()
        self._rebuild_subtitle_editor_after_discard_authorized()
        self.window.statusBar().showMessage(
            f"Salinan subtitle disimpan: {saved.name}. "
            "Project sekarang memakai source baru; klik Simpan untuk menyimpan referensi project.",
            9000,
        )

    def open_subtitle_editor(self) -> None:
        from aavc.presentation.screens.live_subtitle import create_live_subtitle_screen

        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Subtitle tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return
        if not project.subtitle_source:
            self._show_project_notice(
                "Subtitle belum ada",
                "Impor file SRT melalui tombol Impor Media terlebih dahulu.",
            )
            return

        old_working_copy_dirty = self._subtitle_working_copy_dirty
        if (
            self._subtitle_editor_is_active()
            and old_working_copy_dirty
            and not self._subtitle_leave_bypass
            and not self._confirm_subtitle_working_copy_discard(
                "memuat ulang Subtitle Editor"
            )
        ):
            return

        try:
            replacement = create_live_subtitle_screen(
                project.subtitle_source,
                style=project.subtitle_style,
                animation=project.subtitle_animation,
                on_apply_style=self.set_subtitle_style,
                on_apply_animation=self.set_subtitle_animation,
                on_reload=self._rebuild_subtitle_editor_after_discard_authorized,
                on_save_copy=self.save_subtitle_copy,
                on_working_copy_dirty_changed=self._set_subtitle_working_copy_dirty,
            )
        except (OSError, ValueError) as error:
            self._set_subtitle_working_copy_dirty(old_working_copy_dirty)
            self._show_project_error("Gagal membaca subtitle", error)
            return

        self._replace_route_widget(UiRoute.SUBTITLE_EDITOR, replacement)
        self._set_subtitle_working_copy_dirty(False)
        self.show_route(UiRoute.SUBTITLE_EDITOR)
        self.window.statusBar().showMessage(
            f"Subtitle dimuat: {Path(project.subtitle_source).name}",
            5000,
        )


def create_subtitle_edit_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> SubtitleEditMainWindow:
    return SubtitleEditMainWindow(services, initial_state=initial_state)
