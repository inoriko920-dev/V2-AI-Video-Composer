from aavc.presentation.navigation import ROUTES, UiRoute, parse_route


def test_representative_routes_are_frozen_ui_ids() -> None:
    assert {r.value for r in UiRoute} == {"UI-002","UI-003","UI-010","UI-013","UI-014","UI-027","UI-035","UI-041"}
    assert len(ROUTES) == 8
    assert parse_route("ui-027") is UiRoute.SUBTITLE_EDITOR
