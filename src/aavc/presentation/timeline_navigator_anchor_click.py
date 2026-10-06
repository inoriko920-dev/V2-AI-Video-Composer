from __future__ import annotations

from contextlib import suppress
from typing import Any, Literal

from aavc.domain.project.models import ProjectState
from aavc.presentation.timeline_markers import timeline_marker_seek_target
from aavc.presentation.timeline_navigator import (
    TIMELINE_NAVIGATOR_EDGE_HIT_PX,
    timeline_navigator_global_seconds_x,
    timeline_navigator_hit_region,
    timeline_navigator_viewport_geometry,
)
from aavc.presentation.timeline_ruler_seek import timeline_slider_value_for_local_seconds
from aavc.presentation.timeline_zoom_scroll import timeline_global_seconds_pixel_x

TIMELINE_NAVIGATOR_ANCHOR_HIT_PX = 6
TimelineNavigatorAnchorKind = Literal["in", "out", "marker"]
TimelineNavigatorAnchor = tuple[TimelineNavigatorAnchorKind, float]


def timeline_navigator_anchor_hit(
    mouse_x: int | float,
    durations_seconds: tuple[float, ...],
    markers_seconds: tuple[float, ...],
    in_seconds: float | None,
    out_seconds: float | None,
    zoom_percent: int | float,
    track_width_px: int | float,
    navigator_width_px: int | float,
    *,
    hit_radius_px: int = TIMELINE_NAVIGATOR_ANCHOR_HIT_PX,
) -> TimelineNavigatorAnchor | None:
    """Return the closest clickable navigator anchor within the hit radius."""

    if not durations_seconds:
        return None

    total = sum(max(0.0, float(item)) for item in durations_seconds)
    radius = max(1.0, float(hit_radius_px))
    pointer = float(mouse_x)
    candidates: list[tuple[float, int, float, TimelineNavigatorAnchorKind]] = []

    def add_candidate(
        kind: TimelineNavigatorAnchorKind,
        seconds: float,
        priority: int,
    ) -> None:
        normalized = max(0.0, min(total, float(seconds)))
        anchor_x = timeline_navigator_global_seconds_x(
            durations_seconds,
            normalized,
            zoom_percent,
            track_width_px,
            navigator_width_px,
        )
        distance = abs(pointer - float(anchor_x))
        if distance <= radius:
            candidates.append((distance, priority, normalized, kind))

    if in_seconds is not None:
        add_candidate("in", in_seconds, 0)
    if out_seconds is not None:
        add_candidate("out", out_seconds, 1)
    for marker in markers_seconds:
        add_candidate("marker", marker, 2)

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    _distance, _priority, seconds, kind = candidates[0]
    return kind, round(seconds, 6)


def timeline_navigator_anchor_timecode(seconds: float) -> str:
    """Format navigator anchor time as HH:MM:SS.mmm."""

    total_ms = max(0, int(round(float(seconds) * 1000.0)))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"


def timeline_navigator_anchor_tooltip(anchor: TimelineNavigatorAnchor) -> str:
    """Return concise hover text for a navigator Marker/In/Out anchor."""

    kind, seconds = anchor
    label = {"in": "In", "out": "Out", "marker": "Marker"}[kind]
    return f"{label} • {timeline_navigator_anchor_timecode(seconds)}"


def timeline_navigator_anchor_center_scroll_value(
    durations_seconds: tuple[float, ...],
    global_seconds: float,
    zoom_percent: int | float,
    viewport_width_px: int | float,
    maximum_scroll: int | float,
) -> int:
    """Return scroll value that centers a clicked anchor in the main viewport."""

    maximum = max(0, int(round(float(maximum_scroll))))
    if not durations_seconds or maximum <= 0:
        return 0
    total = sum(max(0.0, float(item)) for item in durations_seconds)
    seconds = max(0.0, min(total, float(global_seconds)))
    anchor_x = timeline_global_seconds_pixel_x(
        durations_seconds,
        seconds,
        zoom_percent,
    )
    desired = int(round(float(anchor_x) - max(0.0, float(viewport_width_px)) / 2.0))
    return max(0, min(maximum, desired))


