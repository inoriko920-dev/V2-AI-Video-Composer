from aavc.presentation.timeline_zoom_scroll import (
    MAX_TIMELINE_ZOOM_PERCENT,
    MIN_TIMELINE_SCENE_WIDTH_PX,
    MIN_TIMELINE_ZOOM_PERCENT,
    normalize_timeline_zoom_percent,
    timeline_global_seconds_pixel_x,
    timeline_playhead_pixel_x,
    timeline_ruler_major_interval_seconds,
    timeline_ruler_time_label,
    timeline_scene_pixel_width,
    timeline_track_pixel_width,
)


def test_timeline_zoom_percent_clamps_to_supported_range() -> None:
    assert normalize_timeline_zoom_percent(10) == MIN_TIMELINE_ZOOM_PERCENT
    assert normalize_timeline_zoom_percent(100) == 100
    assert normalize_timeline_zoom_percent(999) == MAX_TIMELINE_ZOOM_PERCENT


def test_timeline_scene_width_scales_with_zoom_and_duration() -> None:
    assert timeline_scene_pixel_width(4.0, 200) == 2 * timeline_scene_pixel_width(4.0, 100)
    assert timeline_scene_pixel_width(8.0, 100) == 2 * timeline_scene_pixel_width(4.0, 100)
    assert timeline_scene_pixel_width(0.001, 100) == MIN_TIMELINE_SCENE_WIDTH_PX


def test_timeline_track_width_adds_scene_widths_and_spacing() -> None:
    first = timeline_scene_pixel_width(2.0, 100)
    second = timeline_scene_pixel_width(3.0, 100)

    assert timeline_track_pixel_width((2.0, 3.0), 100) == first + second + 3
    assert timeline_track_pixel_width((), 100) == 0


def test_timeline_ruler_major_interval_adapts_to_zoom() -> None:
    assert timeline_ruler_major_interval_seconds(50) == 5.0
    assert timeline_ruler_major_interval_seconds(100) == 2.0
    assert timeline_ruler_major_interval_seconds(200) == 1.0
    assert timeline_ruler_major_interval_seconds(400) == 0.5


def test_timeline_ruler_interval_limits_tick_count_for_long_projects() -> None:
    assert timeline_ruler_major_interval_seconds(400, 7200.0) == 5.0


def test_timeline_global_time_mapping_respects_minimum_scene_width() -> None:
    durations = (0.1, 2.0)

    assert timeline_global_seconds_pixel_x(durations, 0.0, 100) == 0
    assert timeline_global_seconds_pixel_x(durations, 0.05, 100) == 28
    assert timeline_global_seconds_pixel_x(durations, 0.1, 100) == 59
    assert timeline_global_seconds_pixel_x(durations, 1.1, 100) == 107
    assert timeline_global_seconds_pixel_x(durations, 2.1, 100) == 155


def test_timeline_playhead_mapping_uses_selected_scene_visual_block() -> None:
    durations = (0.1, 2.0)

    assert timeline_playhead_pixel_x(durations, 1, 0.0, 100) == 59
    assert timeline_playhead_pixel_x(durations, 1, 1.0, 100) == 107
    assert timeline_playhead_pixel_x(durations, 1, 2.0, 100) == 155


def test_timeline_ruler_time_label_supports_subseconds_and_hours() -> None:
    assert timeline_ruler_time_label(0.0) == "0:00"
    assert timeline_ruler_time_label(0.5) == "0:00.5"
    assert timeline_ruler_time_label(65.0) == "1:05"
    assert timeline_ruler_time_label(3605.0) == "1:00:05"
