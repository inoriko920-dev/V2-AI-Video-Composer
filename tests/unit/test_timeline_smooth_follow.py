from __future__ import annotations

from aavc.presentation.timeline_smooth_follow import (
    timeline_smooth_follow_scroll_target,
)


def test_playhead_inside_dead_zone_does_not_scroll() -> None:
    assert timeline_smooth_follow_scroll_target(500, 1000, 0, 3000) is None
    assert timeline_smooth_follow_scroll_target(500, 1000, 100, 3000) is None
    assert timeline_smooth_follow_scroll_target(350, 1000, 0, 3000) is None
    assert timeline_smooth_follow_scroll_target(650, 1000, 0, 3000) is None


def test_playhead_right_of_dead_zone_recenters_viewport() -> None:
    assert timeline_smooth_follow_scroll_target(900, 1000, 0, 3000) == 400


def test_playhead_left_of_dead_zone_recenters_viewport() -> None:
    assert timeline_smooth_follow_scroll_target(900, 1000, 700, 3000) == 400


def test_target_clamps_to_scroll_edges() -> None:
    assert timeline_smooth_follow_scroll_target(100, 1000, 600, 3000) == 0
    assert timeline_smooth_follow_scroll_target(3900, 1000, 2500, 3000) == 3000


def test_noop_when_clamped_target_matches_current_scroll() -> None:
    assert timeline_smooth_follow_scroll_target(100, 1000, 0, 3000) is None
    assert timeline_smooth_follow_scroll_target(3900, 1000, 3000, 3000) is None


def test_non_positive_viewport_width_is_safe() -> None:
    assert timeline_smooth_follow_scroll_target(20, 0, 0, 100) == 20
