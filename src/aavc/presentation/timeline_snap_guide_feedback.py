from __future__ import annotations

from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.motion_preview import preview_scrub_seconds
from aavc.presentation.timeline_in_out import timeline_in_out_hit_point
from aavc.presentation.timeline_magnetic_edit import (
    timeline_magnetic_split_local_seconds,
    timeline_scene_start_seconds,
)
from aavc.presentation.timeline_magnetic_snap import timeline_magnetic_snap_target
from aavc.presentation.timeline_markers import timeline_marker_global_seconds
from aavc.presentation.timeline_preview_seek import timeline_resize_edge
from aavc.presentation.timeline_snap_guide import (
    hide_timeline_snap_guide,
    show_timeline_snap_guide,
)
from aavc.presentation.timeline_zoom_scroll import (
    DEFAULT_TIMELINE_ZOOM_PERCENT,
    normalize_timeline_zoom_percent,
)


def install_timeline_snap_guide_feedback(root: Any, project: ProjectState) -> bool:
    """Observe magnetic edit gestures and render a non-interactive visual snap guide."""

    from PySide6.QtCore import QEvent, QObject, Qt
    from PySide6.QtWidgets import (
        QApplication,
        QListWidget,
        QPushButton,
        QSlider,
        QWidget,
    )

    if not project.scenes:
        return False

    ruler = root.findChild(QWidget, "TimelineTimeRuler")
    if ruler is None:
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
    app: Any = QApplication.instance()
    if scene_list is None or progress_slider is None or app is None:
        return False

    active_scene_list: Any = scene_list
    active_slider: Any = progress_slider
    durations = tuple(scene.duration_seconds for scene in project.scenes)
    owner: Any = ruler.window()

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

    def split_targets() -> tuple[float, ...]:
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

    def current_global_seconds() -> float:
        row = int(active_scene_list.currentRow())
        if row < 0 or row >= len(durations):
            return 0.0
        local = preview_scrub_seconds(
            active_slider.value(),
            active_slider.maximum(),
            durations[row],
        )
        return timeline_marker_global_seconds(durations, row, local)

    def show_magnetic_target(pixel_x: float) -> None:
        snap = timeline_magnetic_snap_target(
            durations,
            pixel_x,
            stored_zoom_percent(),
            project.fps,
            markers_seconds=marker_seconds(),
            playhead_seconds=current_global_seconds(),
        )
        if snap is None:
            hide_timeline_snap_guide(root)
            return
        show_timeline_snap_guide(
            root,
            durations,
            snap[0],
            stored_zoom_percent(),
            snap[1],
        )

    class _RangeGuideFilter(QObject):
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
                raw_in = getattr(owner, "_aavc_timeline_in_seconds", None)
                raw_out = getattr(owner, "_aavc_timeline_out_seconds", None)
                in_point = None if raw_in is None else float(raw_in)
                out_point = None if raw_out is None else float(raw_out)
                self._dragging = (
                    timeline_in_out_hit_point(
                        durations,
                        in_point,
                        out_point,
                        float(event.position().x()),
                        stored_zoom_percent(),
                    )
                    is not None
                )
                if not self._dragging:
                    hide_timeline_snap_guide(root)
                return False

            if (
                event.type() == QEvent.Type.MouseMove
                and self._dragging
                and bool(event.buttons() & Qt.MouseButton.LeftButton)
            ):
                show_magnetic_target(float(event.position().x()))
                return False

            if (
                event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton
                and self._dragging
            ):
                self._dragging = False
                hide_timeline_snap_guide(root)
                return False
            return False

    button_indexes: dict[int, int] = {}
    timeline_buttons: list[Any] = []
    all_buttons = root.findChildren(QPushButton)
    for index, scene in enumerate(project.scenes):
        prefix = f"Sc{scene.scene_number:02d}\n"
        button = next(
            (candidate for candidate in all_buttons if candidate.text().startswith(prefix)),
            None,
        )
        if button is None:
            continue
        button_indexes[id(button)] = index
        timeline_buttons.append(button)

    class _ResizeGuideFilter(QObject):
        def __init__(self, parent: Any) -> None:
            super().__init__(parent)
            self._pressed_button_id: int | None = None
            self._press_global_x = 0.0
            self._resize_edge: str | None = None

        def reset(self) -> None:
            self._pressed_button_id = None
            self._press_global_x = 0.0
            self._resize_edge = None
            hide_timeline_snap_guide(root)

        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802
            if id(watched) not in button_indexes:
                return False

            if (
                event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._pressed_button_id = id(watched)
                self._press_global_x = float(event.globalPosition().x())
                self._resize_edge = timeline_resize_edge(
                    event.position().x(),
                    watched.width(),
                )
                if self._resize_edge is None:
                    hide_timeline_snap_guide(root)
                return False

            if (
                event.type() == QEvent.Type.MouseMove
                and self._pressed_button_id == id(watched)
                and self._resize_edge is not None
                and bool(event.buttons() & Qt.MouseButton.LeftButton)
            ):
                distance = abs(float(event.globalPosition().x()) - self._press_global_x)
                if distance < QApplication.startDragDistance():
                    return False
                pointer_x = float(
                    ruler.mapFromGlobal(event.globalPosition().toPoint()).x()
                )
                show_magnetic_target(pointer_x)
                return False

            if (
                event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton
                and self._pressed_button_id == id(watched)
            ):
                self.reset()
                return False
            return False

    class _SplitGuideFilter(QObject):
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

            focus = app.focusWidget()
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
                markers_seconds=split_targets(),
            )
            if not snapped or abs(snapped_local - local_seconds) < 0.0005:
                return False
            global_seconds = timeline_scene_start_seconds(durations, row) + snapped_local
            show_timeline_snap_guide(
                root,
                durations,
                global_seconds,
                stored_zoom_percent(),
                "split",
                auto_hide_ms=900,
            )
            return False

    previous_range = getattr(root, "_aavc_timeline_snap_range_filter", None)
    if previous_range is not None:
        ruler.removeEventFilter(previous_range)
    range_filter = _RangeGuideFilter(root)
    ruler.installEventFilter(range_filter)
    root._aavc_timeline_snap_range_filter = range_filter

    previous_resize = getattr(root, "_aavc_timeline_snap_resize_filter", None)
    if previous_resize is not None:
        for button in timeline_buttons:
            button.removeEventFilter(previous_resize)
    resize_filter = _ResizeGuideFilter(root)
    for button in timeline_buttons:
        button.installEventFilter(resize_filter)
    root._aavc_timeline_snap_resize_filter = resize_filter

    previous_split = getattr(root, "_aavc_timeline_snap_split_filter", None)
    if previous_split is not None:
        app.removeEventFilter(previous_split)
    split_filter = _SplitGuideFilter(root)
    app.installEventFilter(split_filter)
    root._aavc_timeline_snap_split_filter = split_filter
    return True
