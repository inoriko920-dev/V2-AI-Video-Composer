from __future__ import annotations

from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.motion_preview import preview_scrub_seconds
from aavc.presentation.timeline_in_out import (
    TimelineRangePoint,
    timeline_drag_in_out_point,
    timeline_in_out_drag_seconds,
    timeline_in_out_hit_point,
)
from aavc.presentation.timeline_magnet_control import (
    install_timeline_magnet_control,
    timeline_magnet_active_for_owner,
)
from aavc.presentation.timeline_magnetic_snap import timeline_magnetic_snap_target
from aavc.presentation.timeline_markers import timeline_marker_global_seconds
from aavc.presentation.timeline_snap_guide_feedback import (
    install_timeline_snap_guide_feedback,
)
from aavc.presentation.timeline_zoom_scroll import (
    DEFAULT_TIMELINE_ZOOM_PERCENT,
    normalize_timeline_zoom_percent,
)


def install_timeline_magnetic_in_out(root: Any, project: ProjectState) -> bool:
    """Add optional magnetic marker/Scene/playhead snapping to In/Out handle drag."""

    from PySide6.QtCore import QEvent, QObject, Qt
    from PySide6.QtWidgets import QListWidget, QSlider, QSpinBox, QWidget

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
    if scene_list is None or progress_slider is None:
        return False

    durations = tuple(scene.duration_seconds for scene in project.scenes)
    total_duration = sum(max(0.0, float(item)) for item in durations)
    owner: Any = ruler.window()
    zoom_box = root.findChild(QSpinBox, "TimelineZoomPercent")

    def stored_zoom_percent() -> int:
        value = owner.property("aavcTimelineZoomPercent")
        try:
            raw = DEFAULT_TIMELINE_ZOOM_PERCENT if value is None else int(value)
        except (TypeError, ValueError):
            raw = DEFAULT_TIMELINE_ZOOM_PERCENT
        return normalize_timeline_zoom_percent(raw)

    def range_points() -> tuple[float | None, float | None]:
        raw_in = getattr(owner, "_aavc_timeline_in_seconds", None)
        raw_out = getattr(owner, "_aavc_timeline_out_seconds", None)
        in_point = None if raw_in is None else float(raw_in)
        out_point = None if raw_out is None else float(raw_out)
        return in_point, out_point

    def current_global_seconds() -> float:
        row = int(scene_list.currentRow())
        if row < 0 or row >= len(durations):
            return 0.0
        local = preview_scrub_seconds(
            progress_slider.value(),
            progress_slider.maximum(),
            durations[row],
        )
        return timeline_marker_global_seconds(durations, row, local)

    def marker_seconds() -> tuple[float, ...]:
        raw = getattr(owner, "_aavc_timeline_markers_seconds", ())
        try:
            return tuple(float(item) for item in raw)
        except (TypeError, ValueError):
            return ()

    def refresh_existing_range_overlay() -> None:
        if zoom_box is not None:
            zoom_box.valueChanged.emit(zoom_box.value())
        else:
            ruler.update()

    def show_status(message: str) -> None:
        status_bar = owner.statusBar() if hasattr(owner, "statusBar") else None
        if status_bar is not None:
            status_bar.showMessage(message, 6000)

    def magnetic_drag(
        point: TimelineRangePoint,
        pixel_x: float,
        *,
        release: bool,
        alt_bypass: bool,
    ) -> None:
        raw_seconds = timeline_in_out_drag_seconds(
            durations,
            pixel_x,
            stored_zoom_percent(),
        )
        if raw_seconds is None:
            return

        snap = None
        if timeline_magnet_active_for_owner(owner, alt_bypass=alt_bypass):
            snap = timeline_magnetic_snap_target(
                durations,
                pixel_x,
                stored_zoom_percent(),
                project.fps,
                markers_seconds=marker_seconds(),
                playhead_seconds=current_global_seconds(),
            )
        target_seconds = raw_seconds if snap is None else snap[0]
        in_point, out_point = range_points()
        updated_in, updated_out = timeline_drag_in_out_point(
            in_point,
            out_point,
            point,
            target_seconds,
            total_duration,
            project.fps,
        )
        owner._aavc_timeline_in_seconds = updated_in
        owner._aavc_timeline_out_seconds = updated_out
        refresh_existing_range_overlay()

        if release:
            chosen = updated_in if point == "in" else updated_out
            if chosen is None:
                return
            label = "In" if point == "in" else "Out"
            if snap is None:
                suffix = " · Alt bypass." if alt_bypass else ""
                show_status(f"{label} point dipindah ke {chosen:.3f} detik{suffix}")
                return
            kind_label = {
                "marker": "marker",
                "scene": "batas Scene",
                "playhead": "playhead",
            }[snap[1]]
            show_status(
                f"{label} point dipindah ke {chosen:.3f} detik · magnetic snap ke {kind_label}."
            )

    class _TimelineMagneticInOutFilter(QObject):
        def __init__(self, parent: Any) -> None:
            super().__init__(parent)
            self._dragging_point: TimelineRangePoint | None = None

        def point_at_x(self, pixel_x: float) -> TimelineRangePoint | None:
            in_point, out_point = range_points()
            return timeline_in_out_hit_point(
                durations,
                in_point,
                out_point,
                pixel_x,
                stored_zoom_percent(),
            )

        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802
            if watched is not ruler:
                return False

            if (
                event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                alt_bypass = bool(
                    event.modifiers() & Qt.KeyboardModifier.AltModifier
                )
                if not timeline_magnet_active_for_owner(
                    owner,
                    alt_bypass=alt_bypass,
                ):
                    return False
                point = self.point_at_x(float(event.position().x()))
                if point is None:
                    return False
                self._dragging_point = point
                ruler.setCursor(Qt.CursorShape.SizeHorCursor)
                event.accept()
                return True

            if (
                event.type() == QEvent.Type.MouseMove
                and self._dragging_point is not None
                and bool(event.buttons() & Qt.MouseButton.LeftButton)
            ):
                alt_bypass = bool(
                    event.modifiers() & Qt.KeyboardModifier.AltModifier
                )
                magnetic_drag(
                    self._dragging_point,
                    float(event.position().x()),
                    release=False,
                    alt_bypass=alt_bypass,
                )
                ruler.setCursor(Qt.CursorShape.SizeHorCursor)
                event.accept()
                return True

            if (
                event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton
                and self._dragging_point is not None
            ):
                point = self._dragging_point
                self._dragging_point = None
                alt_bypass = bool(
                    event.modifiers() & Qt.KeyboardModifier.AltModifier
                )
                magnetic_drag(
                    point,
                    float(event.position().x()),
                    release=True,
                    alt_bypass=alt_bypass,
                )
                ruler.setCursor(Qt.CursorShape.SplitHCursor)
                event.accept()
                return True

            return False

    previous_filter = getattr(root, "_aavc_timeline_magnetic_in_out_filter", None)
    if previous_filter is not None:
        ruler.removeEventFilter(previous_filter)

    event_filter = _TimelineMagneticInOutFilter(root)
    ruler.installEventFilter(event_filter)
    root._aavc_timeline_magnetic_in_out_filter = event_filter
    ruler.setToolTip(
        f"{ruler.toolTip()} Magnet ON: drag I/O snap ke marker, batas Scene, atau playhead; "
        "tahan Alt untuk bypass sementara."
    )
    install_timeline_magnet_control(root)
    install_timeline_snap_guide_feedback(root, project)
    return True
