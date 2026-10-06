from __future__ import annotations

import pytest

from aavc.presentation.timeline_in_out import (
    timeline_drag_in_out_point,
    timeline_in_out_drag_seconds,
    timeline_in_out_duration_seconds,
    timeline_in_out_hit_point,
    timeline_set_in_out_point,
)
from aavc.presentation.timeline_markers import timeline_marker_seek_target
from aavc.presentation.timeline_zoom_scroll import (
    TIMELINE_TRACK_SPACING_PX,
    timeline_global_seconds_pixel_x,
    timeline_scene_pixel_width,
)


def test_set_in_point_snaps_to_project_frame() -> None:
    in_point, out_point = timeline_set_in_out_point(
        None,
        None,
        "in",
        1.016,
        10.0,
        30,
    )

    assert in_point == 1.0
    assert out_point is None


def test_setting_opposite_point_normalizes_range_order() -> None:
    in_point, out_point = timeline_set_in_out_point(
        None,
        2.0,
        "in",
        4.0,
        10.0,
        30,
    )

    assert in_point == 2.0
    assert out_point == 4.0


def test_setting_out_before_existing_in_normalizes_range_order() -> None:
    in_point, out_point = timeline_set_in_out_point(
        6.0,
        None,
        "out",
        3.0,
        10.0,
        30,
    )

    assert in_point == 3.0
    assert out_point == 6.0


def test_equal_in_and_out_never_leave_zero_length_range() -> None:
    in_point, out_point = timeline_set_in_out_point(
        3.0,
        None,
        "out",
        3.0,
        10.0,
        30,
    )

    assert in_point is None
    assert out_point == 3.0


def test_drag_in_clamps_one_frame_before_out() -> None:
    in_point, out_point = timeline_drag_in_out_point(
        2.0,
        4.0,
        "in",
        8.0,
        10.0,
        30,
    )

    assert in_point == pytest.approx(3.966667)
    assert out_point == 4.0


def test_drag_out_clamps_one_frame_after_in() -> None:
    in_point, out_point = timeline_drag_in_out_point(
        2.0,
        4.0,
        "out",
        0.5,
        10.0,
        30,
    )

    assert in_point == 2.0
    assert out_point == pytest.approx(2.033333)


def test_drag_single_point_can_move_without_partner() -> None:
    assert timeline_drag_in_out_point(
        2.0,
        None,
        "in",
        8.0,
        10.0,
        30,
    ) == (8.0, None)
    assert timeline_drag_in_out_point(
        None,
        7.0,
        "out",
        1.0,
        10.0,
        30,
    ) == (None, 1.0)


def test_in_out_duration_requires_complete_range() -> None:
    assert timeline_in_out_duration_seconds(None, 4.0) == 0.0
    assert timeline_in_out_duration_seconds(2.25, None) == 0.0
    assert timeline_in_out_duration_seconds(2.25, 5.75) == pytest.approx(3.5)


def test_global_range_endpoint_maps_to_scene_local_position() -> None:
    durations = (2.0, 3.0, 4.0)

    assert timeline_marker_seek_target(durations, 2.0) == (1, 0.0)
    assert timeline_marker_seek_target(durations, 4.5) == (1, 2.5)
    assert timeline_marker_seek_target(durations, 9.0) == (2, 4.0)


def test_drag_pixel_round_trip_respects_zoom_and_minimum_scene_width() -> None:
    durations = (0.1, 3.0, 4.0)
    target_seconds = 1.6

    for zoom in (50, 100, 200, 400):
        x = timeline_global_seconds_pixel_x(durations, target_seconds, zoom)
        resolved = timeline_in_out_drag_seconds(durations, x, zoom)
        assert resolved == pytest.approx(target_seconds, abs=0.02)


def test_drag_pixel_in_scene_gap_maps_to_shared_boundary_time() -> None:
    durations = (2.0, 3.0)
    first_width = timeline_scene_pixel_width(durations[0], 100)

    for gap_offset in range(1, TIMELINE_TRACK_SPACING_PX):
        resolved = timeline_in_out_drag_seconds(
            durations,
            first_width + gap_offset,
            100,
        )
        assert resolved == pytest.approx(2.0)


def test_handle_hit_test_prefers_nearest_visible_point() -> None:
    durations = (2.0, 3.0, 4.0)
    in_x = timeline_global_seconds_pixel_x(durations, 2.0, 100)
    out_x = timeline_global_seconds_pixel_x(durations, 6.0, 100)

    assert timeline_in_out_hit_point(durations, 2.0, 6.0, in_x + 4, 100) == "in"
    assert timeline_in_out_hit_point(durations, 2.0, 6.0, out_x - 4, 100) == "out"
    assert timeline_in_out_hit_point(durations, 2.0, 6.0, in_x + 20, 100) is None
