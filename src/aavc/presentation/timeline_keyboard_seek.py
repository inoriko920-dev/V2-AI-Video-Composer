from __future__ import annotations

from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.motion_preview import preview_scrub_seconds
from aavc.presentation.timeline_ruler_seek import timeline_slider_value_for_local_seconds

KEYBOARD_TIME_JUMP_SECONDS = 1.0


def timeline_frame_step_seconds(fps: int | float) -> float:
    """Return one frame duration using a safe positive project FPS."""

    normalized_fps = max(1, int(round(float(fps))))
    return 1.0 / normalized_fps


def timeline_keyboard_seek_target(
    durations_seconds: tuple[float, ...],
    scene_index: int,
    local_seconds: float,
    delta_seconds: float,
) -> tuple[int, float] | None:
    """Move a Scene-local position by a global time delta across Scene boundaries."""

    if not durations_seconds:
        return None

    durations = tuple(max(0.0, float(item)) for item in durations_seconds)
    index = max(0, min(len(durations) - 1, int(scene_index)))
    current_local = max(0.0, min(durations[index], float(local_seconds)))
    current_global = sum(durations[:index]) + current_local
    total = sum(durations)
    target_global = max(0.0, min(total, current_global + float(delta_seconds)))

    if target_global >= total:
        last_index = len(durations) - 1
        return last_index, durations[last_index]

    elapsed = 0.0
    last_index = len(durations) - 1
    for target_index, duration in enumerate(durations):
        scene_end = elapsed + duration
        if target_global < scene_end:
            return target_index, max(0.0, target_global - elapsed)
        if abs(target_global - scene_end) < 1e-12:
            if target_index < last_index:
                return target_index + 1, 0.0
            return target_index, duration
        elapsed = scene_end

    return last_index, durations[last_index]


def timeline_keyboard_terminal_target(
    durations_seconds: tuple[float, ...],
    *,
    end: bool,
) -> tuple[int, float] | None:
    """Return the project Home/End target as Scene index plus local seconds."""

    if not durations_seconds:
        return None
    durations = tuple(max(0.0, float(item)) for item in durations_seconds)
    if end:
        last_index = len(durations) - 1
        return last_index, durations[last_index]
    return 0, 0.0


