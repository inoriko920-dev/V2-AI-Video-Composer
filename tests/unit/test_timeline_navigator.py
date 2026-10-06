from __future__ import annotations

from aavc.presentation.timeline_navigator import (
    timeline_navigator_anchor_scroll_value,
    timeline_navigator_global_seconds_x,
    timeline_navigator_hit_region,
    timeline_navigator_range_geometry,
    timeline_navigator_scaled_x,
    timeline_navigator_scene_boundary_xs,
    timeline_navigator_scroll_value,
    timeline_navigator_viewport_geometry,
    timeline_navigator_zoom_percent_for_handle_width,
)


def test_full_track_view_uses_full_navigator_handle() -> None:
    assert timeline_navigator_viewport_geometry(240, 800, 800, 0, 0) == (0, 240)
    assert timeline_navigator_viewport_geometry(240, 0, 800, 0, 0) == (0, 240)


def test_viewport_geometry_tracks_scroll_ratio() -> None:
    assert timeline_navigator_viewport_geometry(
        200,
        1000,
        250,
        375,
        750,
    ) == (75, 50)


def test_very_long_track_keeps_minimum_draggable_handle() -> None:
    assert timeline_navigator_viewport_geometry(
        100,
        10000,
        500,
        4750,
        9500,
    ) == (38, 24)


def test_drag_handle_maps_back_to_main_scrollbar() -> None:
    assert timeline_navigator_scroll_value(75, 200, 50, 750) == 375
    assert timeline_navigator_scroll_value(0, 200, 50, 750) == 0
    assert timeline_navigator_scroll_value(150, 200, 50, 750) == 750


def test_drag_mapping_clamps_beyond_overview_edges() -> None:
    assert timeline_navigator_scroll_value(-100, 200, 50, 750) == 0
    assert timeline_navigator_scroll_value(500, 200, 50, 750) == 750
    assert timeline_navigator_scroll_value(10, 20, 20, 100) == 0


def test_track_pixel_scaling_clamps_to_navigator() -> None:
    assert timeline_navigator_scaled_x(500, 1000, 200) == 100
    assert timeline_navigator_scaled_x(-50, 1000, 200) == 0
    assert timeline_navigator_scaled_x(1500, 1000, 200) == 200
    assert timeline_navigator_scaled_x(20, 0, 200) == 0


def test_global_seconds_maps_to_navigator_coordinates() -> None:
    assert timeline_navigator_global_seconds_x(
        (10.0,),
        5.0,
        100,
        480,
        240,
    ) == 120
    assert timeline_navigator_global_seconds_x(
        (10.0,),
        -10.0,
        100,
        480,
        240,
    ) == 0
    assert timeline_navigator_global_seconds_x(
        (10.0,),
        999.0,
        100,
        480,
        240,
    ) == 240


def test_scene_boundary_ticks_follow_minimum_width_and_gap() -> None:
    assert timeline_navigator_scene_boundary_xs(
        (1.0, 1.0),
        100,
        115,
        115,
    ) == (0, 56, 115)


def test_in_out_range_geometry_uses_global_time_mapping() -> None:
    assert timeline_navigator_range_geometry(
        (10.0,),
        2.0,
        8.0,
        100,
        480,
        240,
    ) == (48, 144)
    assert timeline_navigator_range_geometry(
        (10.0,),
        None,
        8.0,
        100,
        480,
        240,
    ) is None


def test_navigator_hit_region_distinguishes_edges_and_pan_center() -> None:
    assert timeline_navigator_hit_region(50, 50, 100) == "left"
    assert timeline_navigator_hit_region(56, 50, 100) == "left"
    assert timeline_navigator_hit_region(100, 50, 100) == "pan"
    assert timeline_navigator_hit_region(144, 50, 100) == "right"
    assert timeline_navigator_hit_region(150, 50, 100) == "right"
    assert timeline_navigator_hit_region(20, 50, 100) == "outside"


def test_overlapping_edge_hit_area_prefers_nearest_edge() -> None:
    assert timeline_navigator_hit_region(55, 50, 10) == "left"
    assert timeline_navigator_hit_region(56, 50, 10) == "right"


def test_handle_width_maps_to_expected_zoom_range() -> None:
    durations = (20.0,)
    assert timeline_navigator_zoom_percent_for_handle_width(
        durations, 500, 200, 200
    ) == 52
    assert 98 <= timeline_navigator_zoom_percent_for_handle_width(
        durations, 500, 200, 104
    ) <= 102
    assert 197 <= timeline_navigator_zoom_percent_for_handle_width(
        durations, 500, 200, 52
    ) <= 203


def test_edge_zoom_can_reach_400_even_below_visual_minimum_handle() -> None:
    assert timeline_navigator_zoom_percent_for_handle_width(
        (20.0,),
        500,
        200,
        20,
    ) == 400


def test_anchor_scroll_preserves_requested_navigator_edge() -> None:
    assert timeline_navigator_anchor_scroll_value(
        "left", 75, 200, 50, 750
    ) == 375
    assert timeline_navigator_anchor_scroll_value(
        "right", 125, 200, 50, 750
    ) == 375
    assert timeline_navigator_anchor_scroll_value(
        "right", 200, 200, 50, 750
    ) == 750
