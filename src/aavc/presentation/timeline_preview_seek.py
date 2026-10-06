from __future__ import annotations

from collections.abc import Callable
from math import floor
from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.motion_preview import preview_scrub_seconds
from aavc.presentation.timeline_magnetic_edit import (
    timeline_magnetic_resize_duration,
    timeline_magnetic_split_local_seconds,
)
from aavc.presentation.timeline_markers import timeline_marker_global_seconds
from aavc.presentation.timeline_ruler_seek import timeline_slider_value_for_local_seconds
from aavc.presentation.timeline_zoom_scroll import (
    DEFAULT_TIMELINE_ZOOM_PERCENT,
    normalize_timeline_zoom_percent,
)

TIMELINE_RESIZE_EDGE_PX = 10.0
MIN_TIMELINE_SCENE_DURATION_SECONDS = 0.001
TIMELINE_RESIZE_SNAP_SECONDS = 0.1


def timeline_seek_slider_value(
    position_x: float,
    width: float,
    maximum: int,
) -> int:
    """Map a horizontal click inside a timeline Scene block to preview slider value."""

    span = float(width)
    upper = int(maximum)
    if span <= 0 or upper <= 0:
        return 0
    fraction = max(0.0, min(1.0, float(position_x) / span))
    return int(round(fraction * upper))


def timeline_drag_target_index(
    pointer_x: float,
    button_center_xs: tuple[float, ...],
) -> int:
    """Return the nearest Scene index for a horizontal drag pointer position."""

    if not button_center_xs:
        return -1
    return min(
        range(len(button_center_xs)),
        key=lambda index: abs(float(pointer_x) - float(button_center_xs[index])),
    )


def timeline_left_resize_handle_hit(
    position_x: float,
    width: float,
    edge_px: float = TIMELINE_RESIZE_EDGE_PX,
) -> bool:
    """Return whether a pointer is inside the left-edge resize handle zone."""

    span = float(width)
    if span <= 0:
        return False
    edge = max(1.0, min(float(edge_px), span / 2.0))
    x = float(position_x)
    return 0.0 <= x <= edge


def timeline_resize_handle_hit(
    position_x: float,
    width: float,
    edge_px: float = TIMELINE_RESIZE_EDGE_PX,
) -> bool:
    """Return whether a pointer is inside the right-edge resize handle zone."""

    span = float(width)
    if span <= 0:
        return False
    edge = max(1.0, min(float(edge_px), span / 2.0))
    x = float(position_x)
    return span - edge <= x <= span


def timeline_resize_edge(
    position_x: float,
    width: float,
    edge_px: float = TIMELINE_RESIZE_EDGE_PX,
) -> str | None:
    """Return the active timeline resize edge, resolving overlap by nearest side."""

    left = timeline_left_resize_handle_hit(position_x, width, edge_px)
    right = timeline_resize_handle_hit(position_x, width, edge_px)
    if left and right:
        return "left" if float(position_x) <= float(width) / 2.0 else "right"
    if left:
        return "left"
    if right:
        return "right"
    return None


def timeline_snap_duration(
    duration_seconds: float,
    *,
    snap_seconds: float = TIMELINE_RESIZE_SNAP_SECONDS,
    minimum_seconds: float = MIN_TIMELINE_SCENE_DURATION_SECONDS,
) -> float:
    """Snap timeline resize duration to a positive fixed grid."""

    value = float(duration_seconds)
    minimum = max(MIN_TIMELINE_SCENE_DURATION_SECONDS, float(minimum_seconds))
    step = float(snap_seconds)
    if step <= 0:
        return max(minimum, round(value, 3))
    snapped = floor(max(0.0, value) / step + 0.5 + 1e-12) * step
    return max(minimum, round(snapped, 3))


def timeline_left_resized_duration(
    current_duration_seconds: float,
    original_width: float,
    delta_x: float,
    *,
    minimum_seconds: float = MIN_TIMELINE_SCENE_DURATION_SECONDS,
) -> float:
    """Scale Scene duration from a left-edge horizontal resize delta."""

    duration = float(current_duration_seconds)
    width = float(original_width)
    minimum = max(MIN_TIMELINE_SCENE_DURATION_SECONDS, float(minimum_seconds))
    if duration <= 0:
        raise ValueError("Durasi Scene harus lebih dari 0")
    if width <= 0:
        return max(minimum, round(duration, 3))

    resized_width = max(width * minimum / duration, width - float(delta_x))
    resized_duration = duration * resized_width / width
    return max(minimum, round(resized_duration, 3))


