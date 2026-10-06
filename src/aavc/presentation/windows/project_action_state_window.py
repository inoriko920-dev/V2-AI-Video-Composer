from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.edit_menu_state_window import EditMenuStateMainWindow


@dataclass(frozen=True, slots=True)
class ProjectActionState:
    save: bool
    save_as: bool
    export: bool
    undo: bool
    redo: bool
    import_media: bool
    subtitle_editor: bool


def project_action_state(
    *,
    has_project: bool,
    can_undo: bool,
    can_redo: bool,
    has_subtitle_source: bool,
) -> ProjectActionState:
    """Return truthful availability for project-dependent menu and toolbar actions."""

    return ProjectActionState(
        save=has_project,
        save_as=has_project,
        export=has_project,
        undo=has_project and can_undo,
        redo=has_project and can_redo,
        import_media=has_project,
        subtitle_editor=has_project and has_subtitle_source,
    )


class ProjectActionStateMainWindow(EditMenuStateMainWindow):
    """Keep File, Export, and toolbar actions aligned with the live project state."""

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        self._project_state_controls: dict[str, list[Any]] = {}
        super().__init__(services, initial_state=initial_state)

    def _register_project_state_control(self, name: str, control: Any) -> None:
        self._project_state_controls.setdefault(name, []).append(control)

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        for menu_action in self.window.menuBar().actions():
            menu: Any | None = menu_action.menu()
            if menu is None:
                continue
            if menu_action.text() == "File":
                for action in menu.actions():
                    if action.text() == "Simpan":
                        self._register_project_state_control("save", action)
                    elif action.text() == "Simpan Sebagai…":
                        self._register_project_state_control("save_as", action)
            elif menu_action.text() == "Ekspor":
                for action in menu.actions():
                    if action.text() == "Ekspor Video":
                        self._register_project_state_control("export", action)

        self._refresh_project_action_state()

    def _build_toolbar(self, toolbar_type: Any, action_type: Any) -> None:
        super()._build_toolbar(toolbar_type, action_type)

        toolbar = self._toolbar
        if toolbar is None:
            return

        toolbar_actions = {
            "Simpan": "save",
            "Undo": "undo",
            "Redo": "redo",
            "Impor Media": "import_media",
            "Tambah Teks": "subtitle_editor",
        }
        for action in toolbar.actions():
            state_name = toolbar_actions.get(action.text())
            if state_name is not None:
                self._register_project_state_control(state_name, action)

        from PySide6.QtWidgets import QPushButton

        for button in toolbar.findChildren(QPushButton):
            if button.text() == "Ekspor Video":
                self._register_project_state_control("export", button)
                break

        self._refresh_project_action_state()

    def _refresh_project_action_state(self) -> None:
        session = self.services.project_session
        project = session.current
        state = project_action_state(
            has_project=project is not None,
            can_undo=session.can_undo,
            can_redo=session.can_redo,
            has_subtitle_source=bool(project and project.subtitle_source),
        )
        for name, enabled in (
            ("save", state.save),
            ("save_as", state.save_as),
            ("export", state.export),
            ("undo", state.undo),
            ("redo", state.redo),
            ("import_media", state.import_media),
            ("subtitle_editor", state.subtitle_editor),
        ):
            for control in self._project_state_controls.get(name, ()):
                control.setEnabled(enabled)

    def refresh_editor_overview(self) -> None:
        super().refresh_editor_overview()
        self._refresh_project_action_state()

    def show_route(self, route: UiRoute) -> None:
        super().show_route(route)
        self._refresh_project_action_state()


def create_project_action_state_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> ProjectActionStateMainWindow:
    return ProjectActionStateMainWindow(services, initial_state=initial_state)
