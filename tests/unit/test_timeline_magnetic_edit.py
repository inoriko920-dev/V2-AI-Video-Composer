from __future__ import annotations

import pytest

from aavc.presentation.timeline_magnetic_edit import (
    timeline_magnetic_resize_duration,
    timeline_magnetic_split_local_seconds,
    timeline_scene_start_seconds,
)
from aavc.presentation.timeline_zoom_scroll import timeline_global_seconds_pixel_x


def test_scene_start_seconds_uses_cumulative_project_time() -> None:
    durations = (2.0, 3.0, 4.0)

    assert timeline_scene_start_seconds(durations, 0) == 0.0
    assert timeline_scene_start_seconds(durations, 1) == 2.0
    assert timeline_scene_start_seconds(durations, 2) == 5.0


def test_resize_snaps_scene_end_to_scene_boundary() -> None:
    durations = (2.0, 3.0, 4.0)
    pointer_x = timeline_global_seconds_pixel_x(durations, 5.0, 100)

    duration, kind = timeline_magnetic_resize_duration(
        durations,
        1,
        2.8,
        pointer_x,
        100,
        30,
    )

    assert duration == pytest.approx(3.0)
    assert kind == "scene"


def test_resize_marker_target_overrides_fixed_grid_duration() -> None:
    durations = (2.0, 3.0, 4.0)
    pointer_x = timeline_global_seconds_pixel_x(durations, 4.4, 100)

    duration, kind = timeline_magnetic_resize_duration(
        durations,
        1,
        2.0,
        pointer_x,
        100,
        30,
        markers_seconds=(4.4,),
    )

    assert duration == pytest.approx(2.4)
    assert kind == "marker"


def test_resize_can_snap_to_active_playhead() -> None:
    durations = (2.0, 3.0, 4.0)
    pointer_x = timeline_global_seconds_pixel_x(durations, 4.5, 200)

    duration, kind = timeline_magnetic_resize_duration(
        durations,
        1,
        2.2,
        pointer_x,
        200,
        30,
        playhead_seconds=4.5,
    )

    assert duration == pytest.approx(2.5)
    assert kind == "playhead"


def test_resize_keeps_proposed_duration_outside_magnetic_radius() -> None:
    durations = (2.0, 3.0, 4.0)
    pointer_x = timeline_global_seconds_pixel_x(durations, 3.5, 400)

    duration, kind = timeline_magnetic_resize_duration(
        durations,
        1,
        1.6,
        pointer_x,
        400,
        30,
    )

    assert duration == pytest.approx(1.6)
    assert kind is None


def test_resize_rejects_target_at_or_before_scene_start() -> None:
    durations = (2.0, 3.0)
    pointer_x = timeline_global_seconds_pixel_x(durations, 2.0, 100)

    duration, kind = timeline_magnetic_resize_duration(
        durations,
        1,
        1.5,
        pointer_x,
        100,
        30,
    )

    assert duration == pytest.approx(1.5)
    assert kind is None


def test_split_snaps_to_nearby_marker_inside_selected_scene() -> None:
    durations = (2.0, 3.0, 4.0)

    local, snapped = timeline_magnetic_split_local_seconds(
        durations,
        1,
        1.04,
        100,
        30,
        markers_seconds=(3.0,),
    )

    assert local == pytest.approx(1.0)
    assert snapped is True


def test_split_does_not_snap_to_scene_boundary_marker() -> None:
    durations = (2.0, 3.0, 4.0)

    local, snapped = timeline_magnetic_split_local_seconds(
        durations,
        1,
        0.03,
        100,
        30,
        markers_seconds=(2.0, 5.0),
    )

    assert local == pytest.approx(0.03)
    assert snapped is False


def test_split_keeps_position_when_marker_is_outside_visual_radius() -> None:
    durations = (2.0, 3.0, 4.0)

    local, snapped = timeline_magnetic_split_local_seconds(
        durations,
        1,
        1.0,
        400,
        30,
        markers_seconds=(4.0,),
    )

    assert local == pytest.approx(1.0)
    assert snapped is False
