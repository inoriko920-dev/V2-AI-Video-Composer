from __future__ import annotations

from aavc.presentation.windows.ai_menu_window import AiMenuMainWindow
from aavc.presentation.windows.edit_menu_state_window import (
    EditMenuStateMainWindow,
    edit_menu_action_state,
)


def test_edit_menu_state_window_preserves_ai_runtime_layer() -> None:
    assert issubclass(EditMenuStateMainWindow, AiMenuMainWindow)


def test_edit_menu_actions_are_disabled_without_project() -> None:
    state = edit_menu_action_state(
        has_project=False,
        has_selected_scene=False,
        can_undo=False,
        can_redo=False,
        selected_index=None,
        scene_count=0,
    )

    assert state.undo is False
    assert state.redo is False
    assert state.move_up is False
    assert state.move_down is False
    assert state.duplicate is False
    assert state.delete is False


def test_history_actions_follow_project_history_capabilities() -> None:
    state = edit_menu_action_state(
        has_project=True,
        has_selected_scene=True,
        can_undo=True,
        can_redo=False,
        selected_index=1,
        scene_count=3,
    )

    assert state.undo is True
    assert state.redo is False


def test_first_scene_disables_move_up_but_keeps_valid_scene_actions() -> None:
    state = edit_menu_action_state(
        has_project=True,
        has_selected_scene=True,
        can_undo=False,
        can_redo=False,
        selected_index=0,
        scene_count=3,
    )

    assert state.move_up is False
    assert state.move_down is True
    assert state.duplicate is True
    assert state.delete is True


def test_last_scene_disables_move_down() -> None:
    state = edit_menu_action_state(
        has_project=True,
        has_selected_scene=True,
        can_undo=False,
        can_redo=False,
        selected_index=2,
        scene_count=3,
    )

    assert state.move_up is True
    assert state.move_down is False


def test_only_scene_cannot_be_moved_or_deleted_but_can_be_duplicated() -> None:
    state = edit_menu_action_state(
        has_project=True,
        has_selected_scene=True,
        can_undo=False,
        can_redo=False,
        selected_index=0,
        scene_count=1,
    )

    assert state.move_up is False
    assert state.move_down is False
    assert state.duplicate is True
    assert state.delete is False
