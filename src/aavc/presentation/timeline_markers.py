from __future__ import annotations

from math import floor
from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.motion_preview import preview_scrub_seconds
from aavc.presentation.timeline_ruler_seek import timeline_slider_value_for_local_seconds
from aavc.presentation.timeline_zoom_scroll import (
    DEFAULT_TIMELINE_ZOOM_PERCENT,
    normalize_timeline_zoom_percent,
    timeline_global_seconds_pixel_x,
)

MARKER_TIME_EPSILON_SECONDS = 1e-6
TIMELINE_MARKER_WIDTH_PX = 9


def timeline_marker_snap_seconds(
    global_seconds: float,
    total_duration_seconds: float,
    fps: int | float,
) -> float:
    """Clamp a marker to the project and snap it to the nearest frame."""

    total = max(0.0, float(total_duration_seconds))
    normalized_fps = max(1, int(round(float(fps))))
    value = max(0.0, min(total, float(global_seconds)))
    frame_index = floor(value * normalized_fps + 0.5 + 1e-12)
    snapped = frame_index / normalized_fps
    return round(max(0.0, min(total, snapped)), 6)


def timeline_toggle_marker(
    markers_seconds: tuple[float, ...],
    global_seconds: float,
    total_duration_seconds: float,
    fps: int | float,
) -> tuple[tuple[float, ...], bool]:
    """Toggle a frame-snapped marker. The bool is True when a marker was added."""

    total = max(0.0, float(total_duration_seconds))
    normalized_fps = max(1, int(round(float(fps))))
    snapped = timeline_marker_snap_seconds(global_seconds, total, normalized_fps)
    tolerance = 0.5 / normalized_fps + MARKER_TIME_EPSILON_SECONDS
    normalized = tuple(
        sorted(
            {
                round(max(0.0, min(total, float(marker))), 6)
                for marker in markers_seconds
            }
        )
    )
    nearby = next(
        (marker for marker in normalized if abs(marker - snapped) <= tolerance),
        None,
    )
    if nearby is not None:
        return tuple(marker for marker in normalized if marker != nearby), False
    return tuple(sorted((*normalized, snapped))), True


def timeline_adjacent_marker(
    markers_seconds: tuple[float, ...],
    current_seconds: float,
    direction: int,
) -> float | None:
    """Return the previous/next marker without wrapping around project edges."""

    markers = tuple(sorted({float(marker) for marker in markers_seconds}))
    current = float(current_seconds)
    if direction > 0:
        return next(
            (marker for marker in markers if marker > current + MARKER_TIME_EPSILON_SECONDS),
            None,
        )
    if direction < 0:
        return next(
            (
                marker
                for marker in reversed(markers)
                if marker < current - MARKER_TIME_EPSILON_SECONDS
            ),
            None,
        )
    return None


def timeline_marker_global_seconds(
    durations_seconds: tuple[float, ...],
    scene_index: int,
    local_seconds: float,
) -> float:
    """Convert a Scene-local playhead position to global project seconds."""

    if not durations_seconds:
        return 0.0
    durations = tuple(max(0.0, float(item)) for item in durations_seconds)
    index = max(0, min(len(durations) - 1, int(scene_index)))
    local = max(0.0, min(durations[index], float(local_seconds)))
    return sum(durations[:index]) + local


def timeline_marker_seek_target(
    durations_seconds: tuple[float, ...],
    global_seconds: float,
) -> tuple[int, float] | None:
    """Map a global marker time to Scene index plus Scene-local seconds."""

    if not durations_seconds:
        return None
    durations = tuple(max(0.0, float(item)) for item in durations_seconds)
    total = sum(durations)
    target = max(0.0, min(total, float(global_seconds)))
    if target >= total:
        last_index = len(durations) - 1
        return last_index, durations[last_index]

    elapsed = 0.0
    last_index = len(durations) - 1
    for index, duration in enumerate(durations):
        scene_end = elapsed + duration
        if target < scene_end:
            return index, max(0.0, target - elapsed)
        if abs(target - scene_end) <= MARKER_TIME_EPSILON_SECONDS:
            if index < last_index:
                return index + 1, 0.0
            return index, duration
        elapsed = scene_end
    return last_index, durations[last_index]


