from __future__ import annotations

from contextlib import suppress
from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.timeline_follow_override import (
    install_timeline_manual_follow_override,
)
from aavc.presentation.timeline_navigator import install_timeline_navigator
from aavc.presentation.timeline_navigator_anchor_click import (
    install_timeline_navigator_anchor_click,
)
from aavc.presentation.timeline_zoom_actions import install_timeline_zoom_actions
from aavc.presentation.timeline_zoom_scroll import (
    TIMELINE_TRACK_SPACING_PX,
    normalize_timeline_zoom_percent,
    timeline_global_seconds_pixel_x,
    timeline_scene_pixel_width,
)

TIMELINE_CURSOR_ZOOM_STEP_PERCENT = 25


def timeline_global_seconds_for_pixel_x(
    durations_seconds: tuple[float, ...],
    pixel_x: float,
    zoom_percent: int | float,
) -> float:
    """Map one visual track pixel to global project seconds."""

    if not durations_seconds:
        return 0.0

    target_x = max(0.0, float(pixel_x))
    cursor_x = 0.0
    elapsed = 0.0
    last_index = len(durations_seconds) - 1
    for index, raw_duration in enumerate(durations_seconds):
        duration = max(0.0, float(raw_duration))
        width = float(timeline_scene_pixel_width(duration, zoom_percent))
        scene_end_x = cursor_x + width
        if target_x <= scene_end_x or index == last_index:
            local_x = max(0.0, min(width, target_x - cursor_x))
            fraction = 0.0 if width <= 0.0 else local_x / width
            return round(elapsed + duration * fraction, 6)

        elapsed += duration
        gap_end_x = scene_end_x + TIMELINE_TRACK_SPACING_PX
        if target_x < gap_end_x:
            return round(elapsed, 6)
        cursor_x = gap_end_x

    return round(elapsed, 6)


def timeline_cursor_zoom_percent(
    current_zoom_percent: int | float,
    wheel_delta_y: int | float,
) -> int:
    """Return the next 25% zoom step from a Ctrl+Wheel delta."""

    current = normalize_timeline_zoom_percent(current_zoom_percent)
    delta = float(wheel_delta_y)
    if delta == 0.0:
        return current
    step = TIMELINE_CURSOR_ZOOM_STEP_PERCENT if delta > 0.0 else -TIMELINE_CURSOR_ZOOM_STEP_PERCENT
    return normalize_timeline_zoom_percent(current + step)


def timeline_cursor_anchor_scroll_value(
    durations_seconds: tuple[float, ...],
    anchor_seconds: float,
    cursor_viewport_x: float,
    zoom_percent: int | float,
    maximum_scroll: int,
) -> int:
    """Return horizontal scroll that keeps the anchor below the same cursor x."""

    anchor_x = timeline_global_seconds_pixel_x(
        durations_seconds,
        anchor_seconds,
        zoom_percent,
    )
    desired = int(round(float(anchor_x) - float(cursor_viewport_x)))
    return max(0, min(max(0, int(maximum_scroll)), desired))


def install_timeline_cursor_zoom(root: Any, project: ProjectState) -> bool:
    """Install Ctrl+Wheel timeline zoom anchored to the mouse cursor."""

    from PySide6.QtCore import QEvent, QObject, Qt, QTimer
    from PySide6.QtWidgets import QScrollArea, QSpinBox, QWidget

    scroll = root.findChild(QScrollArea, "TimelineSceneScrollArea")
    zoom_box = root.findChild(QSpinBox, "TimelineZoomPercent")
    track_widget = root.findChild(QWidget, "TimelineSceneTrack")
    if scroll is None or zoom_box is None or track_widget is None or not project.scenes:
        return False

    durations = tuple(scene.duration_seconds for scene in project.scenes)
    bar = scroll.horizontalScrollBar()
    viewport = scroll.viewport()

    class _TimelineCursorZoomFilter(QObject):
        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802
            del watched
            if event.type() != QEvent.Type.Wheel:
                return False
            if not bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                return False

            delta_y = int(event.angleDelta().y())
            if delta_y == 0:
                delta_y = int(event.pixelDelta().y())
            if delta_y == 0:
                return False

            current_zoom = int(zoom_box.value())
            next_zoom = timeline_cursor_zoom_percent(current_zoom, delta_y)
            if next_zoom == current_zoom:
                event.accept()
                return True

            cursor_point = viewport.mapFromGlobal(event.globalPosition().toPoint())
            cursor_x = max(0.0, min(float(viewport.width()), float(cursor_point.x())))
            track_x = float(bar.value()) + cursor_x
            anchor_seconds = timeline_global_seconds_for_pixel_x(
                durations,
                track_x,
                current_zoom,
            )

            zoom_box.setValue(next_zoom)

            def restore_anchor() -> None:
                bar.setValue(
                    timeline_cursor_anchor_scroll_value(
                        durations,
                        anchor_seconds,
                        cursor_x,
                        next_zoom,
                        bar.maximum(),
                    )
                )

            QTimer.singleShot(0, restore_anchor)
            event.accept()
            return True

    previous_filter = getattr(root, "_aavc_timeline_cursor_zoom_filter", None)
    previous_targets = getattr(root, "_aavc_timeline_cursor_zoom_targets", ())
    if previous_filter is not None:
        for target in previous_targets:
            with suppress(RuntimeError):
                target.removeEventFilter(previous_filter)

    event_filter = _TimelineCursorZoomFilter(root)
    raw_targets = [scroll, viewport, track_widget, *track_widget.findChildren(QWidget)]
    targets: list[Any] = []
    seen: set[int] = set()
    for target in raw_targets:
        target_id = id(target)
        if target_id in seen:
            continue
        seen.add(target_id)
        target.installEventFilter(event_filter)
        targets.append(target)

    root._aavc_timeline_cursor_zoom_filter = event_filter
    root._aavc_timeline_cursor_zoom_targets = tuple(targets)
    scroll.setToolTip(
        f"{scroll.toolTip()} Ctrl+mouse wheel = zoom timeline pada posisi kursor."
    )
    install_timeline_zoom_actions(root, project)
    install_timeline_manual_follow_override(root)
    install_timeline_navigator(root, project)
    install_timeline_navigator_anchor_click(root, project)
    return True