def timeline_resized_duration(
    current_duration_seconds: float,
    original_width: float,
    delta_x: float,
    *,
    minimum_seconds: float = MIN_TIMELINE_SCENE_DURATION_SECONDS,
) -> float:
    """Scale Scene duration from a right-edge horizontal resize delta."""

    duration = float(current_duration_seconds)
    width = float(original_width)
    minimum = max(MIN_TIMELINE_SCENE_DURATION_SECONDS, float(minimum_seconds))
    if duration <= 0:
        raise ValueError("Durasi Scene harus lebih dari 0")
    if width <= 0:
        return max(minimum, round(duration, 3))

    resized_width = max(width * minimum / duration, width + float(delta_x))
    resized_duration = duration * resized_width / width
    return max(minimum, round(resized_duration, 3))


def _find_scene_list(root: Any, project: ProjectState) -> Any | None:
    from PySide6.QtWidgets import QListWidget

    for listing in root.findChildren(QListWidget):
        if listing.count() != len(project.scenes) or not project.scenes:
            continue
        first = listing.item(0)
        if first is not None and first.text().startswith(
            f"{project.scenes[0].scene_number:02d}. Scene"
        ):
            return listing
    return None


def install_timeline_preview_seek(
    root: Any,
    project: ProjectState,
    *,
    on_scene_reordered: Callable[[int, int], None] | None = None,
    on_scene_resized: Callable[[int, float], None] | None = None,
) -> bool:
    """Seek on click, reorder by body drag, and resize duration from either edge."""

    from PySide6.QtCore import QEvent, QObject, Qt
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSlider, QWidget

    scene_list = _find_scene_list(root, project)
    sliders = root.findChildren(QSlider)
    progress_slider = sliders[0] if sliders else None
    app: Any = QApplication.instance()
    if scene_list is None or progress_slider is None or not project.scenes:
        return False

    active_scene_list: Any = scene_list
    active_slider: Any = progress_slider
    durations = tuple(scene.duration_seconds for scene in project.scenes)
    ruler = root.findChild(QWidget, "TimelineTimeRuler")
    owner: Any = root.window()

    def stored_zoom_percent() -> int:
        value = owner.property("aavcTimelineZoomPercent")
        try:
            raw = DEFAULT_TIMELINE_ZOOM_PERCENT if value is None else int(value)
        except (TypeError, ValueError):
            raw = DEFAULT_TIMELINE_ZOOM_PERCENT
        return normalize_timeline_zoom_percent(raw)

    def marker_seconds() -> tuple[float, ...]:
        raw = getattr(owner, "_aavc_timeline_markers_seconds", ())
        try:
            return tuple(float(item) for item in raw)
        except (TypeError, ValueError):
            return ()

    def split_target_seconds() -> tuple[float, ...]:
        values = list(marker_seconds())
        for attribute in ("_aavc_timeline_in_seconds", "_aavc_timeline_out_seconds"):
            raw = getattr(owner, attribute, None)
            if raw is None:
                continue
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                continue
        return tuple(values)

    def current_playhead_global_seconds() -> float:
        row = int(active_scene_list.currentRow())
        if row < 0 or row >= len(durations):
            return 0.0
        local = preview_scrub_seconds(
            active_slider.value(),
            active_slider.maximum(),
            durations[row],
        )
        return timeline_marker_global_seconds(durations, row, local)

    button_indexes: dict[int, int] = {}
    timeline_buttons: list[Any] = []
    buttons = root.findChildren(QPushButton)
    for index, scene in enumerate(project.scenes):
        prefix = f"Sc{scene.scene_number:02d}\n"
        button = next(
            (candidate for candidate in buttons if candidate.text().startswith(prefix)),
            None,
        )
        if button is None:
            continue
        button_indexes[id(button)] = index
        timeline_buttons.append(button)
        button.setMouseTracking(True)
        if on_scene_reordered is not None and on_scene_resized is not None:
            button.setToolTip(
                f"Scene {scene.scene_number:02d}. Klik posisi untuk seek preview; "
                "drag badan blok untuk reorder; drag tepi kiri/kanan untuk mengubah durasi "
                "dengan snap 0,1 detik atau magnetic snap saat dekat marker/batas/playhead."
            )
        elif on_scene_reordered is not None:
            button.setToolTip(
                f"Scene {scene.scene_number:02d}. Klik posisi untuk seek preview; "
                "drag horizontal untuk mengubah urutan Scene."
            )
        else:
            button.setToolTip(
                f"Scene {scene.scene_number:02d}. Klik posisi pada blok untuk seek preview. "
                "Timeline tetap read-only untuk editing."
            )

    if not timeline_buttons:
        return False

    for label in root.findChildren(QLabel):
        if label.text() == "Timeline Scene · Read-only":
            if on_scene_reordered is not None and on_scene_resized is not None:
                label.setText("Timeline Scene · Drag untuk edit")
            elif on_scene_reordered is not None:
                label.setText("Timeline Scene · Drag untuk reorder")
        elif label.text().startswith("Lebar blok mengikuti durasi scene."):
            if on_scene_reordered is not None and on_scene_resized is not None:
                label.setText(
                    "Lebar blok mengikuti durasi scene. Klik untuk seek; drag badan blok untuk "
                    "reorder; drag tepi kiri/kanan untuk durasi (snap 0,1 detik + magnetic). "
                    "Split Ctrl+B magnetic ke marker/In/Out terdekat."
                )
            elif on_scene_reordered is not None:
                label.setText(
                    "Lebar blok mengikuti durasi scene. Klik untuk seek; drag untuk reorder. "
                    "Split dan resize belum aktif."
                )

    class _TimelineSeekFilter(QObject):
        def __init__(self, parent: Any) -> None:
            super().__init__(parent)
            self._pressed_button_id: int | None = None
            self._press_global_x = 0.0
            self._press_width = 0.0
            self._resize_edge: str | None = None
            self._resizing = False
            self._dragging = False

        def _reset_drag(self, watched: Any) -> None:
            self._pressed_button_id = None
            self._press_global_x = 0.0
            self._press_width = 0.0
            self._resize_edge = None
            self._resizing = False
            self._dragging = False
            watched.unsetCursor()
            if hasattr(watched, "setDown"):
                watched.setDown(False)

        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802
            scene_index = button_indexes.get(id(watched))
            if scene_index is None:
                return False

            if event.type() == QEvent.Type.MouseMove and not bool(
                event.buttons() & Qt.MouseButton.LeftButton
            ):
                if on_scene_resized is not None and timeline_resize_edge(
                    event.position().x(), watched.width()
                ) is not None:
                    watched.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    watched.unsetCursor()
                return False

            if (
                event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._pressed_button_id = id(watched)
                self._press_global_x = float(event.globalPosition().x())
                self._press_width = float(watched.width())
                self._resize_edge = (
                    timeline_resize_edge(event.position().x(), watched.width())
                    if on_scene_resized is not None
                    else None
                )
                self._resizing = False
                self._dragging = False
                return False

            if (
                event.type() == QEvent.Type.MouseMove
                and self._pressed_button_id == id(watched)
                and bool(event.buttons() & Qt.MouseButton.LeftButton)
            ):
                distance = abs(float(event.globalPosition().x()) - self._press_global_x)
                if self._resize_edge is not None and on_scene_resized is not None:
                    if distance >= QApplication.startDragDistance():
                        self._resizing = True
                        watched.setCursor(Qt.CursorShape.SizeHorCursor)
                        return True
                    return False
                if on_scene_reordered is not None and distance >= QApplication.startDragDistance():
                    self._dragging = True
                    watched.setCursor(Qt.CursorShape.ClosedHandCursor)
                    return True
                return False

            if (
                event.type() != QEvent.Type.MouseButtonRelease
                or event.button() != Qt.MouseButton.LeftButton
            ):
                return False

            if self._pressed_button_id != id(watched):
                self._reset_drag(watched)
                return False

            source_scene = project.scenes[scene_index]
            if self._resizing and on_scene_resized is not None:
                delta_x = float(event.globalPosition().x()) - self._press_global_x
                if self._resize_edge == "left":
                    raw_duration = timeline_left_resized_duration(
                        source_scene.duration_seconds,
                        self._press_width,
                        delta_x,
                    )
                else:
                    raw_duration = timeline_resized_duration(
                        source_scene.duration_seconds,
                        self._press_width,
                        delta_x,
                    )
                duration_seconds = timeline_snap_duration(raw_duration)
                if ruler is not None:
                    pointer_x = float(
                        ruler.mapFromGlobal(event.globalPosition().toPoint()).x()
                    )
                    duration_seconds, _snap_kind = timeline_magnetic_resize_duration(
                        durations,
                        scene_index,
                        duration_seconds,
                        pointer_x,
                        stored_zoom_percent(),
                        project.fps,
                        markers_seconds=marker_seconds(),
                        playhead_seconds=current_playhead_global_seconds(),
                        minimum_seconds=MIN_TIMELINE_SCENE_DURATION_SECONDS,
                    )
                self._reset_drag(watched)
                if abs(duration_seconds - source_scene.duration_seconds) >= 0.0005:
                    on_scene_resized(source_scene.scene_number, duration_seconds)
                return True

            if self._dragging and on_scene_reordered is not None:
                pointer_x = float(event.globalPosition().x())
                centers = tuple(
                    float(button.mapToGlobal(button.rect().center()).x())
                    for button in timeline_buttons
                )
                target_index = timeline_drag_target_index(pointer_x, centers)
                source_scene_number = source_scene.scene_number
                self._reset_drag(watched)
                if target_index >= 0 and target_index != scene_index:
                    on_scene_reordered(source_scene_number, target_index)
                return True

            self._reset_drag(watched)
            active_scene_list.setCurrentRow(scene_index)
            value = timeline_seek_slider_value(
                event.position().x(),
                watched.width(),
                active_slider.maximum(),
            )
            active_slider.setValue(value)
            active_slider.sliderMoved.emit(value)
            return False

    class _TimelineSplitSnapFilter(QObject):
        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802
            del watched
            if event.type() != QEvent.Type.KeyPress or not root.isVisible():
                return False
            if event.key() != Qt.Key.Key_B:
                return False
            if event.modifiers() != Qt.KeyboardModifier.ControlModifier:
                return False
            if event.isAutoRepeat():
                return False

            focus = app.focusWidget() if app is not None else None
            if focus is not None and focus is not root and not root.isAncestorOf(focus):
                return False

            row = int(active_scene_list.currentRow())
            if row < 0 or row >= len(durations):
                return False
            local_seconds = preview_scrub_seconds(
                active_slider.value(),
                active_slider.maximum(),
                durations[row],
            )
            snapped_local, snapped = timeline_magnetic_split_local_seconds(
                durations,
                row,
                local_seconds,
                stored_zoom_percent(),
                project.fps,
                markers_seconds=split_target_seconds(),
            )
            if not snapped or abs(snapped_local - local_seconds) < 0.0005:
                return False

            slider_value = timeline_slider_value_for_local_seconds(
                snapped_local,
                durations[row],
                active_slider.maximum(),
            )
            active_slider.setValue(slider_value)
            active_slider.sliderMoved.emit(slider_value)
            active_slider.sliderReleased.emit()
            owner.statusBar().showMessage(
                f"Split magnetic snap ke titik timeline {snapped_local:.3f} detik dalam Scene.",
                4000,
            )
            return False

    event_filter = _TimelineSeekFilter(root)
    for button in timeline_buttons:
        button.installEventFilter(event_filter)
    root._aavc_timeline_seek_filter = event_filter

    if app is not None:
        previous_split_filter = getattr(root, "_aavc_timeline_split_snap_filter", None)
        if previous_split_filter is not None:
            app.removeEventFilter(previous_split_filter)
        split_filter = _TimelineSplitSnapFilter(root)
        app.installEventFilter(split_filter)
        root._aavc_timeline_split_snap_filter = split_filter

    return True
