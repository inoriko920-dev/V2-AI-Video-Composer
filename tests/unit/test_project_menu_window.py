from __future__ import annotations

from aavc.presentation.windows.project_menu_window import (
    ProjectMenuMainWindow,
    project_menu_enabled,
    project_title_changed,
)
from aavc.presentation.windows.view_navigation_window import ViewNavigationMainWindow


def test_project_menu_window_preserves_live_navigation_layer() -> None:
    assert issubclass(ProjectMenuMainWindow, ViewNavigationMainWindow)


def test_project_menu_actions_require_active_project() -> None:
    assert project_menu_enabled(has_project=False) is False
    assert project_menu_enabled(has_project=True) is True


def test_project_title_change_ignores_outer_whitespace() -> None:
    assert project_title_changed("Nama Lama", " Nama Lama ") is False
    assert project_title_changed("Nama Lama", "Nama Baru") is True


def test_invalid_empty_title_still_reaches_canonical_command_validation() -> None:
    assert project_title_changed("Nama Lama", "   ") is True
