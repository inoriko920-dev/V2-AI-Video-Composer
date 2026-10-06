import pytest

from aavc.presentation.native_motion_playback import (
    _elapsed_global_position,
    _scene_position_for_global_time,
)


def test_monotonic_clock_advances_by_elapsed_time_not_callback_count() -> None:
    assert _elapsed_global_position(2.0, 100.0, 101.0, 30.0) == pytest.approx(3.0)
    assert _elapsed_global_position(2.0, 100.0, 101.75, 30.0) == pytest.approx(3.75)


def test_monotonic_clock_clamps_at_project_end() -> None:
    assert _elapsed_global_position(9.5, 100.0, 105.0, 10.0) == pytest.approx(10.0)


def test_global_time_maps_across_scene_boundaries_with_residual() -> None:
    durations = (2.0, 3.0, 4.0)

    assert _scene_position_for_global_time(durations, 0.5) == (0, pytest.approx(0.5))
    assert _scene_position_for_global_time(durations, 2.0) == (1, pytest.approx(0.0))
    assert _scene_position_for_global_time(durations, 2.7) == (1, pytest.approx(0.7))
    assert _scene_position_for_global_time(durations, 5.4) == (2, pytest.approx(0.4))
    assert _scene_position_for_global_time(durations, 99.0) == (2, pytest.approx(4.0))


def test_global_time_can_skip_multiple_scenes_after_delayed_redraw() -> None:
    row, local = _scene_position_for_global_time((0.4, 0.4, 2.0), 1.25)

    assert row == 2
    assert local == pytest.approx(0.45)
