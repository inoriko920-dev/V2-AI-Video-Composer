from __future__ import annotations

from math import ceil
from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.timeline_smooth_follow import (
    TIMELINE_FOLLOW_ANIMATION_MS,
    timeline_smooth_follow_scroll_target,
)

MIN_TIMELINE_ZOOM_PERCENT = 50
MAX_TIMELINE_ZOOM_PERCENT = 400
DEFAULT_TIMELINE_ZOOM_PERCENT = 100
DEFAULT_TIMELINE_FOLLOW_PLAYHEAD = True
TIMELINE_FOLLOW_PLAYHEAD_PROPERTY = "aavcTimelineFollowPlayhead"
TIMELINE_PIXELS_PER_SECOND = 48.0
MIN_TIMELINE_SCENE_WIDTH_PX = 56
MAX_TIMELINE_SCENE_WIDTH_PX = 20000
TIMELINE_TRACK_SPACING_PX = 3
TIMELINE_RULER_HEIGHT_PX = 24
TIMELINE_PLAYHEAD_WIDTH_PX = 9
TIMELINE_RULER_TARGET_MAJOR_PX = 90.0
TIMELINE_RULER_MAX_MAJOR_TICKS = 2000
_TIMELINE_RULER_INTERVALS_SECONDS = (
    0.5,
    1.0,
    2.0,
    5.0,
    10.0,
    15.0,
    30.0,
    60.0,
    120.0,
    300.0,
    600.0,
    900.0,
    1800.0,
    3600.0,
    7200.0,
    21600.0,
    43200.0,
    86400.0,
)


def normalize_timeline_zoom_percent(value: int | float) -> int:
    return max(
        MIN_TIMELINE_ZOOM_PERCENT,
        min(MAX_TIMELINE_ZOOM_PERCENT, int(round(float(value)))),
    )


def normalize_timeline_follow_playhead(value: object) -> bool:
    """Normalize a persisted/session Follow Playhead value; default stays enabled."""

    if value is None:
        return DEFAULT_TIMELINE_FOLLOW_PLAYHEAD
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"0", "false", "off", "no"}:
            return False
        if normalized in {"1", "true", "on", "yes"}:
            return True
    return DEFAULT_TIMELINE_FOLLOW_PLAYHEAD


def timeline_should_follow_playhead(requested_follow: bool, setting: object) -> bool:
    """Return whether one playhead update may auto-scroll the timeline."""

    return bool(requested_follow) and normalize_timeline_follow_playhead(setting)


def timeline_scene_pixel_width(
    duration_seconds: float,
    zoom_percent: int | float,
) -> int:
    zoom = normalize_timeline_zoom_percent(zoom_percent) / 100.0
    width = int(round(max(0.0, float(duration_seconds)) * TIMELINE_PIXELS_PER_SECOND * zoom))
    return max(
        MIN_TIMELINE_SCENE_WIDTH_PX,
        min(MAX_TIMELINE_SCENE_WIDTH_PX, width),
    )


def timeline_track_pixel_width(
    durations_seconds: tuple[float, ...],
    zoom_percent: int | float,
) -> int:
    if not durations_seconds:
        return 0
    return sum(
        timeline_scene_pixel_width(duration, zoom_percent)
        for duration in durations_seconds
    ) + TIMELINE_TRACK_SPACING_PX * (len(durations_seconds) - 1)


def timeline_ruler_major_interval_seconds(
    zoom_percent: int | float,
    total_duration_seconds: float = 0.0,
) -> float:
    """Choose a readable ruler interval from zoom and total project duration."""

    zoom = normalize_timeline_zoom_percent(zoom_percent) / 100.0
    pixels_per_second = TIMELINE_PIXELS_PER_SECOND * zoom
    by_pixels = TIMELINE_RULER_TARGET_MAJOR_PX / pixels_per_second
    by_count = max(0.0, float(total_duration_seconds)) / TIMELINE_RULER_MAX_MAJOR_TICKS
    required = max(by_pixels, by_count)
    for interval in _TIMELINE_RULER_INTERVALS_SECONDS:
        if interval >= required:
            return interval
    return _TIMELINE_RULER_INTERVALS_SECONDS[-1]


def timeline_ruler_time_label(seconds: float) -> str:
    """Format a compact global project time label for the timeline ruler."""

    value = max(0.0, float(seconds))
    whole = int(value)
    fraction = value - whole
    hours, remainder = divmod(whole, 3600)
    minutes, second = divmod(remainder, 60)
    second_text = f"{second + fraction:04.1f}" if fraction >= 0.05 else f"{second:02d}"
    if hours:
        return f"{hours}:{minutes:02d}:{second_text}"
    return f"{minutes}:{second_text}"


