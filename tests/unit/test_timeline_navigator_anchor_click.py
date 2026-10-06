from __future__ import annotations

from aavc.presentation.timeline_navigator import timeline_navigator_global_seconds_x
from aavc.presentation.timeline_navigator_anchor_click import (
    timeline_navigator_anchor_center_scroll_value,
    timeline_navigator_anchor_hit,
    timeline_navigator_anchor_timecode,
    timeline_navigator_anchor_tooltip,
)


def test_anchor_hit_selects_nearest_marker() -> None:
    durations = (10.0, 10.0)
    zoom = 100
    track_width = 1200
    navigator_width = 240
    marker_x = timeline_navigator_global_seconds_x(
        durations,
        5.0,
        zoom,
        track_width,
        navigator_width,
    )

    assert timeline_navigator_anchor_hit(
        marker_x + 2,
        durations,
        (5.0, 15.0),
        None,
        None,
        zoom,
        track_width,
        navigator_width,
    ) == ("marker", 5.0)


def test_in_out_anchor_wins_exact_tie_against_marker() -> None:
    durations = (20.0,)
    zoom = 100
    track_width = 1000
    navigator_width = 200
    anchor_x = timeline_navigator_global_seconds_x(
        durations,
        8.0,
        zoom,
        track_width,
        navigator_width,
    )

    assert timeline_navigator_anchor_hit(
        anchor_x,
        durations,
        (8.0,),
        8.0,
        14.0,
        zoom,
        track_width,
        navigator_width,
    ) == ("in", 8.0)


def test_out_anchor_is_clickable_without_in_point() -> None:
    durations = (20.0,)
    zoom = 100
    track_width = 1000
    navigator_width = 200
    anchor_x = timeline_navigator_global_seconds_x(
        durations,
        14.0,
        zoom,
        track_width,
        navigator_width,
    )

    assert timeline_navigator_anchor_hit(
        anchor_x,
        durations,
        (),
        None,
        14.0,
        zoom,
        track_width,
        navigator_width,
    ) == ("out", 14.0)


def test_anchor_hit_returns_none_outside_radius() -> None:
    durations = (20.0,)
    zoom = 100
    track_width = 1000
    navigator_width = 200
    marker_x = timeline_navigator_global_seconds_x(
        durations,
        10.0,
        zoom,
        track_width,
        navigator_width,
    )

    assert (
        timeline_navigator_anchor_hit(
            marker_x + 7,
            durations,
            (10.0,),
            None,
            None,
            zoom,
            track_width,
            navigator_width,
            hit_radius_px=6,
        )
        is None
    )


def test_anchor_hit_clamps_session_time_to_project_bounds() -> None:
    durations = (10.0, 10.0)
    zoom = 100
    track_width = 1200
    navigator_width = 240
    end_x = timeline_navigator_global_seconds_x(
        durations,
        20.0,
        zoom,
        track_width,
        navigator_width,
    )

    assert timeline_navigator_anchor_hit(
        end_x,
        durations,
        (99.0,),
        None,
        None,
        zoom,
        track_width,
        navigator_width,
    ) == ("marker", 20.0)


def test_anchor_timecode_formats_milliseconds_and_long_hours() -> None:
    assert timeline_navigator_anchor_timecode(0.0) == "00:00:00.000"
    assert timeline_navigator_anchor_timecode(65.4321) == "00:01:05.432"
    assert timeline_navigator_anchor_timecode(3661.9996) == "01:01:02.000"
    assert timeline_navigator_anchor_timecode(360000.0) == "100:00:00.000"


def test_anchor_timecode_clamps_negative_values() -> None:
    assert timeline_navigator_anchor_timecode(-2.5) == "00:00:00.000"


def test_anchor_tooltip_uses_expected_labels() -> None:
    assert timeline_navigator_anchor_tooltip(("marker", 5.25)) == (
        "Marker • 00:00:05.250"
    )
    assert timeline_navigator_anchor_tooltip(("in", 65.0)) == "In • 00:01:05.000"
    assert timeline_navigator_anchor_tooltip(("out", 125.5)) == "Out • 00:02:05.500"


def test_anchor_center_scroll_clamps_to_scrollbar_edges() -> None:
    durations = (20.0,)

    assert timeline_navigator_anchor_center_scroll_value(
        durations,
        0.0,
        100,
        300,
        500,
    ) == 0
    assert timeline_navigator_anchor_center_scroll_value(
        durations,
        20.0,
        100,
        300,
        100,
    ) == 100
    assert timeline_navigator_anchor_center_scroll_value(
        (),
        10.0,
        100,
        300,
        100,
    ) == 0
