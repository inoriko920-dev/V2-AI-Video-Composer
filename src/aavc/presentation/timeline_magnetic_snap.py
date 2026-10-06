from __future__ import annotations

from typing import Literal

from aavc.presentation.timeline_magnet_control import (
    timeline_magnet_runtime_active,
    timeline_magnet_runtime_target_enabled,
    timeline_magnet_runtime_tolerance_px,
)
from aavc.presentation.timeline_markers import timeline_marker_snap_seconds
from aavc.presentation.timeline_zoom_scroll import timeline_global_seconds_pixel_x

TimelineMagneticSnapKind = Literal["marker", "scene", "playhead"]
TIMELINE_MAGNETIC_SNAP_RADIUS_PX = 8


def timeline_scene_boundaries_seconds(
    durations_seconds: tuple[float, ...],
) -> tuple[float, ...]:
    """Return project start, every Scene boundary, and project end."""

    boundaries = [0.0]
    elapsed = 0.0
    for raw_duration in durations_seconds:
        elapsed += max(0.0, float(raw_duration))
        boundaries.append(round(elapsed, 6))
    return tuple(boundaries)


def timeline_magnetic_snap_target(
    durations_seconds: tuple[float, ...],
    pixel_x: float,
    zoom_percent: int | float,
    fps: int | float,
    *,
    markers_seconds: tuple[float, ...] = (),
    playhead_seconds: float | None = None,
    tolerance_px: int | None = None,
) -> tuple[float, TimelineMagneticSnapKind] | None:
    """Return the nearest enabled visual magnetic target within the active radius."""

    if not durations_seconds or not timeline_magnet_runtime_active():
        return None

    total_duration = sum(max(0.0, float(item)) for item in durations_seconds)
    normalized_fps = max(1, int(round(float(fps))))
    tolerance = (
        timeline_magnet_runtime_tolerance_px()
        if tolerance_px is None
        else max(0, int(tolerance_px))
    )
    pointer_x = float(pixel_x)

    raw_candidates: list[tuple[float, TimelineMagneticSnapKind, int]] = []
    if timeline_magnet_runtime_target_enabled("scene"):
        raw_candidates.extend(
            (seconds, "scene", 2)
            for seconds in timeline_scene_boundaries_seconds(durations_seconds)
        )
    if timeline_magnet_runtime_target_enabled("marker"):
        raw_candidates.extend((float(seconds), "marker", 1) for seconds in markers_seconds)
    if (
        playhead_seconds is not None
        and timeline_magnet_runtime_target_enabled("playhead")
    ):
        raw_candidates.append((float(playhead_seconds), "playhead", 0))

    normalized: dict[tuple[float, TimelineMagneticSnapKind], int] = {}
    for seconds, kind, priority in raw_candidates:
        snapped = timeline_marker_snap_seconds(
            seconds,
            total_duration,
            normalized_fps,
        )
        key = (snapped, kind)
        existing = normalized.get(key)
        if existing is None or priority < existing:
            normalized[key] = priority

    candidates: list[tuple[float, int, float, TimelineMagneticSnapKind]] = []
    for (seconds, kind), priority in normalized.items():
        target_x = timeline_global_seconds_pixel_x(
            durations_seconds,
            seconds,
            zoom_percent,
        )
        distance = abs(pointer_x - float(target_x))
        if distance <= tolerance:
            candidates.append((distance, priority, seconds, kind))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    _distance, _priority, seconds, kind = candidates[0]
    return seconds, kind
