import pytest

from aavc.presentation.timeline_ruler_seek import (
    timeline_ruler_seek_target,
    timeline_slider_value_for_local_seconds,
)


def test_ruler_seek_maps_pixels_to_scene_local_seconds() -> None:
    durations = (0.1, 2.0)

    assert timeline_ruler_seek_target(durations, 0, 100) == (0, 0.0)
    assert timeline_ruler_seek_target(durations, 28, 100) == pytest.approx((0, 0.05))
    assert timeline_ruler_seek_target(durations, 56, 100) == pytest.approx((0, 0.1))
    assert timeline_ruler_seek_target(durations, 59, 100) == (1, 0.0)
    assert timeline_ruler_seek_target(durations, 107, 100) == pytest.approx((1, 1.0))
    assert timeline_ruler_seek_target(durations, 155, 100) == pytest.approx((1, 2.0))


def test_ruler_seek_resolves_visual_spacing_to_nearest_scene_boundary() -> None:
    durations = (0.1, 2.0)

    assert timeline_ruler_seek_target(durations, 57, 100) == pytest.approx((0, 0.1))
    assert timeline_ruler_seek_target(durations, 58, 100) == (1, 0.0)


def test_ruler_seek_clamps_outside_track() -> None:
    durations = (1.0, 2.0)

    assert timeline_ruler_seek_target(durations, -500, 100) == (0, 0.0)
    assert timeline_ruler_seek_target(durations, 999999, 100) == pytest.approx((1, 2.0))
    assert timeline_ruler_seek_target((), 10, 100) is None


def test_ruler_seek_respects_minimum_scene_width_across_zoom() -> None:
    durations = (0.1, 2.0)

    assert timeline_ruler_seek_target(durations, 28, 200) == pytest.approx((0, 0.05))
    assert timeline_ruler_seek_target(durations, 59, 200) == (1, 0.0)
    assert timeline_ruler_seek_target(durations, 155, 200) == pytest.approx((1, 1.0))


def test_slider_value_maps_scene_local_seconds_and_clamps() -> None:
    assert timeline_slider_value_for_local_seconds(0.0, 4.0, 1000) == 0
    assert timeline_slider_value_for_local_seconds(2.0, 4.0, 1000) == 500
    assert timeline_slider_value_for_local_seconds(4.0, 4.0, 1000) == 1000
    assert timeline_slider_value_for_local_seconds(9.0, 4.0, 1000) == 1000
    assert timeline_slider_value_for_local_seconds(-1.0, 4.0, 1000) == 0
    assert timeline_slider_value_for_local_seconds(1.0, 0.0, 1000) == 0
    assert timeline_slider_value_for_local_seconds(1.0, 4.0, 0) == 0
