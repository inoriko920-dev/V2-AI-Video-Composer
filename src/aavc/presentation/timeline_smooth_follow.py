from __future__ import annotations

TIMELINE_FOLLOW_DEAD_ZONE_START = 0.35
TIMELINE_FOLLOW_DEAD_ZONE_END = 0.65
TIMELINE_FOLLOW_TARGET_RATIO = 0.50
TIMELINE_FOLLOW_ANIMATION_MS = 140


def timeline_smooth_follow_scroll_target(
    playhead_x: int | float,
    viewport_width: int,
    current_scroll: int,
    maximum_scroll: int,
) -> int | None:
    """Return a centered scroll target only when playhead leaves the comfort zone."""

    width = max(1, int(viewport_width))
    maximum = max(0, int(maximum_scroll))
    current = max(0, min(maximum, int(current_scroll)))
    playhead = float(playhead_x)
    relative_x = playhead - current
    dead_start = width * TIMELINE_FOLLOW_DEAD_ZONE_START
    dead_end = width * TIMELINE_FOLLOW_DEAD_ZONE_END
    if dead_start <= relative_x <= dead_end:
        return None

    desired = int(round(playhead - width * TIMELINE_FOLLOW_TARGET_RATIO))
    target = max(0, min(maximum, desired))
    if target == current:
        return None
    return target