def timeline_global_seconds_pixel_x(
    durations_seconds: tuple[float, ...],
    global_seconds: float,
    zoom_percent: int | float,
) -> int:
    """Map global project time to the visual timeline, respecting min Scene widths."""

    if not durations_seconds:
        return 0
    target = max(0.0, min(float(global_seconds), sum(max(0.0, item) for item in durations_seconds)))
    elapsed = 0.0
    x = 0.0
    last_index = len(durations_seconds) - 1
    for index, raw_duration in enumerate(durations_seconds):
        duration = max(0.0, float(raw_duration))
        width = timeline_scene_pixel_width(duration, zoom_percent)
        scene_end = elapsed + duration
        if target < scene_end or index == last_index:
            local = max(0.0, min(duration, target - elapsed))
            fraction = 0.0 if duration <= 0 else local / duration
            return int(round(x + width * fraction))
        elapsed = scene_end
        x += width
        if index < last_index:
            x += TIMELINE_TRACK_SPACING_PX
    return timeline_track_pixel_width(durations_seconds, zoom_percent)


def timeline_playhead_pixel_x(
    durations_seconds: tuple[float, ...],
    scene_index: int,
    local_seconds: float,
    zoom_percent: int | float,
) -> int:
    """Map selected Scene local time to its exact visual block position."""

    if not durations_seconds:
        return 0
    index = max(0, min(len(durations_seconds) - 1, int(scene_index)))
    x = 0
    for duration in durations_seconds[:index]:
        x += timeline_scene_pixel_width(duration, zoom_percent) + TIMELINE_TRACK_SPACING_PX
    duration = max(0.0, float(durations_seconds[index]))
    local = max(0.0, min(duration, float(local_seconds)))
    fraction = 0.0 if duration <= 0 else local / duration
    return int(round(x + timeline_scene_pixel_width(duration, zoom_percent) * fraction))


