import pytest

from aavc.presentation.timeline_markers import (
    timeline_adjacent_marker,
    timeline_marker_global_seconds,
    timeline_marker_seek_target,
    timeline_marker_snap_seconds,
    timeline_toggle_marker,
)


def test_marker_snap_uses_project_fps_and_clamps_edges() -> None:
    assert timeline_marker_snap_seconds(1.016, 10.0, 30) == pytest.approx(1.0)
    assert timeline_marker_snap_seconds(1.02, 10.0, 30) == pytest.approx(
        1.033333,
        abs=1e-6,
    )
    assert timeline_marker_snap_seconds(-5.0, 10.0, 30) == 0.0
    assert timeline_marker_snap_seconds(99.0, 10.0, 30) == 10.0
    assert timeline_marker_snap_seconds(0.49, 10.0, 0) == 0.0


def test_toggle_marker_adds_then_removes_same_frame() -> None:
    markers, added = timeline_toggle_marker((), 1.01, 10.0, 30)

    assert added is True
    assert markers == (1.0,)

    markers, added = timeline_toggle_marker(markers, 1.015, 10.0, 30)

    assert added is False
    assert markers == ()


def test_toggle_marker_keeps_sorted_unique_frame_positions() -> None:
    markers, _ = timeline_toggle_marker((3.0, 1.0, 3.0), 2.02, 10.0, 30)

    assert markers == pytest.approx((1.0, 2.033333, 3.0), abs=1e-6)


def test_adjacent_marker_moves_without_wrapping() -> None:
    markers = (1.0, 2.5, 4.0)

    assert timeline_adjacent_marker(markers, 2.0, 1) == 2.5
    assert timeline_adjacent_marker(markers, 2.5, 1) == 4.0
    assert timeline_adjacent_marker(markers, 2.5, -1) == 1.0
    assert timeline_adjacent_marker(markers, 4.0, 1) is None
    assert timeline_adjacent_marker(markers, 1.0, -1) is None
    assert timeline_adjacent_marker(markers, 2.5, 0) is None


def test_marker_global_seconds_clamps_scene_and_local_position() -> None:
    durations = (2.0, 3.0, 4.0)

    assert timeline_marker_global_seconds(durations, 1, 1.5) == pytest.approx(3.5)
    assert timeline_marker_global_seconds(durations, -10, -1.0) == 0.0
    assert timeline_marker_global_seconds(durations, 99, 99.0) == pytest.approx(9.0)
    assert timeline_marker_global_seconds((), 0, 1.0) == 0.0


def test_marker_seek_target_maps_boundaries_to_next_scene() -> None:
    durations = (2.0, 3.0, 4.0)

    assert timeline_marker_seek_target(durations, 0.0) == (0, 0.0)
    assert timeline_marker_seek_target(durations, 2.0) == (1, 0.0)
    assert timeline_marker_seek_target(durations, 4.5) == pytest.approx((1, 2.5))
    assert timeline_marker_seek_target(durations, 5.0) == (2, 0.0)
    assert timeline_marker_seek_target(durations, 9.0) == (2, 4.0)
    assert timeline_marker_seek_target(durations, 99.0) == (2, 4.0)
    assert timeline_marker_seek_target((), 1.0) is None
