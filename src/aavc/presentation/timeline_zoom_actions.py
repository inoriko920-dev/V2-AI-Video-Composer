from __future__ import annotations

from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.timeline_zoom_scroll import (
    DEFAULT_TIMELINE_ZOOM_PERCENT,
    MAX_TIMELINE_ZOOM_PERCENT,
    MIN_TIMELINE_ZOOM_PERCENT,
    timeline_track_pixel_width,
)

TIMELINE_ZOOM_FIT_BUTTON_OBJECT_NAME = "TimelineZoomFit"
TIMELINE_ZOOM_RESET_BUTTON_OBJECT_NAME = "TimelineZoomReset"


def timeline_fit_zoom_percent(
    durations_seconds: tuple[float, ...],
    viewport_width_px: int,
) -> int:
    """Return the largest integer zoom whose track fits the visible viewport."""

    if not durations_seconds:
        return DEFAULT_TIMELINE_ZOOM_PERCENT

    available_width = max(1, int(viewport_width_px))
    if (
        timeline_track_pixel_width(durations_seconds, MIN_TIMELINE_ZOOM_PERCENT)
        > available_width
    ):
        return MIN_TIMELINE_ZOOM_PERCENT
    if (
        timeline_track_pixel_width(durations_seconds, MAX_TIMELINE_ZOOM_PERCENT)
        <= available_width
    ):
        return MAX_TIMELINE_ZOOM_PERCENT

    low = MIN_TIMELINE_ZOOM_PERCENT
    high = MAX_TIMELINE_ZOOM_PERCENT
    best = MIN_TIMELINE_ZOOM_PERCENT
    while low <= high:
        middle = (low + high) // 2
        width = timeline_track_pixel_width(durations_seconds, middle)
        if width <= available_width:
            best = middle
            low = middle + 1
        else:
            high = middle - 1
    return best


def install_timeline_zoom_actions(root: Any, project: ProjectState) -> bool:
    """Install Fit and 100% reset controls beside the existing timeline zoom box."""

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QScrollArea, QSpinBox, QToolButton

    scroll = root.findChild(QScrollArea, "TimelineSceneScrollArea")
    zoom_box = root.findChild(QSpinBox, "TimelineZoomPercent")
    if scroll is None or zoom_box is None or not project.scenes:
        return False

    timeline = zoom_box.parentWidget()
    if timeline is None or timeline.layout() is None:
        return False
    root_layout = timeline.layout()
    header_layout = root_layout.itemAt(0).layout() if root_layout.count() else None
    if header_layout is None:
        return False

    existing_fit = root.findChild(QToolButton, TIMELINE_ZOOM_FIT_BUTTON_OBJECT_NAME)
    existing_reset = root.findChild(QToolButton, TIMELINE_ZOOM_RESET_BUTTON_OBJECT_NAME)
    if existing_fit is not None and existing_reset is not None:
        return True

    owner: Any = timeline.window()
    durations = tuple(scene.duration_seconds for scene in project.scenes)

    def status(message: str) -> None:
        status_bar = owner.statusBar() if hasattr(owner, "statusBar") else None
        if status_bar is not None:
            status_bar.showMessage(message, 4500)

    fit_button = QToolButton(timeline)
    fit_button.setObjectName(TIMELINE_ZOOM_FIT_BUTTON_OBJECT_NAME)
    fit_button.setText("Fit")
    fit_button.setToolTip(
        "Sesuaikan zoom agar seluruh timeline muat selebar area yang terlihat."
    )
    fit_button.setStyleSheet("QToolButton { padding: 2px 7px; font-size: 9px; }")

    def fit_timeline() -> None:
        target_zoom = timeline_fit_zoom_percent(durations, scroll.viewport().width())
        zoom_box.setValue(target_zoom)

        def finish_fit() -> None:
            scroll.horizontalScrollBar().setValue(0)
            status(f"Zoom timeline Fit: {target_zoom}%.")

        QTimer.singleShot(0, finish_fit)

    fit_button.clicked.connect(fit_timeline)

    reset_button = QToolButton(timeline)
    reset_button.setObjectName(TIMELINE_ZOOM_RESET_BUTTON_OBJECT_NAME)
    reset_button.setText("100%")
    reset_button.setToolTip("Kembalikan zoom timeline ke 100%.")
    reset_button.setStyleSheet("QToolButton { padding: 2px 7px; font-size: 9px; }")

    def reset_zoom() -> None:
        zoom_box.setValue(DEFAULT_TIMELINE_ZOOM_PERCENT)
        status("Zoom timeline dikembalikan ke 100%.")

    reset_button.clicked.connect(reset_zoom)

    header_layout.addWidget(fit_button)
    header_layout.addWidget(reset_button)
    root._aavc_timeline_zoom_fit_button = fit_button
    root._aavc_timeline_zoom_reset_button = reset_button
    return True
