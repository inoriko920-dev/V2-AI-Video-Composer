from __future__ import annotations

from contextlib import suppress
from typing import Any

from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.help_window import HelpMainWindow

VIEW_NAVIGATION_ROUTES: tuple[UiRoute, ...] = (
    UiRoute.HOME,
    UiRoute.EDITOR,
    UiRoute.SUBTITLE_EDITOR,
    UiRoute.VALIDATION_CENTER,
)


def view_route_enabled(route: UiRoute, *, has_project: bool) -> bool:
    """Return whether a live View-menu route may be opened by the user."""

    if route is UiRoute.HOME:
        return True
    return has_project and route in VIEW_NAVIGATION_ROUTES


class ViewNavigationMainWindow(HelpMainWindow):
    """Replace the View placeholder with guarded navigation to live screens."""

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        self._view_actions: dict[UiRoute, Any] = {}
        super().__init__(services, initial_state=initial_state)

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        view_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "Tampilan":
                view_menu = menu_action.menu()
                break
        if view_menu is None:
            return

        view_menu.clear()
        self._view_actions.clear()

        home = action_type("Beranda", self.window)
        home.setObjectName("ViewHomeAction")
        home.triggered.connect(lambda _checked=False: self.open_home_view())
        view_menu.addAction(home)
        self._view_actions[UiRoute.HOME] = home

        editor = action_type("Editor Project", self.window)
        editor.setObjectName("ViewEditorAction")
        editor.triggered.connect(lambda _checked=False: self.open_editor_view())
        view_menu.addAction(editor)
        self._view_actions[UiRoute.EDITOR] = editor

        view_menu.addSeparator()

        subtitle = action_type("Subtitle", self.window)
        subtitle.setObjectName("ViewSubtitleAction")
        subtitle.triggered.connect(lambda _checked=False: self.open_subtitle_editor())
        view_menu.addAction(subtitle)
        self._view_actions[UiRoute.SUBTITLE_EDITOR] = subtitle

        validation = action_type("Validation Center", self.window)
        validation.setObjectName("ViewValidationAction")
        validation.triggered.connect(
            lambda _checked=False: self.open_validation_center()
        )
        view_menu.addAction(validation)
        self._view_actions[UiRoute.VALIDATION_CENTER] = validation

        self._refresh_view_navigation_state()

    def _build_toolbar(self, toolbar_type: Any, action_type: Any) -> None:
        super()._build_toolbar(toolbar_type, action_type)

        button = self._validation_button
        if button is None:
            return
        with suppress(TypeError, RuntimeError):
            button.clicked.disconnect()
        button.clicked.connect(
            lambda _checked=False: self.open_validation_center()
        )

    def _refresh_view_navigation_state(self) -> None:
        has_project = self.services.project_session.current is not None
        for route, action in self._view_actions.items():
            action.setEnabled(view_route_enabled(route, has_project=has_project))

    def open_home_view(self) -> None:
        """Open Home without replacing or clearing the active project session."""

        self.show_route(UiRoute.HOME)

    def open_editor_view(self) -> None:
        """Refresh and reopen the live editor for the active project."""

        if self.services.project_session.current is None:
            self._show_project_notice(
                "Editor Project tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return
        self.refresh_editor_overview()
        self.show_route(UiRoute.EDITOR)

    def open_validation_center(self) -> None:
        """Open live validation only when a real project session exists."""

        if self.services.project_session.current is None:
            self._show_project_notice(
                "Validation Center tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return
        self.show_route(UiRoute.VALIDATION_CENTER)

    def show_route(self, route: UiRoute) -> None:
        """Keep live navigation reachable from Home while a project is active."""

        super().show_route(route)
        self._refresh_view_navigation_state()

        if route is not UiRoute.HOME:
            return
        if self.services.project_session.current is None:
            return

        self.window.menuBar().setVisible(True)
        if self._toolbar is not None:
            self._toolbar.setVisible(True)


def create_view_navigation_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> ViewNavigationMainWindow:
    return ViewNavigationMainWindow(services, initial_state=initial_state)