def install_timeline_markers(root: Any, project: ProjectState) -> bool:
    """Install session-only timeline markers and keyboard marker navigation."""

    from PySide6.QtCore import QEvent, QObject, QPointF, Qt
    from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QApplication,
        QLineEdit,
        QListWidget,
        QPlainTextEdit,
        QSlider,
        QSpinBox,
        QTextEdit,
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

    durations = tuple(scene.duration_seconds for scene in project.scenes)
    total_duration = sum(max(0.0, float(item)) for item in durations)
    owner: Any = ruler.window()
    signature = (project.source_docx, project.asset_directory)
    if getattr(owner, "_aavc_timeline_marker_project_signature", None) != signature:
        owner._aavc_timeline_marker_project_signature = signature
        owner._aavc_timeline_markers_seconds = ()
    elif not hasattr(owner, "_aavc_timeline_markers_seconds"):
        owner._aavc_timeline_markers_seconds = ()

    class _TimelineMarkerGlyph(QWidget):
        def __init__(self, parent: Any) -> None:
            super().__init__(parent)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        def paintEvent(self, event: Any) -> None:  # noqa: N802
            del event
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            center_x = self.width() / 2.0
            color = QColor("#F59E0B")
            painter.setPen(QPen(color, 2))
            painter.drawLine(
                int(round(center_x)),
                7,
                int(round(center_x)),
                self.height(),
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawPolygon(
                QPolygonF(
                    (
                        QPointF(center_x - 4.0, 0.0),
                        QPointF(center_x + 4.0, 0.0),
                        QPointF(center_x, 7.0),
                    )
                )
            )
            painter.end()

    marker_glyphs: list[Any] = []
    root._aavc_timeline_marker_glyphs = marker_glyphs

    def markers() -> tuple[float, ...]:
        stored = getattr(owner, "_aavc_timeline_markers_seconds", ())
        return tuple(float(item) for item in stored)

    def stored_zoom_percent() -> int:
        value = owner.property("aavcTimelineZoomPercent")
        try:
            raw = DEFAULT_TIMELINE_ZOOM_PERCENT if value is None else int(value)
        except (TypeError, ValueError):
            raw = DEFAULT_TIMELINE_ZOOM_PERCENT
        return normalize_timeline_zoom_percent(raw)

    def refresh_marker_glyphs() -> None:
        for glyph in marker_glyphs:
            glyph.deleteLater()
        marker_glyphs.clear()
        zoom = stored_zoom_percent()
        for marker_seconds in markers():
            x = timeline_global_seconds_pixel_x(durations, marker_seconds, zoom)
            glyph = _TimelineMarkerGlyph(ruler)
            glyph.setObjectName("TimelineSessionMarker")
            glyph.setGeometry(
                max(0, x - TIMELINE_MARKER_WIDTH_PX // 2),
                0,
                TIMELINE_MARKER_WIDTH_PX,
                max(1, ruler.height()),
            )
            glyph.setToolTip(f"Marker sesi · {marker_seconds:.3f} detik")
            glyph.show()
            glyph.raise_()
            marker_glyphs.append(glyph)

    def show_status(message: str) -> None:
        status_bar = owner.statusBar() if hasattr(owner, "statusBar") else None
        if status_bar is not None:
            status_bar.showMessage(message, 5000)

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

    def seek_global(global_seconds: float) -> None:
        target = timeline_marker_seek_target(durations, global_seconds)
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

    def toggle_current_marker() -> None:
        playhead_seconds = current_global_seconds()
        updated, added = timeline_toggle_marker(
            markers(),
            playhead_seconds,
            total_duration,
            project.fps,
        )
        owner._aavc_timeline_markers_seconds = updated
        refresh_marker_glyphs()
        action = "ditambahkan" if added else "dihapus"
        marker_time = timeline_marker_snap_seconds(
            playhead_seconds,
            total_duration,
            project.fps,
        )
        show_status(
            f"Marker {action} pada {marker_time:.3f} detik. "
            "Marker ini hanya tersimpan selama sesi editor."
        )

    def goto_marker(direction: int) -> None:
        target = timeline_adjacent_marker(
            markers(),
            current_global_seconds(),
            direction,
        )
        if target is None:
            show_status(
                "Tidak ada marker berikutnya."
                if direction > 0
                else "Tidak ada marker sebelumnya."
            )
            return
        seek_global(target)
        show_status(f"Playhead dipindah ke marker {target:.3f} detik.")

    class _TimelineMarkerKeyFilter(QObject):
        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802
            del watched
            if event.type() != QEvent.Type.KeyPress or not root.isVisible():
                return False
            if event.key() != Qt.Key.Key_M:
                return False

            focus = app.focusWidget()
            if isinstance(
                focus,
                (QLineEdit, QAbstractSpinBox, QTextEdit, QPlainTextEdit),
            ):
                return False
            if focus is not None and focus is not root and not root.isAncestorOf(focus):
                return False

            modifiers = event.modifiers()
            if modifiers == Qt.KeyboardModifier.NoModifier:
                toggle_current_marker()
            elif modifiers == Qt.KeyboardModifier.ShiftModifier:
                goto_marker(1)
            elif modifiers == (
                Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
            ):
                goto_marker(-1)
            else:
                return False
            event.accept()
            return True

    previous_filter = getattr(root, "_aavc_timeline_marker_key_filter", None)
    if previous_filter is not None:
        app.removeEventFilter(previous_filter)

    event_filter = _TimelineMarkerKeyFilter(root)
    app.installEventFilter(event_filter)
    root._aavc_timeline_marker_key_filter = event_filter

    zoom_box = root.findChild(QSpinBox, "TimelineZoomPercent")
    if zoom_box is not None:
        zoom_box.valueChanged.connect(lambda _value: refresh_marker_glyphs())

    ruler.setToolTip(
        f"{ruler.toolTip()} M = tambah/hapus marker; Shift+M = marker berikutnya; "
        "Ctrl+Shift+M = marker sebelumnya. Marker hanya untuk sesi ini."
    )
    refresh_marker_glyphs()
    return True
