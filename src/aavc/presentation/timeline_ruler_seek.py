from __future__ import annotations

from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.timeline_zoom_scroll import (
    DEFAULT_TIMELINE_ZOOM_PERCENT,
    TIMELINE_TRACK_SPACING_PX,
    normalize_timeline_zoom_percent,
    timeline_scene_pixel_width,
)


def timeline_ruler_seek_target(
    durations_seconds: tuple[float, ...],
    pixel_x: float,
    zoom_percent: int | float,
) -> tuple[int, float] | None:
    """Map a ruler pixel position to Scene index plus local Scene seconds."""

    if not durations_seconds:
        return None

    target_x = max(0.0, float(pixel_x))
    cursor_x = 0.0
    last_index = len(durations_seconds) - 1
    for index, raw_duration in enumerate(durations_seconds):
        duration = max(0.0, float(raw_duration))
        width = float(timeline_scene_pixel_width(duration, zoom_percent))
        scene_end_x = cursor_x + width
        if target_x <= scene_end_x or index == last_index:
            local_x = max(0.0, min(width, target_x - cursor_x))
            fraction = 0.0 if width <= 0 else local_x / width
            return index, duration * fraction

        gap_end_x = scene_end_x + TIMELINE_TRACK_SPACING_PX
        if target_x < gap_end_x:
            gap_offset = target_x - scene_end_x
            if gap_offset <= TIMELINE_TRACK_SPACING_PX / 2.0:
                return index, duration
            next_index = min(last_index, index + 1)
            return next_index, 0.0
        cursor_x = gap_end_x

    return last_index, max(0.0, float(durations_seconds[last_index]))


def timeline_slider_value_for_local_seconds(
    local_seconds: float,
    duration_seconds: float,
    maximum: int,
) -> int:
    """Map Scene-local seconds to the preview scrub slider range."""

    upper = max(0, int(maximum))
    duration = max(0.0, float(duration_seconds))
    if upper <= 0 or duration <= 0:
        return 0
    local = max(0.0, min(duration, float(local_seconds)))
    return int(round(local / duration * upper))


def _stored_zoom_percent(owner: Any) -> int:
    value = owner.property("aavcTimelineZoomPercent")
    try:
        raw = DEFAULT_TIMELINE_ZOOM_PERCENT if value is None else int(value)
    except (TypeError, ValueError):
        raw = DEFAULT_TIMELINE_ZOOM_PERCENT
    return normalize_timeline_zoom_percent(raw)


def install_timeline_ruler_seek(root: Any, project: ProjectState) -> bool:
    """Enable click-and-drag global seeking on the installed timeline ruler."""

    from PySide6.QtCore import QEvent, QObject, Qt
    from PySide6.QtWidgets import QListWidget, QSlider, QWidget

    ruler = root.findChild(QWidget, "TimelineTimeRuler")
    if ruler is None:
        return False

    scene_list: Any | None = None
    for listing in root.findChildren(QListWidget):
        if listing.count() != len(project.scenes) or not project.scenes:
            continue
        first = listing.item(0)
        if first is not None and first.text().startswith(
            f"{project.scenes[0].scene_number:02d}. Scene"
        ):
            scene_list = listing
            break

    sliders = root.findChildren(QSlider)
    progress_slider: Any | None = sliders[0] if sliders else None
    if scene_list is None or progress_slider is None or not project.scenes:
        return False

    durations = tuple(scene.duration_seconds for scene in project.scenes)
    owner = ruler.window()
    ruler.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
    ruler.setMouseTracking(True)
    ruler.setCursor(Qt.CursorShape.SplitHCursor)
    ruler.setToolTip(
        "Klik untuk seek ke waktu global project. Tahan dan drag horizontal untuk scrub lintas Scene."
    )

    def seek_at_x(position_x: float, *, release: bool) -> None:
        target = timeline_ruler_seek_target(
            durations,
            position_x,
            _stored_zoom_percent(owner),
        )
        if target is None:
            return
        scene_index, local_seconds = target
        if scene_list.currentRow() != scene_index:
            scene_list.setCurrentRow(scene_index)

        duration = max(0.0, float(durations[scene_index]))
        slider_value = timeline_slider_value_for_local_seconds(
            local_seconds,
            duration,
            progress_slider.maximum(),
        )
        progress_slider.setValue(slider_value)
        progress_slider.sliderMoved.emit(slider_value)
        if release:
            progress_slider.sliderReleased.emit()

    class _RulerSeekFilter(QObject):
        def __init__(self, parent: Any) -> None:
            super().__init__(parent)
            self._dragging = False

        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802
            if watched is not ruler:
                return False

            if (
                event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._dragging = True
                seek_at_x(float(event.position().x()), release=False)
                return True

            if (
                event.type() == QEvent.Type.MouseMove
                and self._dragging
                and bool(event.buttons() & Qt.MouseButton.LeftButton)
            ):
                seek_at_x(float(event.position().x()), release=False)
                return True

            if (
                event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton
                and self._dragging
            ):
                self._dragging = False
                seek_at_x(float(event.position().x()), release=True)
                return True

            return False

    event_filter = _RulerSeekFilter(root)
    ruler.installEventFilter(event_filter)
    root._aavc_timeline_ruler_seek_filter = event_filter
    return True