def _stored_int_property(owner: Any, name: str, default: int) -> int:
    value = owner.property(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def install_timeline_zoom_scroll(root: Any, project: ProjectState) -> bool:
    """Install timeline zoom, horizontal scroll, global ruler, and synced playhead."""

    from PySide6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, Qt, QTimer
    from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QPushButton,
        QScrollArea,
        QSlider,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

    labels = root.findChildren(QLabel)
    title = next(
        (label for label in labels if label.text().startswith("Timeline Scene ·")),
        None,
    )
    if title is None:
        return False

    timeline = title.parentWidget()
    if timeline is None or timeline.layout() is None:
        return False
    root_layout = timeline.layout()

    track_layout: Any | None = None
    for layout_index in range(root_layout.count()):
        candidate = root_layout.itemAt(layout_index).layout()
        if candidate is None:
            continue
        for item_index in range(candidate.count()):
            widget = candidate.itemAt(item_index).widget()
            if isinstance(widget, QLabel) and widget.text() == "V1  Scene":
                track_layout = candidate
                break
        if track_layout is not None:
            break
    if track_layout is None:
        return False

    buttons: list[Any] = []
    all_buttons = root.findChildren(QPushButton)
    for scene in project.scenes:
        prefix = f"Sc{scene.scene_number:02d}\n"
        button = next(
            (candidate for candidate in all_buttons if candidate.text().startswith(prefix)),
            None,
        )
        if button is None:
            return False
        buttons.append(button)

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

    owner = timeline.window()
    zoom_percent = normalize_timeline_zoom_percent(
        _stored_int_property(
            owner,
            "aavcTimelineZoomPercent",
            DEFAULT_TIMELINE_ZOOM_PERCENT,
        )
    )
    follow_playhead = normalize_timeline_follow_playhead(
        owner.property(TIMELINE_FOLLOW_PLAYHEAD_PROPERTY)
    )
    owner.setProperty(TIMELINE_FOLLOW_PLAYHEAD_PROPERTY, follow_playhead)
    saved_scroll = max(0, _stored_int_property(owner, "aavcTimelineScrollValue", 0))
    durations = tuple(scene.duration_seconds for scene in project.scenes)
    total_duration = sum(max(0.0, float(item)) for item in durations)

    for button in buttons:
        track_layout.removeWidget(button)

    scroll = QScrollArea(timeline)
    scroll.setObjectName("TimelineSceneScrollArea")
    scroll.setWidgetResizable(False)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    track_widget = QWidget(scroll)
    track_widget.setObjectName("TimelineSceneTrack")
    stack_layout = QVBoxLayout(track_widget)
    stack_layout.setContentsMargins(0, 0, 0, 0)
    stack_layout.setSpacing(0)

    class _TimelineRuler(QWidget):
        def __init__(self, parent: Any, zoom: int) -> None:
            super().__init__(parent)
            self._zoom_percent = normalize_timeline_zoom_percent(zoom)
            self.setFixedHeight(TIMELINE_RULER_HEIGHT_PX)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        def set_zoom(self, value: int) -> None:
            self._zoom_percent = normalize_timeline_zoom_percent(value)
            self.update()

        def paintEvent(self, event: Any) -> None:  # noqa: N802
            del event
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            painter.fillRect(self.rect(), QColor("#F8FAFC"))
            baseline_y = self.height() - 1
            painter.setPen(QPen(QColor("#CBD5E1"), 1))
            painter.drawLine(0, baseline_y, self.width(), baseline_y)
            if total_duration <= 0:
                painter.end()
                return

            major = timeline_ruler_major_interval_seconds(
                self._zoom_percent,
                total_duration,
            )
            minor = major / 5.0
            steps = max(1, int(ceil(total_duration / minor)))
            for step_index in range(steps + 1):
                seconds = min(total_duration, step_index * minor)
                x = timeline_global_seconds_pixel_x(
                    durations,
                    seconds,
                    self._zoom_percent,
                )
                ratio = seconds / major
                is_major = abs(ratio - round(ratio)) < 1e-6 or seconds >= total_duration
                if is_major:
                    painter.setPen(QPen(QColor("#64748B"), 1))
                    painter.drawLine(x, 11, x, baseline_y)
                    painter.setPen(QColor("#475569"))
                    painter.drawText(
                        min(max(2, x + 3), max(2, self.width() - 54)),
                        10,
                        timeline_ruler_time_label(seconds),
                    )
                else:
                    painter.setPen(QPen(QColor("#CBD5E1"), 1))
                    painter.drawLine(x, 17, x, baseline_y)
                if seconds >= total_duration:
                    break
            painter.end()

    class _TimelinePlayhead(QWidget):
        def __init__(self, parent: Any) -> None:
            super().__init__(parent)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.hide()

        def paintEvent(self, event: Any) -> None:  # noqa: N802
            del event
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            center_x = self.width() / 2.0
            color = QColor("#2563EB")
            painter.setPen(QPen(color, 2))
            painter.drawLine(int(round(center_x)), 7, int(round(center_x)), self.height())
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

    ruler = _TimelineRuler(track_widget, zoom_percent)
    ruler.setObjectName("TimelineTimeRuler")
    stack_layout.addWidget(ruler)

    scene_row = QWidget(track_widget)
    scene_row.setObjectName("TimelineSceneRow")
    content_layout = QHBoxLayout(scene_row)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(TIMELINE_TRACK_SPACING_PX)
    for button in buttons:
        content_layout.addWidget(button)
    stack_layout.addWidget(scene_row)

    playhead = _TimelinePlayhead(track_widget)
    playhead.setObjectName("TimelinePlayhead")

    scroll.setWidget(track_widget)
    track_layout.addWidget(scroll, 1)
    scene_height = max(
        44,
        max((button.sizeHint().height() for button in buttons), default=44),
    )
    scene_row.setMinimumHeight(scene_height)
    scroll.setMinimumHeight(
        TIMELINE_RULER_HEIGHT_PX
        + scene_height
        + scroll.horizontalScrollBar().sizeHint().height()
        + 4
    )

    bar = scroll.horizontalScrollBar()
    follow_animation = QPropertyAnimation(bar, b"value", root)
    follow_animation.setDuration(TIMELINE_FOLLOW_ANIMATION_MS)
    follow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    root._aavc_timeline_follow_animation = follow_animation

    def smooth_follow_playhead(x: int) -> None:
        target = timeline_smooth_follow_scroll_target(
            x,
            scroll.viewport().width(),
            bar.value(),
            bar.maximum(),
        )
        if target is None:
            return
        follow_animation.stop()
        follow_animation.setStartValue(bar.value())
        follow_animation.setEndValue(target)
        follow_animation.start()

    def update_playhead(*, follow: bool) -> None:
        if scene_list is None or progress_slider is None:
            playhead.hide()
            return
        row = int(scene_list.currentRow())
        if row < 0 or row >= len(durations):
            playhead.hide()
            return
        maximum = int(progress_slider.maximum())
        fraction = 0.0
        if maximum > 0:
            fraction = max(0.0, min(1.0, float(progress_slider.value()) / maximum))
        local_seconds = max(0.0, float(durations[row])) * fraction
        active_zoom = normalize_timeline_zoom_percent(
            _stored_int_property(owner, "aavcTimelineZoomPercent", zoom_percent)
        )
        x = timeline_playhead_pixel_x(durations, row, local_seconds, active_zoom)
        playhead.setGeometry(
            max(0, x - TIMELINE_PLAYHEAD_WIDTH_PX // 2),
            0,
            TIMELINE_PLAYHEAD_WIDTH_PX,
            max(1, track_widget.height()),
        )
        playhead.show()
        playhead.raise_()
        if timeline_should_follow_playhead(
            follow,
            owner.property(TIMELINE_FOLLOW_PLAYHEAD_PROPERTY),
        ):
            smooth_follow_playhead(x)

    def apply_zoom(value: int) -> None:
        normalized = normalize_timeline_zoom_percent(value)
        owner.setProperty("aavcTimelineZoomPercent", normalized)
        current_scroll = bar.value()
        for button, scene in zip(buttons, project.scenes, strict=True):
            button.setFixedWidth(
                timeline_scene_pixel_width(scene.duration_seconds, normalized)
            )
        track_width = timeline_track_pixel_width(durations, normalized)
        ruler.set_zoom(normalized)
        ruler.setFixedWidth(track_width)
        scene_row.setFixedWidth(track_width)
        track_widget.setFixedWidth(track_width)
        track_widget.adjustSize()
        QTimer.singleShot(0, lambda: update_playhead(follow=False))
        QTimer.singleShot(
            0,
            lambda: bar.setValue(min(current_scroll, bar.maximum())),
        )

    apply_zoom(zoom_percent)

    header_layout = root_layout.itemAt(0).layout() if root_layout.count() else None
    if header_layout is not None:
        snap_label = QLabel("Snap 0,1 dtk", timeline)
        snap_label.setStyleSheet("color:#64748B; font-size:9px;")
        header_layout.addWidget(snap_label)
        header_layout.addWidget(QLabel("Zoom", timeline))
        zoom_box = QSpinBox(timeline)
        zoom_box.setObjectName("TimelineZoomPercent")
        zoom_box.setRange(MIN_TIMELINE_ZOOM_PERCENT, MAX_TIMELINE_ZOOM_PERCENT)
        zoom_box.setSingleStep(25)
        zoom_box.setSuffix("%")
        zoom_box.setValue(zoom_percent)
        zoom_box.setToolTip("Zoom visual timeline. Tidak mengubah durasi atau file project.")
        zoom_box.valueChanged.connect(apply_zoom)
        header_layout.addWidget(zoom_box)

        follow_button = QPushButton(timeline)
        follow_button.setObjectName("TimelineFollowPlayhead")
        follow_button.setCheckable(True)
        follow_button.setChecked(follow_playhead)
        follow_button.setText("Follow ON" if follow_playhead else "Follow OFF")
        follow_button.setToolTip(
            "Aktif: timeline mengikuti playhead dengan scroll halus. Nonaktif: viewport tetap diam saat playhead bergerak."
        )
        follow_button.setStyleSheet("QPushButton { padding: 2px 7px; font-size: 9px; }")

        def set_follow_playhead(checked: bool) -> None:
            owner.setProperty(TIMELINE_FOLLOW_PLAYHEAD_PROPERTY, bool(checked))
            follow_button.setText("Follow ON" if checked else "Follow OFF")
            if not checked:
                follow_animation.stop()
            status_bar = owner.statusBar() if hasattr(owner, "statusBar") else None
            if status_bar is not None:
                state = "aktif" if checked else "nonaktif"
                status_bar.showMessage(f"Follow Playhead {state}.", 3500)
            if checked:
                update_playhead(follow=True)

        follow_button.toggled.connect(set_follow_playhead)
        header_layout.addWidget(follow_button)
        root._aavc_timeline_follow_playhead_button = follow_button

    bar.valueChanged.connect(
        lambda value: owner.setProperty("aavcTimelineScrollValue", int(value))
    )
    if scene_list is not None:
        scene_list.currentRowChanged.connect(
            lambda _row: QTimer.singleShot(0, lambda: update_playhead(follow=True))
        )
    if progress_slider is not None:
        progress_slider.valueChanged.connect(lambda _value: update_playhead(follow=True))

    def restore_scroll() -> None:
        bar.setValue(min(saved_scroll, bar.maximum()))
        update_playhead(follow=False)

    QTimer.singleShot(0, restore_scroll)

    for label in labels:
        if label.text().startswith("Lebar blok mengikuti durasi scene."):
            label.setText(
                f"{label.text()} Resize timeline snap 0,1 detik. Zoom {zoom_percent}%; "
                "ruler waktu global + playhead aktif; gunakan scrollbar untuk navigasi horizontal."
            )
            break
    return True
