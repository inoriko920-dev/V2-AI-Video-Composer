from __future__ import annotations

from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.view_navigation_window import (
    VIEW_NAVIGATION_ROUTES,
    view_route_enabled,
)


def test_view_navigation_exposes_only_live_target_routes() -> None:
    assert VIEW_NAVIGATION_ROUTES == (
        UiRoute.HOME,
        UiRoute.EDITOR,
        UiRoute.SUBTITLE_EDITOR,
        UiRoute.VALIDATION_CENTER,
    )


def test_home_is_always_available_without_project() -> None:
    assert view_route_enabled(UiRoute.HOME, has_project=False) is True


def test_project_views_are_disabled_without_active_project() -> None:
    assert view_route_enabled(UiRoute.EDITOR, has_project=False) is False
    assert view_route_enabled(UiRoute.SUBTITLE_EDITOR, has_project=False) is False
    assert view_route_enabled(UiRoute.VALIDATION_CENTER, has_project=False) is False


def test_project_views_enable_when_project_is_active() -> None:
    assert view_route_enabled(UiRoute.EDITOR, has_project=True) is True
    assert view_route_enabled(UiRoute.SUBTITLE_EDITOR, has_project=True) is True
    assert view_route_enabled(UiRoute.VALIDATION_CENTER, has_project=True) is True


def test_non_view_routes_never_enable_through_view_menu() -> None:
    assert view_route_enabled(UiRoute.NEW_PROJECT_DOCX, has_project=True) is False
    assert view_route_enabled(UiRoute.EXPORT_SETTINGS, has_project=True) is False
