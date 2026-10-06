from __future__ import annotations

from aavc.presentation.timeline_magnet_control import (
    timeline_magnet_runtime_active,
    timeline_magnet_runtime_target_enabled,
    timeline_magnet_runtime_tolerance_px,
)
from aavc.presentation.timeline_magnetic_snap import timeline_magnetic_snap_target
from aavc.presentation.timeline_markers import timeline_marker_snap_seconds
from aavc.presentation.timeline_zoom_scroll import timeline_global_seconds_pixel_x


def timeline_scene_start_seconds(
    durations_seconds: tuple[float, ...],
    scene_index: int,
) -> float:
    if not durations_seconds:
        return 0.0
    index = max(0, min(len(durations_seconds) - 1, int(scene_index)))
    return round(sum(max(0.0, float(item)) for item in durations_seconds[:index]), 6)


def timeline_magnetic_resize_duration(
    durations_seconds: tuple[float, ...],
    scene_index: int,
    proposed_duration_seconds: float,
    pointer_pixel_x: float,
    zoom_percent: int | float,
    fps: int | float,
    *,
    markers_seconds: tuple[float, ...] = (),
    playhead_seconds: float | None = None,
    minimum_seconds: float = 0.001,
) -> tuple[float, str | None]:
    """Snap the persisted Scene end boundary to the nearest enabled magnetic target."""

    if not durations_seconds:
        return max(float(minimum_seconds), round(float(proposed_duration_seconds), 3)), None

    start_seconds = timeline_scene_start_seconds(durations_seconds, scene_index)
    snap = timeline_magnetic_snap_target(
        durations_seconds,
        pointer_pixel_x,
        zoom_percent,
        fps,
        markers_seconds=markers_seconds,
        playhead_seconds=playhead_seconds,
    )
    if snap is None:
        return max(float(minimum_seconds), round(float(proposed_duration_seconds), 3)), None

    target_seconds, kind = snap
    duration = float(target_seconds) - start_seconds
    if duration < float(minimum_seconds):
        return max(float(minimum_seconds), round(float(proposed_duration_seconds), 3)), None
    return round(duration, 3), kind


def timeline_magnetic_split_local_seconds(
    durations_seconds: tuple[float, ...],
    scene_index: int,
    local_seconds: float,
    zoom_percent: int | float,
    fps: int | float,
    *,
    markers_seconds: tuple[float, ...] = (),
    tolerance_px: int | None = None,
) -> tuple[float, bool]:
    """Snap a Split point to nearby marker/In-Out anchors inside the selected Scene."""

    if not durations_seconds:
        return round(max(0.0, float(local_seconds)), 3), False

    index = max(0, min(len(durations_seconds) - 1, int(scene_index)))
    duration = max(0.0, float(durations_seconds[index]))
    if (
        not timeline_magnet_runtime_active()
        or not timeline_magnet_runtime_target_enabled("marker")
    ):
        return round(max(0.0, min(duration, float(local_seconds))), 3), False

    start_seconds = timeline_scene_start_seconds(durations_seconds, index)
    total_duration = sum(max(0.0, float(item)) for item in durations_seconds)
    global_seconds = max(0.0, min(total_duration, start_seconds + float(local_seconds)))
    pixel_x = timeline_global_seconds_pixel_x(
        durations_seconds,
        global_seconds,
        zoom_percent,
    )
    tolerance = (
        timeline_magnet_runtime_tolerance_px()
        if tolerance_px is None
        else max(0, int(tolerance_px))
    )

    candidates: list[tuple[float, float]] = []
    for raw_marker in markers_seconds:
        snapped = timeline_marker_snap_seconds(raw_marker, total_duration, fps)
        if snapped <= start_seconds or snapped >= start_seconds + duration:
            continue
        marker_x = timeline_global_seconds_pixel_x(
            durations_seconds,
            snapped,
            zoom_percent,
        )
        distance = abs(float(pixel_x) - float(marker_x))
        if distance <= tolerance:
            candidates.append((distance, snapped))

    if not candidates:
        return round(max(0.0, min(duration, float(local_seconds))), 3), False

    candidates.sort(key=lambda item: (item[0], item[1]))
    snapped_global = candidates[0][1]
    return round(snapped_global - start_seconds, 3), True
