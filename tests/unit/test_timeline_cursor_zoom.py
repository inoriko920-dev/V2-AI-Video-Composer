from aavc.presentation.timeline_cursor_zoom import (
    timeline_cursor_anchor_scroll_value,
    timeline_cursor_zoom_percent,
    timeline_global_seconds_for_pixel_x,
)
from aavc.presentation.timeline_zoom_scroll import (
    timeline_global_seconds_pixel_x,
    timeline_scene_pixel_width,
)


def test_pixel_to_global_seconds_respects_minimum_scene_width() -> None:
    durations = (1.0, 10.0)

    # Scene 1 is visually clamped to the 56 px minimum at 100% zoom.
    assert timeline_global_seconds_for_pixel_x(durations, 28.0, 100) == 0.5
    assert timeline_global_seconds_for_pixel_x(durations, 56.0, 100) == 1.0


def test_pixel_in_inter_scene_gap_maps_to_shared_scene_boundary() -> None:
    durations = (2.0, 3.0)
    first_scene_end_x = timeline_scene_pixel_width(durations[0], 100)

    assert (
        timeline_global_seconds_for_pixel_x(
            durations,
            first_scene_end_x + 1.0,
            100,
        )
        == 2.0
    )


def test_ctrl_wheel_zoom_uses_25_percent_steps_and_clamps() -> None:
    assert timeline_cursor_zoom_percent(100, 120) == 125
    assert timeline_cursor_zoom_percent(100, -120) == 75
    assert timeline_cursor_zoom_percent(400, 120) == 400
    assert timeline_cursor_zoom_percent(50, -120) == 50
    assert timeline_cursor_zoom_percent(175, 0) == 175


def test_anchor_scroll_keeps_same_time_under_cursor_after_zoom() -> None:
    durations = (2.0, 10.0, 1.0)
    anchor_seconds = 6.0
    cursor_x = 140.0
    new_zoom = 200

    scroll_value = timeline_cursor_anchor_scroll_value(
        durations,
        anchor_seconds,
        cursor_x,
        new_zoom,
        maximum_scroll=5000,
    )
    anchor_x = timeline_global_seconds_pixel_x(durations, anchor_seconds, new_zoom)

    assert anchor_x - scroll_value == round(cursor_x)


def test_anchor_scroll_clamps_to_available_scroll_range() -> None:
    durations = (20.0,)

    assert (
        timeline_cursor_anchor_scroll_value(
            durations,
            anchor_seconds=0.0,
            cursor_viewport_x=200.0,
            zoom_percent=200,
            maximum_scroll=500,
        )
        == 0
    )
    assert (
        timeline_cursor_anchor_scroll_value(
            durations,
            anchor_seconds=20.0,
            cursor_viewport_x=0.0,
            zoom_percent=400,
            maximum_scroll=300,
        )
        == 300
    )
