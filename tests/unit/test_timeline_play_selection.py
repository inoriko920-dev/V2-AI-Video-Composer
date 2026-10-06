from __future__ import annotations

import pytest

from aavc.presentation.timeline_play_selection import (
    timeline_play_selection_outcome,
    timeline_play_selection_range,
    timeline_play_selection_should_stop,
    timeline_timecode_seconds,
)


def test_play_selection_requires_two_distinct_points() -> None:
    assert timeline_play_selection_range(None, 3.0, 10.0) is None
    assert timeline_play_selection_range(2.0, None, 10.0) is None
    assert timeline_play_selection_range(4.0, 4.0, 10.0) is None


def test_play_selection_normalizes_order_and_clamps_to_project() -> None:
    assert timeline_play_selection_range(8.0, 2.0, 10.0) == (2.0, 8.0)
    assert timeline_play_selection_range(-3.0, 50.0, 10.0) == (0.0, 10.0)


def test_timecode_seconds_uses_project_fps() -> None:
    assert timeline_timecode_seconds("00:00:01:15", 30) == pytest.approx(1.5)
    assert timeline_timecode_seconds("01:02:03:12", 24) == pytest.approx(3723.5)
    assert timeline_timecode_seconds("00:00:00:30", 30) is None
    assert timeline_timecode_seconds("not-timecode", 30) is None


def test_play_selection_stops_at_out_across_scene_boundaries() -> None:
    durations = (2.0, 3.0, 4.0)

    assert not timeline_play_selection_should_stop(durations, 1, 2.49, 4.5)
    assert timeline_play_selection_should_stop(durations, 1, 2.5, 4.5)
    assert timeline_play_selection_should_stop(durations, 2, 0.0, 5.0)


def test_play_selection_stops_at_project_end() -> None:
    durations = (1.0, 2.0)

    assert not timeline_play_selection_should_stop(durations, 1, 1.99, 3.0)
    assert timeline_play_selection_should_stop(durations, 1, 2.0, 3.0)


def test_play_selection_outcome_continues_before_out() -> None:
    assert (
        timeline_play_selection_outcome(
            playback_active=True,
            reached_out=False,
            loop_enabled=False,
        )
        == "continue"
    )
    assert (
        timeline_play_selection_outcome(
            playback_active=True,
            reached_out=False,
            loop_enabled=True,
        )
        == "continue"
    )


def test_play_selection_outcome_stops_normal_mode_at_out() -> None:
    assert (
        timeline_play_selection_outcome(
            playback_active=True,
            reached_out=True,
            loop_enabled=False,
        )
        == "stop"
    )


def test_play_selection_outcome_restarts_loop_mode_at_out() -> None:
    assert (
        timeline_play_selection_outcome(
            playback_active=True,
            reached_out=True,
            loop_enabled=True,
        )
        == "restart"
    )


def test_play_selection_outcome_stops_when_user_pauses() -> None:
    assert (
        timeline_play_selection_outcome(
            playback_active=False,
            reached_out=False,
            loop_enabled=True,
        )
        == "stop"
    )
    assert (
        timeline_play_selection_outcome(
            playback_active=False,
            reached_out=True,
            loop_enabled=True,
        )
        == "stop"
    )
