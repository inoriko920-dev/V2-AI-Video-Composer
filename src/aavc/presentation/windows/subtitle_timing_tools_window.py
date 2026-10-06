from __future__ import annotations

from pathlib import Path
from typing import Any

from aavc.application.commands import SetSubtitleSource
from aavc.bootstrap.composition_root import FoundationServices
from aavc.domain.errors import AAVCError
from aavc.presentation.windows.subtitle_save_guard_window import (
    SubtitleSaveGuardMainWindow,
)
from aavc.subtitles import (
    fit_subtitle_cues_from_row_to_end,
    format_srt_timestamp,
    parse_srt,
    parse_srt_timestamp,
    write_srt_atomic,
)


def subtitle_target_fit_requires_clean_working_copy(
    *,
    editor_active: bool,
    working_copy_dirty: bool,
) -> bool:
    """Return whether target-end fit must stop to protect local cue edits."""

    return editor_active and working_copy_dirty


def resolve_subtitle_fit_destination(source: Path, chosen: str | Path) -> Path:
    """Normalize a fit-copy destination while protecting the source SRT."""

    destination = Path(chosen).expanduser()
    if destination.suffix.lower() != ".srt":
        destination = destination.with_suffix(".srt")
    resolved = destination.resolve()
    if resolved == source.expanduser().resolve():
        raise ValueError("Pilih nama atau lokasi lain; source SRT asli tidak boleh ditimpa")
    return resolved


class SubtitleTimingToolsMainWindow(SubtitleSaveGuardMainWindow):
    """Expose safe subtitle timing correction tools above the working-copy guards."""

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        edit_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "Edit":
                edit_menu = menu_action.menu()
                break
        if edit_menu is None:
            return

        edit_menu.addSeparator()
        fit_action = action_type("Fit Subtitle ke Target OUT…", self.window)
        fit_action.triggered.connect(
            lambda _checked=False: self.fit_subtitle_to_target_end()
        )
        edit_menu.addAction(fit_action)

    def fit_subtitle_to_target_end(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QInputDialog

        session = self.services.project_session
        project = session.current
        if project is None or not project.subtitle_source:
            self._show_project_notice(
                "Fit Subtitle tidak tersedia",
                "Project aktif belum memiliki source subtitle SRT.",
            )
            return

        if subtitle_target_fit_requires_clean_working_copy(
            editor_active=self._subtitle_editor_is_active(),
            working_copy_dirty=self._subtitle_working_copy_dirty,
        ):
            self._show_project_notice(
                "Simpan working copy terlebih dahulu",
                "Edit Cue masih memiliki perubahan lokal. Gunakan Simpan Salinan SRT terlebih "
                "dahulu agar Fit Subtitle tidak membuang edit tersebut.",
            )
            return

        source = Path(project.subtitle_source).expanduser().resolve()
        try:
            cues = parse_srt(source)
        except (OSError, ValueError) as error:
            self._show_project_error("Gagal membaca subtitle", error)
            return
        if not cues:
            self._show_project_notice(
                "Subtitle kosong",
                "Source SRT aktif tidak memiliki cue yang dapat di-fit.",
            )
            return

        choices = [
            f"{row + 1}. {format_srt_timestamp(cue.start_seconds)} — "
            f"{cue.text.replace('\\N', ' ')[:72]}"
            for row, cue in enumerate(cues)
        ]
        selected, accepted = QInputDialog.getItem(
            self.window,
            "Fit Subtitle ke Target OUT",
            "Pilih cue anchor. Cue ini dan seluruh cue setelahnya akan di-stretch:",
            choices,
            0,
            False,
        )
        if not accepted:
            return
        try:
            selected_row = choices.index(selected)
        except ValueError:
            self._show_project_notice(
                "Cue tidak valid",
                "Cue anchor yang dipilih tidak ditemukan.",
            )
            return

        target_text, accepted = QInputDialog.getText(
            self.window,
            "Target OUT Akhir Subtitle",
            "Masukkan OUT akhir yang diinginkan (HH:MM:SS,mmm):",
            text=format_srt_timestamp(cues[-1].end_seconds),
        )
        if not accepted:
            return

        try:
            target_end = parse_srt_timestamp(target_text.strip())
            fitted = fit_subtitle_cues_from_row_to_end(
                cues,
                selected_row,
                target_end,
            )
        except ValueError as error:
            self._show_project_error("Target OUT tidak valid", error)
            return
        if fitted is cues or fitted == cues:
            self.window.statusBar().showMessage(
                "Target OUT sama dengan timing saat ini; tidak ada perubahan.",
                5000,
            )
            return

        default_destination = source.with_name(f"{source.stem}.fit.srt")
        chosen, _ = QFileDialog.getSaveFileName(
            self.window,
            "Simpan Hasil Fit Subtitle",
            str(default_destination),
            "Subtitle SRT (*.srt)",
        )
        if not chosen:
            return

        try:
            destination = resolve_subtitle_fit_destination(source, chosen)
            saved = write_srt_atomic(destination, fitted)
            subtitle_editor_was_active = self._subtitle_editor_is_active()
            session.execute(SetSubtitleSource(str(saved)))
        except (AAVCError, OSError, ValueError) as error:
            self._show_project_error("Gagal menyimpan hasil Fit Subtitle", error)
            return

        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        if subtitle_editor_was_active:
            self._rebuild_subtitle_editor_after_discard_authorized()
        self.window.statusBar().showMessage(
            f"Fit Subtitle disimpan: {saved.name}. Project memakai salinan baru; "
            "klik Simpan untuk menyimpan referensi project.",
            9000,
        )


def create_subtitle_timing_tools_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> SubtitleTimingToolsMainWindow:
    return SubtitleTimingToolsMainWindow(services, initial_state=initial_state)
