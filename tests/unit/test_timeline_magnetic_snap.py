from __future__ import annotations

import pytest

from aavc.presentation.timeline_magnetic_snap import (
    timeline_magnetic_snap_target,
    timeline_scene_boundaries_seconds,
)
from aavc.presentation.timeline_zoom_scroll import timeline_global_seconds_pixel_x


def test_scene_boundaries_include_project_edges() -> None:
    assert timeline_scene_boundaries_seconds((2.0, 3.5, 1.25)) == (
        0.0,
        2.0,
        5.5,
        6.75,
    )


def test_magnetic_snap_uses_scene_boundary_with_visual_mapping() -> None:
    durations = (0.2, 3.0, 1.0)
    boundary_seconds = 0.2
    boundary_x = timeline_global_seconds_pixel_x(durations, boundary_seconds, 100)

    snapped = timeline_magnetic_snap_target(
        durations,
        boundary_x + 6,
        100,
        30,
        tolerance_px=8,
    )

    assert snapped is not None
    seconds, kind = snapped
    assert seconds == pytest.approx(0.2)
    assert kind == "scene"


def test_magnetic_snap_prefers_nearest_marker() -> None:
    durations = (2.0, 3.0, 4.0)
    marker = 4.0
    marker_x = timeline_global_seconds_pixel_x(durations, marker, 200)

    snapped = timeline_magnetic_snap_target(
        durations,
        marker_x + 3,
        200,
        30,
        markers_seconds=(1.0, marker, 7.0),
        tolerance_px=8,
    )

    assert snapped == (4.0, "marker")


def test_magnetic_snap_prefers_playhead_on_exact_visual_tie() -> None:
    durations = (2.0, 3.0)
    target = 1.0
    target_x = timeline_global_seconds_pixel_x(durations, target, 100)

    snapped = timeline_magnetic_snap_target(
        durations,
        target_x,
        100,
        30,
        markers_seconds=(target,),
        playhead_seconds=target,
    )

    assert snapped == (1.0, "playhead")


def test_magnetic_snap_returns_none_outside_tolerance() -> None:
    durations = (2.0, 3.0)
    marker_x = timeline_global_seconds_pixel_x(durations, 1.0, 100)

    snapped = timeline_magnetic_snap_target(
        durations,
        marker_x + 20,
        100,
        30,
        markers_seconds=(1.0,),
        tolerance_px=8,
    )

    assert snapped is None


def test_magnetic_snap_scene_boundary_remains_frame_snapped() -> None:
    durations = (2.04, 3.0)
    raw_boundary_x = timeline_global_seconds_pixel_x(durations, 2.04, 100)

    snapped = timeline_magnetic_snap_target(
        durations,
        raw_boundary_x,
        100,
        30,
        tolerance_px=8,
    )

    assert snapped is not None
    seconds, kind = snapped
    assert seconds == pytest.approx(2.033333, abs=1e-6)
    assert kind == "scene"


def test_magnetic_snap_respects_zoom_and_minimum_scene_width() -> None:
    durations = (0.05, 2.0)
    marker = 0.05
    marker_x = timeline_global_seconds_pixel_x(durations, marker, 400)

    snapped = timeline_magnetic_snap_target(
        durations,
        marker_x - 5,
        400,
        60,
        markers_seconds=(marker,),
        tolerance_px=8,
    )

    assert snapped is not None
    seconds, kind = snapped
    assert seconds == pytest.approx(0.05)
    assert kind == "marker"
