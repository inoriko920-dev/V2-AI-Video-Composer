from __future__ import annotations

from typing import Any

from aavc.presentation.timeline_zoom_scroll import timeline_global_seconds_pixel_x

TIMELINE_SNAP_GUIDE_LABEL_MARGIN_PX = 4
TIMELINE_SNAP_GUIDE_LABEL_PADDING_X_PX = 6
TIMELINE_SNAP_GUIDE_LABEL_HEIGHT_PX = 18


def timeline_snap_guide_label(kind: str) -> str:
    """Return the compact user-facing label for a magnetic snap target."""

    return {
        "marker": "Marker",
        "scene": "Scene Edge",
        "playhead": "Playhead",
        "split": "Split Target",
    }.get(str(kind), "Snap")


def timeline_snap_guide_label_left(
    target_x: int | float,
    track_width: int | float,
    label_width: int | float,
    *,
    margin_px: int = TIMELINE_SNAP_GUIDE_LABEL_MARGIN_PX,
) -> int:
    """Center a snap label on the target while keeping it inside the track."""

    track = max(1, int(round(float(track_width))))
    width = max(1, min(track, int(round(float(label_width)))))
    margin = max(0, int(margin_px))
    maximum_left = max(0, track - width - margin)
    preferred = int(round(float(target_x) - width / 2.0))
    return max(margin if track - width >= margin * 2 else 0, min(maximum_left, preferred))


def hide_timeline_snap_guide(root: Any) -> None:
    """Hide any active magnetic guide and invalidate delayed hide callbacks."""

    generation = int(getattr(root, "_aavc_timeline_snap_guide_generation", 0)) + 1
    root._aavc_timeline_snap_guide_generation = generation
    guide = getattr(root, "_aavc_timeline_snap_guide", None)
    if guide is not None:
        guide.hide()


def show_timeline_snap_guide(
    root: Any,
    durations_seconds: tuple[float, ...],
    target_seconds: float,
    zoom_percent: int | float,
    kind: str,
    *,
    auto_hide_ms: int | None = None,
) -> bool:
    """Show a mouse-transparent vertical magnetic guide on the timeline track."""

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import QWidget

    track = root.findChild(QWidget, "TimelineSceneTrack")
    if track is None or not durations_seconds:
        hide_timeline_snap_guide(root)
        return False

    class _TimelineSnapGuide(QWidget):
        def __init__(self, parent: Any) -> None:
            super().__init__(parent)
            self._target_x = 0
            self._label = "Snap"
            self.setObjectName("TimelineMagneticSnapGuide")
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.hide()

        def set_target(self, target_x: int, label: str) -> None:
            self._target_x = max(0, min(max(0, self.width() - 1), int(target_x)))
            self._label = str(label)
            self.update()

        def paintEvent(self, event: Any) -> None:  # noqa: N802
            del event
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            line_color = QColor("#0EA5E9")
            painter.setPen(QPen(line_color, 1, Qt.PenStyle.DashLine))
            painter.drawLine(self._target_x, 0, self._target_x, self.height())

            metrics = painter.fontMetrics()
            label_width = (
                metrics.horizontalAdvance(self._label)
                + TIMELINE_SNAP_GUIDE_LABEL_PADDING_X_PX * 2
            )
            label_left = timeline_snap_guide_label_left(
                self._target_x,
                self.width(),
                label_width,
            )
            label_width = min(max(1, label_width), max(1, self.width() - label_left))
            painter.fillRect(
                label_left,
                2,
                label_width,
                TIMELINE_SNAP_GUIDE_LABEL_HEIGHT_PX,
                QColor("#E0F2FE"),
            )
            painter.setPen(QColor("#0369A1"))
            painter.drawText(
                label_left + TIMELINE_SNAP_GUIDE_LABEL_PADDING_X_PX,
                15,
                self._label,
            )
            painter.end()

    guide = getattr(root, "_aavc_timeline_snap_guide", None)
    if guide is None or guide.parentWidget() is not track:
        guide = _TimelineSnapGuide(track)
        root._aavc_timeline_snap_guide = guide

    guide.setGeometry(0, 0, max(1, track.width()), max(1, track.height()))
    target_x = timeline_global_seconds_pixel_x(
        durations_seconds,
        target_seconds,
        zoom_percent,
    )
    guide.set_target(target_x, timeline_snap_guide_label(kind))
    guide.show()
    guide.raise_()

    generation = int(getattr(root, "_aavc_timeline_snap_guide_generation", 0)) + 1
    root._aavc_timeline_snap_guide_generation = generation
    if auto_hide_ms is not None and int(auto_hide_ms) > 0:
        delay = int(auto_hide_ms)

        def hide_if_current() -> None:
            if int(getattr(root, "_aavc_timeline_snap_guide_generation", 0)) != generation:
                return
            hide_timeline_snap_guide(root)

        QTimer.singleShot(delay, hide_if_current)
    return True
