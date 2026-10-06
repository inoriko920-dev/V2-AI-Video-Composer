from __future__ import annotations

from pathlib import Path
from typing import Any

from aavc.application.commands import MoveSceneToIndex, SplitScene
from aavc.application.services.export_service import ExportOptions
from aavc.application.services.selection_export_service import render_project_selection
from aavc.bootstrap.composition_root import FoundationServices
from aavc.domain.errors import AAVCError
from aavc.presentation.motion_preview import preview_scrub_seconds
from aavc.presentation.native_motion_playback import install_native_motion_preview
from aavc.presentation.navigation import UiRoute
from aavc.presentation.timeline_cursor_zoom import install_timeline_cursor_zoom
from aavc.presentation.timeline_in_out import install_timeline_in_out
from aavc.presentation.timeline_keyboard_seek import install_timeline_keyboard_seek
from aavc.presentation.timeline_magnetic_in_out import install_timeline_magnetic_in_out
from aavc.presentation.timeline_markers import install_timeline_markers
from aavc.presentation.timeline_play_selection import start_timeline_play_selection
from aavc.presentation.timeline_preview_seek import install_timeline_preview_seek
from aavc.presentation.timeline_ruler_seek import install_timeline_ruler_seek
from aavc.presentation.timeline_zoom_scroll import install_timeline_zoom_scroll
from aavc.presentation.windows.native_motion_window import NativeMotionMainWindow


def scene_split_seconds_from_slider(
    value: int,
    maximum: int,
    duration_seconds: float,
) -> float:
    """Map the editor playhead slider to a millisecond-precision Scene split point."""

    return round(preview_scrub_seconds(value, maximum, duration_seconds), 3)


