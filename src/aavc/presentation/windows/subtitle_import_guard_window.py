from __future__ import annotations

from pathlib import Path

from aavc.application.commands import SetNarrationAudio, SetSubtitleSource
from aavc.application.services.media_import import classify_media_path
from aavc.bootstrap.composition_root import FoundationServices
from aavc.domain.errors import AAVCError
from aavc.presentation.windows.subtitle_edit_window import SubtitleEditMainWindow
from aavc.subtitles import parse_srt


def subtitle_import_requires_working_copy_guard(
    media_kind: str,
    *,
    editor_active: bool,
    working_copy_dirty: bool,
) -> bool:
    """Return whether importing media must confirm discarding local subtitle edits."""

    return media_kind == "subtitle" and editor_active and working_copy_dirty


class SubtitleImportGuardMainWindow(SubtitleEditMainWindow):
    """Prevent SRT re-import from desynchronizing project source and cue working copy."""

    def _apply_imported_media(self, chosen: str, media_kind: str) -> str | None:
        if subtitle_import_requires_working_copy_guard(
            media_kind,
            editor_active=self._subtitle_editor_is_active(),
            working_copy_dirty=self._subtitle_working_copy_dirty,
        ) and not self._confirm_subtitle_working_copy_discard("mengimpor SRT baru"):
            return None

        if media_kind == "subtitle":
            self.services.project_session.execute(SetSubtitleSource(chosen))
            media_label = "Subtitle SRT"
            if self._subtitle_editor_is_active():
                self._rebuild_subtitle_editor_after_discard_authorized()
            else:
                self._set_subtitle_working_copy_dirty(False)
        else:
            self.services.project_session.execute(SetNarrationAudio(chosen))
            media_label = "Narasi audio"

        self._refresh_window_title()
        self.refresh_editor_overview()
        return media_label

    def import_media(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Impor Media tidak tersedia",
                "Buat atau buka proyek terlebih dahulu sebelum mengimpor media.",
            )
            return

        project_path = self.services.project_session.path
        if project_path is not None:
            start_directory = str(project_path.parent)
        else:
            start_directory = str(Path(project.source_docx).resolve().parent)

        chosen, _ = QFileDialog.getOpenFileName(
            self.window,
            "Impor Media",
            start_directory,
            (
                "Media didukung (*.srt *.mp3 *.wav *.m4a *.aac *.flac *.ogg);;"
                "Subtitle SRT (*.srt);;"
                "Audio narasi (*.mp3 *.wav *.m4a *.aac *.flac *.ogg);;"
                "Semua File (*.*)"
            ),
        )
        if not chosen:
            return

        try:
            media_kind = classify_media_path(chosen)
            if media_kind == "subtitle":
                # Validate before asking the user to discard a dirty working copy and
                # before mutating ProjectState. The live editor parses the same format.
                parse_srt(chosen)
            media_label = self._apply_imported_media(chosen, media_kind)
        except (AAVCError, OSError, ValueError) as error:
            self._show_project_error("Impor Media gagal", error)
            return

        if media_label is None:
            return

        self.window.statusBar().showMessage(
            f"{media_label} diimpor: {Path(chosen).name}. "
            "Klik Simpan untuk menyimpan perubahan.",
            7000,
        )


def create_subtitle_import_guard_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> SubtitleImportGuardMainWindow:
    return SubtitleImportGuardMainWindow(services, initial_state=initial_state)