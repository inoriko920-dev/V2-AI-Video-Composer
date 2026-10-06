from __future__ import annotations

from aavc.presentation.windows.edit_menu_state_window import EditMenuStateMainWindow
from aavc.presentation.windows.project_action_state_window import (
    ProjectActionStateMainWindow,
    project_action_state,
)


def test_project_action_state_window_preserves_edit_state_layer() -> None:
    assert issubclass(ProjectActionStateMainWindow, EditMenuStateMainWindow)


def test_project_actions_are_disabled_without_project() -> None:
    state = project_action_state(
        has_project=False,
        can_undo=False,
        can_redo=False,
        has_subtitle_source=False,
    )

    assert state.save is False
    assert state.save_as is False
    assert state.export is False
    assert state.undo is False
    assert state.redo is False
    assert state.import_media is False
    assert state.subtitle_editor is False


def test_project_actions_enable_core_workflows_with_active_project() -> None:
    state = project_action_state(
        has_project=True,
        can_undo=False,
        can_redo=False,
        has_subtitle_source=False,
    )

    assert state.save is True
    assert state.save_as is True
    assert state.export is True
    assert state.import_media is True
    assert state.subtitle_editor is False


def test_toolbar_history_actions_follow_session_history() -> None:
    state = project_action_state(
        has_project=True,
        can_undo=True,
        can_redo=False,
        has_subtitle_source=False,
    )

    assert state.undo is True
    assert state.redo is False


def test_subtitle_editor_requires_imported_subtitle_source() -> None:
    without_subtitle = project_action_state(
        has_project=True,
        can_undo=False,
        can_redo=False,
        has_subtitle_source=False,
    )
    with_subtitle = project_action_state(
        has_project=True,
        can_undo=False,
        can_redo=False,
        has_subtitle_source=True,
    )

    assert without_subtitle.subtitle_editor is False
    assert with_subtitle.subtitle_editor is True