class NativeMotionPreviewMainWindow(NativeMotionMainWindow):
    """Native-motion editor with playback plus direct timeline Scene editing."""

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        edit_menu: Any | None = None
        export_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "Edit":
                edit_menu = menu_action.menu()
            elif menu_action.text() == "Ekspor":
                export_menu = menu_action.menu()

        if edit_menu is not None:
            edit_menu.addSeparator()
            split_action = action_type("Split Scene di Playhead", self.window)
            split_action.setShortcut("Ctrl+B")
            split_action.triggered.connect(
                lambda _checked=False: self.split_selected_scene_at_playhead()
            )
            edit_menu.addAction(split_action)

            play_selection_action = action_type("Play Selection In–Out", self.window)
            play_selection_action.setShortcut("Ctrl+Space")
            play_selection_action.triggered.connect(
                lambda _checked=False: self.play_in_out_selection()
            )
            edit_menu.addAction(play_selection_action)

            loop_selection_action = action_type("Loop Selection In–Out", self.window)
            loop_selection_action.setShortcut("Ctrl+Shift+Space")
            loop_selection_action.triggered.connect(
                lambda _checked=False: self.loop_in_out_selection()
            )
            edit_menu.addAction(loop_selection_action)

        if export_menu is not None:
            export_menu.addSeparator()
            export_selection_action = action_type(
                "Ekspor Selection In–Out",
                self.window,
            )
            export_selection_action.triggered.connect(
                lambda _checked=False: self.open_export_selection()
            )
            export_menu.addAction(export_selection_action)

    def _session_render_selection(self) -> tuple[float, float] | None:
        project = self.services.project_session.current
        if project is None:
            return None
        raw_in = getattr(self.window, "_aavc_timeline_in_seconds", None)
        raw_out = getattr(self.window, "_aavc_timeline_out_seconds", None)
        if raw_in is None or raw_out is None:
            return None
        try:
            start_seconds = float(raw_in)
            end_seconds = float(raw_out)
        except (TypeError, ValueError):
            return None
        total_duration = sum(max(0.0, scene.duration_seconds) for scene in project.scenes)
        epsilon = 1e-6
        if start_seconds < -epsilon or end_seconds > total_duration + epsilon:
            return None
        start_seconds = max(0.0, start_seconds)
        end_seconds = min(total_duration, end_seconds)
        if end_seconds - start_seconds <= epsilon:
            return None
        return start_seconds, end_seconds

    def open_export_selection(self) -> None:
        from aavc.presentation.dialogs.export_settings import create_export_dialog

        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Ekspor Selection tidak tersedia",
                "Buat atau buka project terlebih dahulu.",
            )
            return
        selection = self._session_render_selection()
        if selection is None:
            self._show_project_notice(
                "Range In/Out belum siap",
                "Setel In point (I) dan Out point (O) terlebih dahulu sebelum mengekspor selection.",
            )
            return
        start_seconds, end_seconds = selection

        project_path = self.services.project_session.path
        if project_path is not None:
            default_directory = str(project_path.parent)
        else:
            default_directory = str(Path(project.source_docx).resolve().parent)
        default_name = (
            f"{project.title} - Selection {start_seconds:.3f}-{end_seconds:.3f}"
        )

        dialog = create_export_dialog(
            self.window,
            default_directory=default_directory,
            default_name=default_name,
            on_render=lambda options: self.render_active_selection(
                options,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
            ),
        )
        dialog.setWindowTitle("Ekspor Selection In–Out")
        dialog.setModal(True)
        dialog.show()
        self._active_dialog = dialog

    def render_active_selection(
        self,
        options: ExportOptions,
        *,
        start_seconds: float,
        end_seconds: float,
    ) -> bool:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QCursor
        from PySide6.QtWidgets import QApplication

        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Render Selection tidak tersedia",
                "Buat atau buka project terlebih dahulu.",
            )
            return False

        self.window.statusBar().showMessage(
            f"Render Selection {start_seconds:.3f}–{end_seconds:.3f} detik sedang berjalan…"
        )
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        QApplication.processEvents()
        try:
            result = render_project_selection(
                project,
                options,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
            )
        except (AAVCError, OSError, RuntimeError, ValueError) as error:
            self._show_project_error("Render Selection gagal", error)
            self.window.statusBar().showMessage("Render Selection gagal", 5000)
            return False
        finally:
            QApplication.restoreOverrideCursor()

        self.window.statusBar().showMessage(
            f"Render Selection selesai: {result.output_path}",
            8000,
        )
        self._show_project_notice(
            "Render Selection selesai",
            f"Video range In–Out berhasil dibuat:\n{result.output_path}",
        )
        return True

    def play_in_out_selection(self) -> None:
        project = self.services.project_session.current
        if project is None:
            self.window.statusBar().showMessage(
                "Buat atau buka project terlebih dahulu sebelum Play Selection.",
                6000,
            )
            return
        root = self._route_widgets.get(UiRoute.EDITOR)
        if root is None:
            self.window.statusBar().showMessage(
                "Buka Editor terlebih dahulu untuk Play Selection In–Out.",
                6000,
            )
            return
        started, message = start_timeline_play_selection(root, project)
        self.window.statusBar().showMessage(message, 7000 if started else 6000)

    def loop_in_out_selection(self) -> None:
        project = self.services.project_session.current
        if project is None:
            self.window.statusBar().showMessage(
                "Buat atau buka project terlebih dahulu sebelum Loop Selection.",
                6000,
            )
            return
        root = self._route_widgets.get(UiRoute.EDITOR)
        if root is None:
            self.window.statusBar().showMessage(
                "Buka Editor terlebih dahulu untuk Loop Selection In–Out.",
                6000,
            )
            return
        started, message = start_timeline_play_selection(root, project, loop=True)
        self.window.statusBar().showMessage(message, 7000 if started else 6000)

    def move_scene_to_index(self, scene_number: int, target_index: int) -> None:
        project = self.services.project_session.current
        if project is None:
            return

        source_index = next(
            (
                index
                for index, scene in enumerate(project.scenes)
                if scene.scene_number == scene_number
            ),
            None,
        )
        if source_index is None or source_index == target_index:
            return

        try:
            self.services.project_session.execute(
                MoveSceneToIndex(scene_number, target_index)
            )
        except ValueError as error:
            self.window.statusBar().showMessage(str(error), 5000)
            return

        self._selected_scene_number = scene_number
        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"Scene {scene_number:02d} dipindah ke posisi {target_index + 1} melalui timeline. "
            "Klik Simpan untuk menyimpan perubahan.",
            7000,
        )

    def split_selected_scene_at_playhead(self) -> None:
        from PySide6.QtWidgets import QSlider

        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Split Scene tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        scene_number = self._selected_scene_number
        if scene_number is None:
            self.window.statusBar().showMessage(
                "Pilih Scene terlebih dahulu sebelum melakukan Split.",
                5000,
            )
            return

        scene = next(
            (item for item in project.scenes if item.scene_number == scene_number),
            None,
        )
        if scene is None:
            self.window.statusBar().showMessage(
                f"Scene {scene_number} tidak ditemukan.",
                5000,
            )
            return

        root = self._route_widgets.get(UiRoute.EDITOR)
        if root is None:
            self.window.statusBar().showMessage(
                "Buka Editor untuk menentukan posisi playhead Split.",
                5000,
            )
            return
        sliders = root.findChildren(QSlider)
        progress_slider = sliders[0] if sliders else None
        if progress_slider is None:
            self.window.statusBar().showMessage(
                "Playhead preview tidak tersedia pada Editor aktif.",
                5000,
            )
            return

        split_seconds = scene_split_seconds_from_slider(
            progress_slider.value(),
            progress_slider.maximum(),
            scene.duration_seconds,
        )
        new_scene_number = max(item.scene_number for item in project.scenes) + 1
        try:
            session.execute(SplitScene(scene_number, split_seconds))
        except ValueError as error:
            self.window.statusBar().showMessage(
                f"Split tidak dilakukan: {error}. Geser playhead ke bagian tengah Scene.",
                7000,
            )
            return

        self._selected_scene_number = scene_number
        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"Scene {scene_number:02d} di-split pada {split_seconds:.3f} detik; "
            f"bagian kedua menjadi Scene {new_scene_number:02d}. "
            "Gunakan Undo untuk membatalkan atau klik Simpan untuk menyimpan perubahan.",
            9000,
        )

    def _mark_split_available(self, root: Any) -> None:
        from PySide6.QtWidgets import QLabel, QSlider

        for label in root.findChildren(QLabel):
            text = label.text()
            if "Split belum aktif." in text:
                label.setText(
                    text.replace(
                        "Split belum aktif.",
                        "Split: Ctrl+B pada playhead.",
                    )
                )
            elif "Split dan trim kiri belum aktif." in text:
                label.setText(
                    text.replace(
                        "Split dan trim kiri belum aktif.",
                        "Split: Ctrl+B pada playhead. Trim kiri belum aktif.",
                    )
                )
        sliders = root.findChildren(QSlider)
        if sliders:
            sliders[0].setToolTip(
                f"{sliders[0].toolTip()} Gunakan Ctrl+B untuk Split Scene pada posisi ini."
            )

    def refresh_editor_overview(self) -> None:
        super().refresh_editor_overview()
        project = self.services.project_session.current
        if project is None:
            return
        root = self._route_widgets.get(UiRoute.EDITOR)
        if root is not None:
            install_native_motion_preview(root, project)
            install_timeline_preview_seek(
                root,
                project,
                on_scene_reordered=self.move_scene_to_index,
                on_scene_resized=self.set_scene_duration,
            )
            self._mark_split_available(root)
            install_timeline_zoom_scroll(root, project)
            install_timeline_cursor_zoom(root, project)
            install_timeline_ruler_seek(root, project)
            install_timeline_keyboard_seek(root, project)
            install_timeline_markers(root, project)
            install_timeline_in_out(root, project)
            install_timeline_magnetic_in_out(root, project)


def create_native_motion_preview_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> NativeMotionPreviewMainWindow:
    return NativeMotionPreviewMainWindow(services, initial_state=initial_state)