def install_timeline_navigator_anchor_click(root: Any, project: ProjectState) -> bool:
    """Make session Marker/In/Out anchors clickable in the mini navigator."""

    from PySide6.QtCore import QEvent, QObject, Qt
    from PySide6.QtWidgets import (
        QListWidget,
        QScrollArea,
        QSlider,
        QSpinBox,
        QToolTip,
        QWidget,
    )

    navigator = root.findChild(QWidget, "TimelineMiniNavigator")
    scroll = root.findChild(QScrollArea, "TimelineSceneScrollArea")
    track_widget = root.findChild(QWidget, "TimelineSceneTrack")
    zoom_box = root.findChild(QSpinBox, "TimelineZoomPercent")
    if (
        navigator is None
        or scroll is None
        or track_widget is None
        or zoom_box is None
        or not project.scenes
    ):
        return False

    scene_list: Any | None = None
    for listing in root.findChildren(QListWidget):
        if listing.count() != len(project.scenes):
            continue
        first = listing.item(0)
        if first is not None and first.text().startswith(
            f"{project.scenes[0].scene_number:02d}. Scene"
        ):
            scene_list = listing
            break

    sliders = root.findChildren(QSlider)
    progress_slider: Any | None = sliders[0] if sliders else None
    if scene_list is None or progress_slider is None:
        return False

    durations = tuple(max(0.0, float(scene.duration_seconds)) for scene in project.scenes)
    bar = scroll.horizontalScrollBar()
    viewport = scroll.viewport()
    owner: Any = navigator.window()

    def session_markers() -> tuple[float, ...]:
        raw = getattr(owner, "_aavc_timeline_markers_seconds", ())
        values: list[float] = []
        for item in raw:
            try:
                values.append(float(item))
            except (TypeError, ValueError):
                continue
        return tuple(sorted(values))

    def session_range() -> tuple[float | None, float | None]:
        raw_in = getattr(owner, "_aavc_timeline_in_seconds", None)
        raw_out = getattr(owner, "_aavc_timeline_out_seconds", None)
        try:
            in_point = None if raw_in is None else float(raw_in)
        except (TypeError, ValueError):
            in_point = None
        try:
            out_point = None if raw_out is None else float(raw_out)
        except (TypeError, ValueError):
            out_point = None
        return in_point, out_point

    def anchor_at(mouse_x: float) -> TimelineNavigatorAnchor | None:
        in_point, out_point = session_range()
        return timeline_navigator_anchor_hit(
            mouse_x,
            durations,
            session_markers(),
            in_point,
            out_point,
            zoom_box.value(),
            track_widget.width(),
            navigator.width(),
        )

    def is_resize_grip(mouse_x: float) -> bool:
        handle_x, handle_width = timeline_navigator_viewport_geometry(
            navigator.width(),
            track_widget.width(),
            viewport.width(),
            bar.value(),
            bar.maximum(),
        )
        region = timeline_navigator_hit_region(
            mouse_x,
            handle_x,
            handle_width,
            edge_hit_px=TIMELINE_NAVIGATOR_EDGE_HIT_PX,
        )
        return region in {"left", "right"}

    def activate_manual_override() -> None:
        callback = getattr(root, "_aavc_timeline_set_manual_follow_override", None)
        if callable(callback):
            callback(True, announce=True)

    def seek_anchor(anchor: TimelineNavigatorAnchor) -> None:
        kind, seconds = anchor
        target = timeline_marker_seek_target(durations, seconds)
        if target is None:
            return
        scene_index, local_seconds = target
        if scene_list.currentRow() != scene_index:
            scene_list.setCurrentRow(scene_index)
        slider_value = timeline_slider_value_for_local_seconds(
            local_seconds,
            durations[scene_index],
            progress_slider.maximum(),
        )
        progress_slider.setValue(slider_value)
        progress_slider.sliderMoved.emit(slider_value)
        progress_slider.sliderReleased.emit()
        bar.setValue(
            timeline_navigator_anchor_center_scroll_value(
                durations,
                seconds,
                zoom_box.value(),
                viewport.width(),
                bar.maximum(),
            )
        )

        status_bar = owner.statusBar() if hasattr(owner, "statusBar") else None
        if status_bar is not None:
            label = {"in": "In point", "out": "Out point", "marker": "Marker"}[kind]
            status_bar.showMessage(
                f"Playhead dipindah ke {label} {seconds:.3f} detik melalui mini navigator.",
                5000,
            )

    class _NavigatorAnchorClickFilter(QObject):
        def __init__(self, parent: Any) -> None:
            super().__init__(parent)
            self._consuming_click = False

        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802
            del watched
            event_type = event.type()

            if event_type == QEvent.Type.MouseMove:
                mouse_x = float(event.position().x())
                if self._consuming_click:
                    QToolTip.hideText()
                    event.accept()
                    return True
                if bool(event.buttons() & Qt.MouseButton.LeftButton):
                    QToolTip.hideText()
                    return False
                if is_resize_grip(mouse_x):
                    QToolTip.hideText()
                    return False
                anchor = anchor_at(mouse_x)
                if anchor is not None:
                    navigator.setCursor(Qt.CursorShape.PointingHandCursor)
                    QToolTip.showText(
                        navigator.mapToGlobal(event.position().toPoint()),
                        timeline_navigator_anchor_tooltip(anchor),
                        navigator,
                    )
                    event.accept()
                    return True
                QToolTip.hideText()
                return False

            if event_type == QEvent.Type.Leave:
                QToolTip.hideText()
                return False

            if event_type == QEvent.Type.MouseButtonPress:
                if event.button() != Qt.MouseButton.LeftButton:
                    return False
                mouse_x = float(event.position().x())
                if is_resize_grip(mouse_x):
                    QToolTip.hideText()
                    return False
                anchor = anchor_at(mouse_x)
                if anchor is None:
                    QToolTip.hideText()
                    return False
                QToolTip.hideText()
                activate_manual_override()
                seek_anchor(anchor)
                self._consuming_click = True
                navigator.setCursor(Qt.CursorShape.PointingHandCursor)
                event.accept()
                return True

            if event_type == QEvent.Type.MouseButtonRelease:
                if not self._consuming_click or event.button() != Qt.MouseButton.LeftButton:
                    return False
                self._consuming_click = False
                event.accept()
                return True

            return False

    previous_filter = getattr(root, "_aavc_timeline_navigator_anchor_click_filter", None)
    previous_target = getattr(root, "_aavc_timeline_navigator_anchor_click_target", None)
    if previous_filter is not None and previous_target is not None:
        with suppress(RuntimeError):
            previous_target.removeEventFilter(previous_filter)

    event_filter = _NavigatorAnchorClickFilter(root)
    navigator.installEventFilter(event_filter)
    root._aavc_timeline_navigator_anchor_click_filter = event_filter
    root._aavc_timeline_navigator_anchor_click_target = navigator
    navigator.setToolTip(
        f"{navigator.toolTip()} Klik Marker/In/Out untuk memindahkan playhead tepat ke anchor tersebut."
    )
    return True
