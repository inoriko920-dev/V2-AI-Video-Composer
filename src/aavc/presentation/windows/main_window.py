from __future__ import annotations

from pathlib import Path
from typing import Any

from aavc.application.commands import (
    RelinkAsset,
    SetNarrationAudio,
    SetSceneDuration,
    SetSubtitleAnimation,
    SetSubtitleSource,
    SetSubtitleStyle,
)
from aavc.application.services.export_service import ExportOptions, render_project
from aavc.application.services.media_import import classify_media_path
from aavc.application.services.validation import validate_project
from aavc.bootstrap.composition_root import FoundationServices
from aavc.domain.errors import AAVCError
from aavc.domain.project.models import SubtitleAnimationSettings, SubtitleStyle
from aavc.presentation.design_tokens import METRICS, app_stylesheet
from aavc.presentation.navigation import UiRoute, parse_route


def pending_feature_message(feature: str) -> tuple[str, str]:
    return (
        "Fitur belum terhubung",
        f"{feature} belum terhubung ke sesi proyek pada build ini. "
        "Tidak ada perubahan proyek yang dilakukan.",
    )


def ensure_project_suffix(path: str) -> str:
    return path if Path(path).suffix.lower() == ".aavcproj" else f"{path}.aavcproj"


def format_window_title(
    app_name: str,
    project_title: str | None,
    *,
    is_dirty: bool = False,
) -> str:
    if not project_title:
        return app_name
    dirty_marker = " *" if is_dirty else ""
    return f"{app_name} — Project: {project_title}{dirty_marker}"


