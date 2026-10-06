from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.windows.ai_menu_window import AiMenuMainWindow


@dataclass(frozen=True, slots=True)
class EditMenuActionState:
    undo: bool
    redo: bool
    move_up: bool
    move_down: bool
    duplicate: bool
    copy_animation: bool
    paste_animation: bool
    delete: bool


def edit_menu_action_state(
    *,
    has_project: bool,
    has_selected_scene: bool,
    can_undo: bool,
    can_redo: bool,
    selected_index: int | None,
    scene_count: int,
    selected_scene_number: int | None = None,
    selected_has_animation: bool = False,
    animation_copy_source_scene_number: int | None = None,
    animation_copy_source_exists: bool = False,
) -> EditMenuActionState:
    """Return truthful enabled-state for the existing Edit menu actions."""

    scene_ready = has_project and has_selected_scene and selected_index is not None
    move_up = (
        has_project
        and has_selected_scene
        and selected_index is not None
        and selected_index > 0
    )
    move_down = (
        has_project
        and has_selected_scene
        and selected_index is not None
        and selected_index < scene_count - 1
    )
    return EditMenuActionState(
        undo=has_project and can_undo,
        redo=has_project and can_redo,
        move_up=move_up,
        move_down=move_down,
        duplicate=scene_ready,
        copy_animation=scene_ready and selected_has_animation,
        paste_animation=(
            scene_ready
            and animation_copy_source_exists
            and animation_copy_source_scene_number is not None
            and selected_scene_number != animation_copy_source_scene_number
        ),
        delete=scene_ready and scene_count > 1,
    )


class EditMenuStateMainWindow(AiMenuMainWindow):
    """Keep legacy Edit actions synchronized with the live project/session state."""

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        self._edit_state_actions: dict[str, Any] = {}
        super().__init__(services, initial_state=initial_state)

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        edit_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "Edit":
                edit_menu = menu_action.menu()
                break
        if edit_menu is None:
            return

        action_names = {
            "Undo": "undo",
            "Redo": "redo",
            "Pindah Scene ke Atas": "move_up",
            "Pindah Scene ke Bawah": "move_down",
            "Duplikasi Scene": "duplicate",
            "Salin Animasi Scene": "copy_animation",
            "Tempel Animasi Scene": "paste_animation",
            "Hapus Scene": "delete",
        }
        self._edit_state_actions.clear()
        for action in edit_menu.actions():
            state_name = action_names.get(action.text())
            if state_name is not None:
                self._edit_state_actions[state_name] = action
        self._refresh_edit_menu_state()

    def _refresh_edit_menu_state(self) -> None:
        session = self.services.project_session
        project = session.current
        selected_index: int | None = None
        scene_count = 0
        selected_scene_number: int | None = None
        selected_has_animation = False
        copy_source = self._animation_copy_source_scene_number
        copy_source_exists = False
        if project is not None:
            scene_count = len(project.scenes)
            if self._selected_scene_number is not None:
                selected_index = next(
                    (
                        index
                        for index, scene in enumerate(project.scenes)
                        if scene.scene_number == self._selected_scene_number
                    ),
                    None,
                )
                if selected_index is not None:
                    selected_scene_number = self._selected_scene_number
                    selected_has_animation = any(
                        assignment.scene_number == selected_scene_number
                        for assignment in project.animations
                    )
            if copy_source is not None:
                copy_source_exists = any(
                    scene.scene_number == copy_source for scene in project.scenes
                )

        state = edit_menu_action_state(
            has_project=project is not None,
            has_selected_scene=selected_index is not None,
            can_undo=session.can_undo,
            can_redo=session.can_redo,
            selected_index=selected_index,
            scene_count=scene_count,
            selected_scene_number=selected_scene_number,
            selected_has_animation=selected_has_animation,
            animation_copy_source_scene_number=copy_source,
            animation_copy_source_exists=copy_source_exists,
        )
        for name, enabled in (
            ("undo", state.undo),
            ("redo", state.redo),
            ("move_up", state.move_up),
            ("move_down", state.move_down),
            ("duplicate", state.duplicate),
            ("copy_animation", state.copy_animation),
            ("paste_animation", state.paste_animation),
            ("delete", state.delete),
        ):
            action = self._edit_state_actions.get(name)
            if action is not None:
                action.setEnabled(enabled)

    def _remember_selected_scene(self, scene_number: int) -> None:
        super()._remember_selected_scene(scene_number)
        self._refresh_edit_menu_state()

    def refresh_editor_overview(self) -> None:
        super().refresh_editor_overview()
        self._refresh_edit_menu_state()

    def copy_selected_scene_animation(self) -> None:
        super().copy_selected_scene_animation()
        self._refresh_edit_menu_state()

    def paste_animation_to_selected_scene(self) -> None:
        super().paste_animation_to_selected_scene()
        self._refresh_edit_menu_state()


def create_edit_menu_state_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> EditMenuStateMainWindow:
    return EditMenuStateMainWindow(services, initial_state=initial_state)
