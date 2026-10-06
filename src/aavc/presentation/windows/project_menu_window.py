from __future__ import annotations

from typing import Any

from aavc.application.commands import SetProjectTitle
from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.view_navigation_window import ViewNavigationMainWindow


def project_menu_enabled(*, has_project: bool) -> bool:
    """Return whether project-scoped menu actions may be used."""

    return has_project


def project_title_changed(current_title: str, requested_title: str) -> bool:
    """Return whether a rename request would change the canonical title."""

    return requested_title.strip() != current_title


class ProjectMenuMainWindow(ViewNavigationMainWindow):
    """Expose safe project metadata actions through the runtime Project menu."""

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        self._rename_project_action: Any | None = None
        super().__init__(services, initial_state=initial_state)

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        project_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "Proyek":
                project_menu = menu_action.menu()
                break
        if project_menu is None:
            return

        project_menu.clear()
        rename_action = action_type("Ubah Nama Proyek…", self.window)
        rename_action.setObjectName("ProjectRenameAction")
        rename_action.triggered.connect(
            lambda _checked=False: self.rename_active_project()
        )
        project_menu.addAction(rename_action)
        self._rename_project_action = rename_action
        self._refresh_project_menu_state()

    def _refresh_project_menu_state(self) -> None:
        action = self._rename_project_action
        if action is None:
            return
        action.setEnabled(
            project_menu_enabled(
                has_project=self.services.project_session.current is not None
            )
        )

    def rename_active_project(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Ubah Nama Proyek tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            self._refresh_project_menu_state()
            return

        requested_title, accepted = QInputDialog.getText(
            self.window,
            "Ubah Nama Proyek",
            "Nama proyek:",
            text=project.title,
        )
        if not accepted:
            return
        if not project_title_changed(project.title, requested_title):
            self.window.statusBar().showMessage("Nama proyek tidak berubah.", 3000)
            return

        try:
            updated = session.execute(SetProjectTitle(requested_title))
        except ValueError as error:
            self._show_project_error("Gagal mengubah nama proyek", error)
            return

        self._refresh_window_title()
        self.refresh_editor_overview()
        self._refresh_project_menu_state()
        self.window.statusBar().showMessage(
            f"Nama proyek diubah menjadi: {updated.title}. "
            "Path file project tetap sama; klik Simpan untuk menyimpan perubahan.",
            7000,
        )

    def show_route(self, route: UiRoute) -> None:
        super().show_route(route)
        self._refresh_project_menu_state()


def create_project_menu_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> ProjectMenuMainWindow:
    return ProjectMenuMainWindow(services, initial_state=initial_state)