class MainWindow:
    def __init__(self, services: FoundationServices, initial_state: str = "UI-002") -> None:
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMainWindow, QStackedWidget, QToolBar

        self.services = services
        self.window = QMainWindow()
        self.window.setObjectName("AAVCMainWindow")
        self.window.setWindowTitle(format_window_title(services.app_name, None))
        self.window.resize(1600, 900)
        self.window.setMinimumSize(1280, 720)
        self.window.setStyleSheet(app_stylesheet())
        self.stack = QStackedWidget()
        self.window.setCentralWidget(self.stack)
        self._route_widgets: dict[UiRoute, Any] = {}
        self._active_dialog: Any | None = None
        self._toolbar: Any | None = None
        self._validation_button: Any | None = None
        self._selected_scene_number: int | None = None
        self._build_menu(QAction)
        self._build_toolbar(QToolBar, QAction)
        self._build_pages()
        self.show_route(parse_route(initial_state))

    def _show_pending_feature(self, feature: str) -> None:
        from PySide6.QtWidgets import QMessageBox

        title, message = pending_feature_message(feature)
        QMessageBox.information(self.window, title, message)

    def _show_project_error(self, title: str, error: Exception) -> None:
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(self.window, title, str(error))

    def _show_project_notice(self, title: str, message: str) -> None:
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(self.window, title, message)

    def _refresh_window_title(self) -> None:
        session = self.services.project_session
        project = session.current
        self.window.setWindowTitle(
            format_window_title(
                self.services.app_name,
                project.title if project is not None else None,
                is_dirty=session.is_dirty,
            )
        )

    def _replace_route_widget(self, route: UiRoute, replacement: Any) -> None:
        previous = self._route_widgets[route]
        previous_index = self.stack.indexOf(previous)
        was_current = self.stack.currentWidget() is previous
        self.stack.removeWidget(previous)
        previous.deleteLater()
        self._route_widgets[route] = replacement
        if previous_index >= 0:
            self.stack.insertWidget(previous_index, replacement)
        else:
            self.stack.addWidget(replacement)
        if was_current:
            self.stack.setCurrentWidget(replacement)

    def _refresh_validation_badge(self) -> None:
        button = self._validation_button
        if button is None:
            return

        project = self.services.project_session.current
        if project is None:
            button.setText("✓ Validasi OK")
            button.setStyleSheet(
                "color:#15803D; background:#F0FDF4; border:1px solid #BBF7D0; "
                "border-radius:6px; padding:5px 9px; font-weight:600;"
            )
            return

        issues = validate_project(project)
        errors = sum(issue.severity == "ERROR" for issue in issues)
        warnings = sum(issue.severity == "WARNING" for issue in issues)
        if errors:
            button.setText(f"Validasi: {errors} Error")
            button.setStyleSheet(
                "color:#B91C1C; background:#FEF2F2; border:1px solid #FECACA; "
                "border-radius:6px; padding:5px 9px; font-weight:600;"
            )
        elif warnings:
            button.setText(f"Validasi: {warnings} Peringatan")
            button.setStyleSheet(
                "color:#B45309; background:#FFFBEB; border:1px solid #FDE68A; "
                "border-radius:6px; padding:5px 9px; font-weight:600;"
            )
        else:
            button.setText("✓ Validasi OK")
            button.setStyleSheet(
                "color:#15803D; background:#F0FDF4; border:1px solid #BBF7D0; "
                "border-radius:6px; padding:5px 9px; font-weight:600;"
            )

    def _remember_selected_scene(self, scene_number: int) -> None:
        self._selected_scene_number = scene_number

    def refresh_editor_overview(self) -> None:
        from aavc.presentation.screens.live_editor_overview import (
            create_live_editor_overview,
        )

        project = self.services.project_session.current
        if project is None:
            return
        replacement = create_live_editor_overview(
            project,
            on_set_scene_duration=self.set_scene_duration,
            selected_scene_number=self._selected_scene_number,
            on_scene_selected=self._remember_selected_scene,
        )
        self._replace_route_widget(UiRoute.EDITOR, replacement)

    def create_project_from_docx(self, scene_docx: str) -> None:
        from PySide6.QtWidgets import QFileDialog

        from aavc.application.services.vertical_slice import create_project_state

        source = Path(scene_docx).resolve()
        if not source.is_file():
            self._show_project_notice("Scene DOCX belum dipilih", "Pilih file Scene DOCX terlebih dahulu.")
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

    def save_project(self) -> None:
        try:
            saved = self.services.project_session.save()
        except ValueError as error:
            self._show_project_notice("Simpan tidak tersedia", str(error))
            return
        except (AAVCError, OSError) as error:
            self._show_project_error("Gagal menyimpan proyek", error)
            return
        self._refresh_window_title()
        self.window.statusBar().showMessage(f"Proyek disimpan: {saved}", 5000)

    def undo_project(self) -> None:
        subtitle_was_open = self.stack.currentWidget() is self._route_widgets[UiRoute.SUBTITLE_EDITOR]
        try:
            self.services.project_session.undo()
        except ValueError as error:
            self.window.statusBar().showMessage(f"Undo tidak tersedia: {error}", 5000)
            return
        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        if subtitle_was_open:
            project = self.services.project_session.current
            if project is not None and project.subtitle_source:
                self.open_subtitle_editor()
        self.window.statusBar().showMessage("Undo berhasil", 3000)

    def redo_project(self) -> None:
        subtitle_was_open = self.stack.currentWidget() is self._route_widgets[UiRoute.SUBTITLE_EDITOR]
        try:
            self.services.project_session.redo()
        except ValueError as error:
            self.window.statusBar().showMessage(f"Redo tidak tersedia: {error}", 5000)
            return
        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        if subtitle_was_open:
            project = self.services.project_session.current
            if project is not None and project.subtitle_source:
                self.open_subtitle_editor()
        self.window.statusBar().showMessage("Redo berhasil", 3000)

    def set_scene_duration(self, scene_number: int, duration_seconds: float) -> None:
        try:
            self.services.project_session.execute(
                SetSceneDuration(scene_number, duration_seconds)
            )
        except (AAVCError, ValueError) as error:
            self._show_project_error("Gagal mengubah durasi Scene", error)
            return
        self._selected_scene_number = scene_number
        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"Durasi Scene {scene_number:02d} diubah menjadi {duration_seconds:.3f} detik. "
            "Klik Simpan untuk menyimpan perubahan.",
            7000,
        )

    def set_subtitle_style(self, style: SubtitleStyle) -> None:
        try:
            self.services.project_session.execute(SetSubtitleStyle(style))
        except (AAVCError, ValueError) as error:
            self._show_project_error("Gagal mengubah gaya subtitle", error)
            return
        self._refresh_window_title()
        self.refresh_editor_overview()
        self.open_subtitle_editor()
        self.window.statusBar().showMessage(
            f"Gaya subtitle diterapkan: {style.preset_name}. "
            "Klik Simpan untuk menyimpan perubahan.",
            7000,
        )

    def set_subtitle_animation(self, animation: SubtitleAnimationSettings) -> None:
        try:
            self.services.project_session.execute(SetSubtitleAnimation(animation))
        except (AAVCError, ValueError) as error:
            self._show_project_error("Gagal mengubah animasi subtitle", error)
            return
        self._refresh_window_title()
        self.refresh_editor_overview()
        self.open_subtitle_editor()
        self.window.statusBar().showMessage(
            f"Animasi subtitle diterapkan: {animation.preset}. "
            "Klik Simpan untuk menyimpan perubahan.",
            7000,
        )

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
            kind = classify_media_path(chosen)
            if kind == "subtitle":
                self.services.project_session.execute(SetSubtitleSource(chosen))
                media_label = "Subtitle SRT"
            else:
                self.services.project_session.execute(SetNarrationAudio(chosen))
                media_label = "Narasi audio"
        except (AAVCError, OSError, ValueError) as error:
            self._show_project_error("Impor Media gagal", error)
            return

        self._refresh_window_title()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"{media_label} diimpor: {Path(chosen).name}. "
            "Klik Simpan untuk menyimpan perubahan.",
            7000,
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

        try:
            replacement = create_live_subtitle_screen(
                project.subtitle_source,
                style=project.subtitle_style,
                animation=project.subtitle_animation,
                on_apply_style=self.set_subtitle_style,
                on_apply_animation=self.set_subtitle_animation,
                on_reload=self.open_subtitle_editor,
            )
        except (OSError, ValueError) as error:
            self._show_project_error("Gagal membaca subtitle", error)
            return

        self._replace_route_widget(UiRoute.SUBTITLE_EDITOR, replacement)
        self.show_route(UiRoute.SUBTITLE_EDITOR)
        self.window.statusBar().showMessage(
            f"Subtitle dimuat: {Path(project.subtitle_source).name}",
            5000,
        )

    def relink_asset_from_validation(self, asset_id: str) -> None:
        from PySide6.QtWidgets import QFileDialog

        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Relink tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        chosen, _ = QFileDialog.getOpenFileName(
            self.window,
            f"Relink {asset_id}",
            project.asset_directory,
            "Gambar (*.png *.jpg *.jpeg *.webp);;Semua File (*.*)",
        )
        if chosen:
            try:
                self.services.project_session.execute(RelinkAsset(asset_id, chosen))
            except (AAVCError, OSError, ValueError) as error:
                self._show_project_error("Relink gagal", error)
            else:
                self._refresh_window_title()
                self._refresh_validation_badge()
                self.refresh_editor_overview()
                self.window.statusBar().showMessage(
                    f"{asset_id} direlink. Klik Simpan untuk menyimpan perubahan.",
                    6000,
                )
        self.open_validation()

    def render_active_project(self, options: ExportOptions) -> bool:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QCursor
        from PySide6.QtWidgets import QApplication

        project = self.services.project_session.current
        if project is None:
            self._show_project_notice(
                "Render tidak tersedia",
                "Buat atau buka proyek terlebih dahulu sebelum mengekspor video.",
            )
            return False

        self.window.statusBar().showMessage("Render sedang berjalan…")
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        QApplication.processEvents()
        try:
            result = render_project(project, options)
        except (AAVCError, OSError, RuntimeError, ValueError) as error:
            self._show_project_error("Render gagal", error)
            self.window.statusBar().showMessage("Render gagal", 5000)
            return False
        finally:
            QApplication.restoreOverrideCursor()

        self.window.statusBar().showMessage(f"Render selesai: {result.output_path}", 8000)
        self._show_project_notice("Render selesai", f"Video berhasil dibuat:\n{result.output_path}")
        return True

    def _build_menu(self, action_type: Any) -> None:
        menu_bar = self.window.menuBar()
        for name in [
            "File",
            "Edit",
            "Proyek",
            "Tampilan",
            "Animasi",
            "AI",
            "Ekspor",
            "Bantuan",
        ]:
            menu = menu_bar.addMenu(name)
            if name == "File":
                new_action = action_type("Proyek Baru", self.window)
                new_action.triggered.connect(
                    lambda: self.show_route(UiRoute.NEW_PROJECT_DOCX)
                )
                menu.addAction(new_action)
                open_action = action_type("Buka Proyek", self.window)
                open_action.triggered.connect(self.open_project)
                menu.addAction(open_action)
                menu.addSeparator()
                save_action = action_type("Simpan", self.window)
                save_action.triggered.connect(self.save_project)
                menu.addAction(save_action)
                exit_action = action_type("Keluar", self.window)
                exit_action.triggered.connect(self.window.close)
                menu.addAction(exit_action)
            elif name == "Ekspor":
                export_action = action_type("Ekspor Video", self.window)
                export_action.triggered.connect(self.open_export)
                menu.addAction(export_action)
            elif name == "Bantuan":
                help_action = action_type("Shortcut & Bantuan Cepat", self.window)
                help_action.triggered.connect(
                    lambda: self._show_pending_feature("Shortcut & Bantuan Cepat")
                )
                menu.addAction(help_action)
            else:
                placeholder_action = action_type(f"{name} — menu", self.window)
                placeholder_action.triggered.connect(
                    lambda _checked=False, feature=name: self._show_pending_feature(
                        f"Menu {feature}"
                    )
                )
                menu.addAction(placeholder_action)

    def _build_toolbar(self, toolbar_type: Any, action_type: Any) -> None:
        from PySide6.QtWidgets import (
            QComboBox,
            QLabel,
            QPushButton,
            QSizePolicy,
            QWidget,
        )

        toolbar = toolbar_type("Utama", self.window)
        toolbar.setMovable(False)
        toolbar.setFixedHeight(METRICS.toolbar_h)
        actions = [
            ("Baru", lambda: self.show_route(UiRoute.NEW_PROJECT_DOCX)),
            ("Buka", self.open_project),
            ("Simpan", self.save_project),
            ("Undo", self.undo_project),
            ("Redo", self.redo_project),
            ("Impor Media", self.import_media),
            ("Tambah Teks", self.open_subtitle_editor),
            ("Rekam Narasi", lambda: self._show_pending_feature("Rekam Narasi")),
        ]
        for text, callback in actions:
            action = action_type(text, self.window)
            action.triggered.connect(callback)
            toolbar.addAction(action)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Mode Animasi"))
        animation_mode = QComboBox()
        animation_mode.addItems(["Auto (AI)", "Random App", "Manual"])
        animation_mode.setMaximumWidth(130)
        toolbar.addWidget(animation_mode)

        validation = QPushButton("✓ Validasi OK")
        validation.setStyleSheet(
            "color:#15803D; background:#F0FDF4; border:1px solid #BBF7D0; "
            "border-radius:6px; padding:5px 9px; font-weight:600;"
        )
        validation.clicked.connect(lambda: self.show_route(UiRoute.VALIDATION_CENTER))
        toolbar.addWidget(validation)
        self._validation_button = validation

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        export_button = QPushButton("Ekspor Video")
        export_button.setProperty("primary", True)
        export_button.clicked.connect(self.open_export)
        toolbar.addWidget(export_button)
        self.window.addToolBar(toolbar)
        self._toolbar = toolbar

    def _build_pages(self) -> None:
        from aavc.presentation.screens.home import create_home_screen
        from aavc.presentation.screens.new_project import create_new_project_screen
        from aavc.presentation.widgets.editor_shell import create_editor_shell

        self._route_widgets[UiRoute.HOME] = create_home_screen(
            lambda: self.show_route(UiRoute.NEW_PROJECT_DOCX),
            self.open_project,
            getattr(self, "open_quick_help", None),
        )
        self._route_widgets[UiRoute.NEW_PROJECT_DOCX] = create_new_project_screen(
            lambda: self.show_route(UiRoute.HOME),
            self.create_project_from_docx,
        )
        self._route_widgets[UiRoute.EDITOR] = create_editor_shell("overview").root
        self._route_widgets[UiRoute.SCENE_SINGLE] = create_editor_shell("single").root
        self._route_widgets[UiRoute.SCENE_DOUBLE] = create_editor_shell("double").root
        self._route_widgets[UiRoute.SUBTITLE_EDITOR] = create_editor_shell("subtitle").root
        self._route_widgets[UiRoute.EXPORT_SETTINGS] = create_editor_shell("subtitle").root
        self._route_widgets[UiRoute.VALIDATION_CENTER] = create_editor_shell("overview").root
        for widget in self._route_widgets.values():
            self.stack.addWidget(widget)

    def show_route(self, route: UiRoute) -> None:
        widget = self._route_widgets[route]
        self.stack.setCurrentWidget(widget)
        self.window.setProperty("ui_state", route.value)
        editor_chrome = route not in {UiRoute.HOME, UiRoute.NEW_PROJECT_DOCX}
        self.window.menuBar().setVisible(editor_chrome)
        if self._toolbar is not None:
            self._toolbar.setVisible(editor_chrome)
        if route is UiRoute.EXPORT_SETTINGS:
            self.open_export()
        elif route is UiRoute.VALIDATION_CENTER:
            self.open_validation()

    def open_export(self) -> None:
        from aavc.presentation.dialogs.export_settings import create_export_dialog

        project = self.services.project_session.current
        project_path = self.services.project_session.path
        if project is not None:
            default_name = f"{project.title} - Final"
            if project_path is not None:
                default_directory = str(project_path.parent)
            else:
                default_directory = str(Path(project.source_docx).resolve().parent)
            dialog = create_export_dialog(
                self.window,
                default_directory=default_directory,
                default_name=default_name,
                on_render=self.render_active_project,
            )
        else:
            dialog = create_export_dialog(
                self.window,
                on_render=self.render_active_project,
            )
        dialog.setModal(True)
        dialog.show()
        self._active_dialog = dialog

    def open_validation(self) -> None:
        from aavc.presentation.dialogs.validation_center import create_validation_dialog

        project = self.services.project_session.current
        if project is None:
            dialog = create_validation_dialog(self.window)
        else:
            issues = validate_project(project)
            dialog = create_validation_dialog(
                self.window,
                issues=issues,
                on_revalidate=self.open_validation,
                on_relink=self.relink_asset_from_validation,
            )
        dialog.setModal(False)
        dialog.show()
        self._active_dialog = dialog
        self._refresh_validation_badge()

    def show(self) -> None:
        self.window.show()

    def resize(self, width: int, height: int) -> None:
        self.window.resize(width, height)

    def grab(self) -> Any:
        from PySide6.QtCore import QPoint, QRect
        from PySide6.QtGui import QColor, QPainter, QPixmap

        base = self.window.grab()
        dialog = self._active_dialog
        if dialog is None or not dialog.isVisible():
            return base

        dialog_grab = dialog.grab()
        result = QPixmap(base)
        painter = QPainter(result)
        route = str(self.window.property("ui_state") or "")
        if route == UiRoute.EXPORT_SETTINGS.value:
            painter.fillRect(
                QRect(0, 0, result.width(), result.height()),
                QColor(23, 32, 51, 80),
            )
            x = max(0, (result.width() - dialog_grab.width()) // 2)
            y = max(0, (result.height() - dialog_grab.height()) // 2)
        elif route == UiRoute.VALIDATION_CENTER.value:
            x = max(0, result.width() - dialog_grab.width())
            y = max(0, METRICS.menu_h + METRICS.toolbar_h)
        else:
            global_pos = dialog.mapToGlobal(QPoint(0, 0))
            window_global = self.window.mapToGlobal(QPoint(0, 0))
            x = global_pos.x() - window_global.x()
            y = global_pos.y() - window_global.y()
        painter.drawPixmap(x, y, dialog_grab)
        painter.end()
        return result

    def close(self) -> None:
        self.window.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.window, name)


def create_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> MainWindow:
    return MainWindow(services, initial_state=initial_state)