def install_timeline_keyboard_seek(root: Any, project: ProjectState) -> bool:
    """Enable precise timeline navigation and J/K/L preview transport shortcuts."""

    from PySide6.QtCore import QEvent, QObject, Qt, QTimer
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QApplication,
        QLineEdit,
        QListWidget,
        QPlainTextEdit,
        QPushButton,
        QSlider,
        QTextEdit,
    )

    if not project.scenes:
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
    play_button = next(
        (button for button in root.findChildren(QPushButton) if button.text() in {"▶", "⏸"}),
        None,
    )
    app: Any = QApplication.instance()
    if scene_list is None or progress_slider is None or app is None:
        return False

    durations = tuple(scene.duration_seconds for scene in project.scenes)
    frame_seconds = timeline_frame_step_seconds(project.fps)
    state_scene_index = max(0, min(len(durations) - 1, scene_list.currentRow()))
    state_local_seconds = preview_scrub_seconds(
        progress_slider.value(),
        progress_slider.maximum(),
        durations[state_scene_index],
    )
    applying_keyboard_seek = False

    reverse_timer = QTimer(root)
    reverse_timer.setTimerType(Qt.TimerType.PreciseTimer)
    reverse_timer.setInterval(max(15, int(round(frame_seconds * 1000.0))))

    def sync_from_slider(value: int) -> None:
        nonlocal state_scene_index, state_local_seconds
        if applying_keyboard_seek:
            return
        row = scene_list.currentRow()
        if row < 0 or row >= len(durations):
            return
        state_scene_index = row
        state_local_seconds = preview_scrub_seconds(
            value,
            progress_slider.maximum(),
            durations[row],
        )

    def sync_from_scene(row: int) -> None:
        nonlocal state_scene_index, state_local_seconds
        if applying_keyboard_seek or row < 0 or row >= len(durations):
            return
        state_scene_index = row
        state_local_seconds = 0.0

    def seek_to_target(target: tuple[int, float] | None) -> tuple[int, float] | None:
        nonlocal applying_keyboard_seek, state_scene_index, state_local_seconds
        if target is None:
            return None
        target_index, target_local = target
        applying_keyboard_seek = True
        try:
            if scene_list.currentRow() != target_index:
                scene_list.setCurrentRow(target_index)
            slider_value = timeline_slider_value_for_local_seconds(
                target_local,
                durations[target_index],
                progress_slider.maximum(),
            )
            progress_slider.setValue(slider_value)
            progress_slider.sliderMoved.emit(slider_value)
            progress_slider.sliderReleased.emit()
            state_scene_index = target_index
            state_local_seconds = target_local
        finally:
            applying_keyboard_seek = False
        return target

    def seek_by(delta_seconds: float) -> tuple[int, float] | None:
        return seek_to_target(
            timeline_keyboard_seek_target(
                durations,
                state_scene_index,
                state_local_seconds,
                delta_seconds,
            )
        )

    def pause_forward_preserving_position() -> None:
        if play_button is None or play_button.text() != "⏸":
            return
        preserved = (state_scene_index, state_local_seconds)
        play_button.click()
        seek_to_target(preserved)

    def pause_transport() -> None:
        reverse_timer.stop()
        pause_forward_preserving_position()

    def start_forward() -> None:
        reverse_timer.stop()
        if play_button is None or play_button.text() == "⏸":
            return
        play_button.click()

    def reverse_tick() -> None:
        target = seek_by(-frame_seconds)
        if target is None:
            reverse_timer.stop()
            return
        target_index, target_local = target
        if target_index == 0 and target_local <= 1e-12:
            reverse_timer.stop()

    def start_reverse() -> None:
        pause_forward_preserving_position()
        if state_scene_index == 0 and state_local_seconds <= 1e-12:
            return
        reverse_timer.start()

    reverse_timer.timeout.connect(reverse_tick)

    class _KeyboardSeekFilter(QObject):
        def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802
            del watched
            if event.type() != QEvent.Type.KeyPress or not root.isVisible():
                return False

            key = event.key()
            supported_keys = {
                Qt.Key.Key_Left,
                Qt.Key.Key_Right,
                Qt.Key.Key_Home,
                Qt.Key.Key_End,
                Qt.Key.Key_J,
                Qt.Key.Key_K,
                Qt.Key.Key_L,
            }
            if key not in supported_keys:
                return False

            modifiers = event.modifiers()
            if key in {Qt.Key.Key_Left, Qt.Key.Key_Right}:
                if modifiers not in {
                    Qt.KeyboardModifier.NoModifier,
                    Qt.KeyboardModifier.ShiftModifier,
                }:
                    return False
            elif modifiers != Qt.KeyboardModifier.NoModifier:
                return False

            focus = app.focusWidget()
            if isinstance(
                focus,
                (QLineEdit, QAbstractSpinBox, QTextEdit, QPlainTextEdit),
            ):
                return False
            if focus is not None and focus is not root and not root.isAncestorOf(focus):
                return False

            if key in {Qt.Key.Key_Left, Qt.Key.Key_Right}:
                reverse_timer.stop()
                magnitude = (
                    KEYBOARD_TIME_JUMP_SECONDS
                    if modifiers == Qt.KeyboardModifier.ShiftModifier
                    else frame_seconds
                )
                direction = -1.0 if key == Qt.Key.Key_Left else 1.0
                seek_by(direction * magnitude)
            elif key == Qt.Key.Key_Home:
                reverse_timer.stop()
                seek_to_target(timeline_keyboard_terminal_target(durations, end=False))
            elif key == Qt.Key.Key_End:
                reverse_timer.stop()
                seek_to_target(timeline_keyboard_terminal_target(durations, end=True))
            elif key == Qt.Key.Key_J:
                start_reverse()
            elif key == Qt.Key.Key_K:
                pause_transport()
            else:
                start_forward()

            event.accept()
            return True

    previous_filter = getattr(root, "_aavc_timeline_keyboard_seek_filter", None)
    if previous_filter is not None:
        app.removeEventFilter(previous_filter)
    previous_reverse_timer = getattr(root, "_aavc_timeline_reverse_timer", None)
    if previous_reverse_timer is not None:
        previous_reverse_timer.stop()

    event_filter = _KeyboardSeekFilter(root)
    app.installEventFilter(event_filter)
    root._aavc_timeline_keyboard_seek_filter = event_filter
    root._aavc_timeline_reverse_timer = reverse_timer
    progress_slider.valueChanged.connect(sync_from_slider)
    scene_list.currentRowChanged.connect(sync_from_scene)
    progress_slider.setToolTip(
        f"{progress_slider.toolTip()} Left/Right = 1 frame; Shift+Left/Right = 1 detik; "
        "Home/End = awal/akhir project; J/K/L = reverse/pause/play."
    )
    return True
