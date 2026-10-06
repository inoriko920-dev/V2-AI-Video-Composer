from __future__ import annotations

from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.windows.subtitle_export_guard_window import (
    SubtitleExportGuardMainWindow,
)


def subtitle_project_save_requires_working_copy_guard(
    *,
    editor_active: bool,
    working_copy_dirty: bool,
) -> bool:
    """Return whether project persistence must stop for unsaved local cue edits."""

    return editor_active and working_copy_dirty


class SubtitleSaveGuardMainWindow(SubtitleExportGuardMainWindow):
    """Prevent project persistence from implying local subtitle cue edits were saved."""

    def _project_persistence_blocked_by_subtitle_working_copy(self) -> bool:
        if not subtitle_project_save_requires_working_copy_guard(
            editor_active=self._subtitle_editor_is_active(),
            working_copy_dirty=self._subtitle_working_copy_dirty,
        ):
            return False

        self._show_project_notice(
            "Subtitle belum disimpan",
            "Working copy subtitle memiliki perubahan cue yang belum disimpan ke file SRT. "
            "Gunakan Simpan Salinan di Subtitle Editor terlebih dahulu, lalu simpan project.",
        )
        return True

    def save_project(self) -> None:
        if self._project_persistence_blocked_by_subtitle_working_copy():
            return
        super().save_project()

    def save_project_as(self) -> None:
        if self._project_persistence_blocked_by_subtitle_working_copy():
            return
        super().save_project_as()


def create_subtitle_save_guard_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> SubtitleSaveGuardMainWindow:
    return SubtitleSaveGuardMainWindow(services, initial_state=initial_state)
