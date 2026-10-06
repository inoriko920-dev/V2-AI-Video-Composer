from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from aavc.application.commands.scene_order import DeleteScene, DuplicateScene, MoveScene
from aavc.application.services.vertical_slice import create_project_state
from aavc.bootstrap.composition_root import FoundationServices
from aavc.domain.errors import AAVCError
from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.main_window import MainWindow, ensure_project_suffix

UnsavedChoice = Literal["save", "discard", "cancel"]


def background_work_blocks_close(*, background_busy: bool) -> bool:
    """Return whether active long-running work must keep the UI event loop alive."""

    return background_busy


def resolve_unsaved_choice(
    is_dirty: bool,
    choice: UnsavedChoice,
    *,
    save_succeeded: bool = False,
) -> bool:
    """Return whether a destructive action may continue."""

    if not is_dirty:
        return True
    if choice == "discard":
        return True
    if choice == "cancel":
        return False
    if choice == "save":
        return save_succeeded
    raise ValueError(f"Pilihan unsaved-change tidak dikenal: {choice}")


class GuardedMainWindow(MainWindow):
    """Main window that prevents silent loss and exposes safe editor commands."""

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        self._allow_close = False
        self._close_guard: object | None = None
        super().__init__(services, initial_state=initial_state)
        self._install_close_guard()

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        file_menu: Any | None = None
        edit_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "File":
                file_menu = menu_action.menu()
            elif menu_action.text() == "Edit":
                edit_menu = menu_action.menu()

        if file_menu is not None:
            save_as_action = action_type("Simpan Sebagai…", self.window)
            save_as_action.setShortcut("Ctrl+Shift+S")
            save_as_action.triggered.connect(self.save_project_as)
            exit_action = next(
                (action for action in file_menu.actions() if action.text() == "Keluar"),
                None,
            )
            if exit_action is not None:
                file_menu.insertAction(exit_action, save_as_action)
            else:
                file_menu.addAction(save_as_action)

        if edit_menu is None:
            return

        edit_menu.clear()

        undo_action = action_type("Undo", self.window)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_project)
        edit_menu.addAction(undo_action)

        redo_action = action_type("Redo", self.window)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo_project)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()

        move_up = action_type("Pindah Scene ke Atas", self.window)
        move_up.setShortcut("Alt+Up")
        move_up.triggered.connect(
            lambda _checked=False: self.move_selected_scene(-1)
        )
        edit_menu.addAction(move_up)

        move_down = action_type("Pindah Scene ke Bawah", self.window)
        move_down.setShortcut("Alt+Down")
        move_down.triggered.connect(
            lambda _checked=False: self.move_selected_scene(1)
        )
        edit_menu.addAction(move_down)
        edit_menu.addSeparator()

        duplicate_scene = action_type("Duplikasi Scene", self.window)
        duplicate_scene.setShortcut("Ctrl+D")
        duplicate_scene.triggered.connect(
            lambda _checked=False: self.duplicate_selected_scene()
        )
        edit_menu.addAction(duplicate_scene)

        delete_scene = action_type("Hapus Scene", self.window)
        delete_scene.setShortcut("Delete")
        delete_scene.triggered.connect(
            lambda _checked=False: self.delete_selected_scene()
        )
        edit_menu.addAction(delete_scene)

    def _install_close_guard(self) -> None:
        from PySide6.QtCore import QEvent, QObject

        owner = self

        class CloseGuard(QObject):
            def eventFilter(self, watched: Any, event: Any) -> bool:
                if watched is owner.window and event.type() == QEvent.Type.Close:
                    if owner._allow_close:
                        return False
                    busy_check = getattr(owner, "_background_busy", None)
                    background_busy = bool(busy_check()) if callable(busy_check) else False
                    if background_work_blocks_close(background_busy=background_busy):
                        active_name = getattr(owner, "_background_name", "") or "Render/Auto AI"
                        owner._show_project_notice(
                            "Pekerjaan masih berjalan",
                            f"{active_name} masih berjalan. Selesaikan pekerjaan tersebut "
                            "sebelum menutup aplikasi agar proses tidak terputus.",
                        )
                        event.ignore()
                        return True
                    if not owner._confirm_unsaved_changes("keluar dari aplikasi"):
                        event.ignore()
                        return True
                    owner._allow_close = True
                return False

        guard = CloseGuard(self.window)
        self.window.installEventFilter(guard)
        self._close_guard = guard

    def _confirm_unsaved_changes(self, action_label: str) -> bool:
        from PySide6.QtWidgets import QMessageBox

        session = self.services.project_session
        if not session.is_dirty:
            return True

        project = session.current
        project_title = project.title if project is not None else "project aktif"
        box = QMessageBox(self.window)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Perubahan belum disimpan")
        box.setText(f"{project_title} memiliki perubahan yang belum disimpan.")
        box.setInformativeText(f"Simpan perubahan sebelum {action_label}?")
        box.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        box.setDefaultButton(QMessageBox.StandardButton.Save)
        result = QMessageBox.StandardButton(box.exec())

        if result == QMessageBox.StandardButton.Save:
            super().save_project()
            return resolve_unsaved_choice(
                True,
                "save",
                save_succeeded=not session.is_dirty,
            )
        if result == QMessageBox.StandardButton.Discard:
            return resolve_unsaved_choice(True, "discard")
        return resolve_unsaved_choice(True, "cancel")

    def save_project_as(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Simpan Sebagai tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        current_path = session.path
        if current_path is not None:
            default_destination = str(current_path)
        else:
            source_parent = Path(project.source_docx).resolve().parent
            default_destination = str(source_parent / f"{project.title}.aavcproj")

        destination, _ = QFileDialog.getSaveFileName(
            self.window,
            "Simpan Proyek AAVC Sebagai",
            default_destination,
            "AAVC Project (*.aavcproj)",
        )
        if not destination:
            return
        destination = ensure_project_suffix(destination)

        try:
            saved = session.save(destination)
        except (AAVCError, OSError, ValueError) as error:
            self._show_project_error("Simpan Sebagai gagal", error)
            return

        self._refresh_window_title()
        self.window.statusBar().showMessage(
            f"Proyek disimpan sebagai: {saved}",
            6000,
        )

    def move_selected_scene(self, offset: int) -> None:
        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Reorder Scene tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        scene_number = self._selected_scene_number
        if scene_number is None:
            self.window.statusBar().showMessage(
                "Pilih Scene terlebih dahulu sebelum mengubah urutan.",
                5000,
            )
            return

        try:
            self.services.project_session.execute(MoveScene(scene_number, offset))
        except ValueError as error:
            self.window.statusBar().showMessage(str(error), 5000)
            return

        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        direction = "atas" if offset < 0 else "bawah"
        self.window.statusBar().showMessage(
            f"Scene {scene_number:02d} dipindah satu posisi ke {direction}. "
            "Klik Simpan untuk menyimpan perubahan.",
            7000,
        )

    def duplicate_selected_scene(self) -> None:
        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Duplikasi Scene tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        scene_number = self._selected_scene_number
        if scene_number is None:
            self.window.statusBar().showMessage(
                "Pilih Scene terlebih dahulu sebelum menduplikasi.",
                5000,
            )
            return

        try:
            updated = session.execute(DuplicateScene(scene_number))
        except ValueError as error:
            self.window.statusBar().showMessage(str(error), 5000)
            return

        source_index = next(
            index
            for index, scene in enumerate(updated.scenes)
            if scene.scene_number == scene_number
        )
        duplicate = updated.scenes[source_index + 1]
        self._selected_scene_number = duplicate.scene_number
        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"Scene {scene_number:02d} diduplikasi menjadi Scene "
            f"{duplicate.scene_number:02d}. Gunakan Undo untuk membatalkan atau "
            "klik Simpan untuk menyimpan perubahan.",
            7000,
        )

    def delete_selected_scene(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Hapus Scene tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        scene_number = self._selected_scene_number
        if scene_number is None:
            self.window.statusBar().showMessage(
                "Pilih Scene terlebih dahulu sebelum menghapus.",
                5000,
            )
            return

        if len(project.scenes) <= 1:
            self.window.statusBar().showMessage(
                "Scene terakhir tidak boleh dihapus.",
                5000,
            )
            return

        scene_index = next(
            index
            for index, scene in enumerate(project.scenes)
            if scene.scene_number == scene_number
        )
        answer = QMessageBox.question(
            self.window,
            "Hapus Scene",
            f"Hapus Scene {scene_number:02d}? Aksi ini dapat dikembalikan dengan Undo.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            updated = session.execute(DeleteScene(scene_number))
        except ValueError as error:
            self.window.statusBar().showMessage(str(error), 5000)
            return

        next_index = min(scene_index, len(updated.scenes) - 1)
        self._selected_scene_number = updated.scenes[next_index].scene_number
        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"Scene {scene_number:02d} dihapus. Gunakan Undo untuk mengembalikan "
            "atau klik Simpan untuk menyimpan perubahan.",
            7000,
        )

    def open_project(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        chosen, _ = QFileDialog.getOpenFileName(
            self.window,
            "Buka Proyek AAVC",
            "",
            "AAVC Project (*.aavcproj);;Semua File (*.*)",
        )
        if not chosen:
            return
        if not self._confirm_unsaved_changes("membuka project lain"):
            return

        try:
            project = self.services.project_session.open(chosen)
        except (AAVCError, OSError, ValueError, KeyError, TypeError) as error:
            self._show_project_error("Gagal membuka proyek", error)
            return

        self._selected_scene_number = (
            project.scenes[0].scene_number if project.scenes else None
        )
        self._refresh_window_title()
        self.window.statusBar().showMessage(f"Proyek dibuka: {chosen}", 5000)
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.show_route(UiRoute.EDITOR)

    def create_project_from_docx(self, scene_docx: str) -> None:
        from PySide6.QtWidgets import QFileDialog

        source = Path(scene_docx).resolve()
        if not source.is_file():
            self._show_project_notice(
                "Scene DOCX belum dipilih",
                "Pilih file Scene DOCX terlebih dahulu.",
            )
            return

        asset_directory = QFileDialog.getExistingDirectory(
            self.window,
            "Pilih Folder Aset",
            str(source.parent),
        )
        if not asset_directory:
            return

        try:
            project = create_project_state(
                title=source.stem,
                scene_docx=source,
                asset_directory=asset_directory,
            )
        except (AAVCError, OSError, ValueError, KeyError, TypeError) as error:
            self._show_project_error("Gagal membaca input proyek", error)
            return

        default_destination = str(source.with_suffix(".aavcproj"))
        destination, _ = QFileDialog.getSaveFileName(
            self.window,
            "Simpan Proyek AAVC",
            default_destination,
            "AAVC Project (*.aavcproj)",
        )
        if not destination:
            return
        destination = ensure_project_suffix(destination)

        if not self._confirm_unsaved_changes("membuat project baru"):
            return

        try:
            self.services.project_session.create(project, destination)
        except (AAVCError, OSError, ValueError) as error:
            self._show_project_error("Gagal menyimpan proyek baru", error)
            return

        self._selected_scene_number = (
            project.scenes[0].scene_number if project.scenes else None
        )
        self._refresh_window_title()
        self.window.statusBar().showMessage(f"Proyek dibuat: {destination}", 5000)
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.show_route(UiRoute.EDITOR)


def create_guarded_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> GuardedMainWindow:
    return GuardedMainWindow(services, initial_state=initial_state)
