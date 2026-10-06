from __future__ import annotations

from typing import Any, Literal

from aavc.domain.project.models import ProjectState
from aavc.presentation.motion_preview import preview_scrub_seconds
from aavc.presentation.timeline_markers import (
    timeline_marker_global_seconds,
    timeline_marker_seek_target,
)
from aavc.presentation.timeline_ruler_seek import timeline_slider_value_for_local_seconds

PLAY_SELECTION_EPSILON_SECONDS = 1e-6
PlaySelectionOutcome = Literal["continue", "restart", "stop"]


def timeline_play_selection_range(
    in_seconds: float | None,
    out_seconds: float | None,
    total_duration_seconds: float,
) -> tuple[float, float] | None:
    """Return a normalized valid In/Out range, or None when incomplete/empty."""

    if in_seconds is None or out_seconds is None:
        return None
    total = max(0.0, float(total_duration_seconds))
    first = max(0.0, min(total, float(in_seconds)))
    second = max(0.0, min(total, float(out_seconds)))
    start = min(first, second)
    end = max(first, second)
    if end - start <= PLAY_SELECTION_EPSILON_SECONDS:
        return None
    return start, end


def timeline_play_selection_should_stop(
    durations_seconds: tuple[float, ...],
    scene_index: int,
    local_seconds: float,
    out_seconds: float,
) -> bool:
    """Return True once the current global playhead reaches the selection Out point."""

    if not durations_seconds:
        return True
    current = timeline_marker_global_seconds(
        durations_seconds,
        scene_index,
        local_seconds,
    )
    return current >= float(out_seconds) - PLAY_SELECTION_EPSILON_SECONDS


def timeline_play_selection_outcome(
    *,
    playback_active: bool,
    reached_out: bool,
    loop_enabled: bool,
) -> PlaySelectionOutcome:
    """Resolve whether selection playback should continue, restart at In, or stop."""

    if not playback_active:
        return "stop"
    if not reached_out:
        return "continue"
    return "restart" if loop_enabled else "stop"


def timeline_timecode_seconds(text: str, fps: int | float) -> float | None:
    """Parse HH:MM:SS:FF timecode to seconds for selection playback monitoring."""

    parts = text.strip().split(":")
    if len(parts) != 4:
        return None
    try:
        hours, minutes, seconds, frames = (int(item) for item in parts)
    except ValueError:
        return None
    normalized_fps = max(1, int(round(float(fps))))
    if min(hours, minutes, seconds, frames) < 0:
        return None
    if minutes >= 60 or seconds >= 60 or frames >= normalized_fps:
        return None
    return hours * 3600.0 + minutes * 60.0 + seconds + frames / normalized_fps


def start_timeline_play_selection(
    root: Any,
    project: ProjectState,
    *,
    loop: bool = False,
) -> tuple[bool, str]:
    """Start native preview at session In and stop or loop when playback reaches Out."""

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QSlider

    if not project.scenes:
        return False, "Play Selection tidak tersedia karena project belum memiliki Scene."

    durations = tuple(max(0.0, float(scene.duration_seconds)) for scene in project.scenes)
    total_duration = sum(durations)
    owner: Any = root.window()
    selection = timeline_play_selection_range(
        getattr(owner, "_aavc_timeline_in_seconds", None),
        getattr(owner, "_aavc_timeline_out_seconds", None),
        total_duration,
    )
    if selection is None:
        mode_label = "Loop Selection" if loop else "Play Selection"
        return False, f"Setel In dan Out point yang berbeda terlebih dahulu sebelum {mode_label}."
    in_seconds, out_seconds = selection

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
        (
            button
            for button in root.findChildren(QPushButton)
            if button.text() in {"▶", "⏸"}
        ),
        None,
    )
    timecode_label = next(
        (
            label
            for label in root.findChildren(QLabel)
            if " / " in label.text() and label.text().count(":") >= 6
        ),
        None,
    )
    if scene_list is None or progress_slider is None or play_button is None:
        return False, "Kontrol preview tidak tersedia pada Editor aktif."

    previous_guard = getattr(root, "_aavc_play_selection_guard_timer", None)
    if previous_guard is not None:
        previous_guard.stop()
        previous_guard.deleteLater()
    reverse_timer = getattr(root, "_aavc_timeline_reverse_timer", None)
    if reverse_timer is not None:
        reverse_timer.stop()

    if play_button.text() == "⏸":
        play_button.click()

    def seek_to_global_seconds(global_seconds: float) -> bool:
        target = timeline_marker_seek_target(durations, global_seconds)
        if target is None:
            return False
        scene_index, local_seconds = target
        if play_button.text() == "⏸":
            play_button.click()
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
        return True

    if not seek_to_global_seconds(in_seconds):
        return False, "In point tidak dapat dipetakan ke Scene project."

    root._aavc_play_selection_active = True
    root._aavc_play_selection_loop = loop
    root._aavc_play_selection_range_seconds = selection
    root._aavc_play_selection_out_seconds = out_seconds
    play_button.click()
    if play_button.text() != "⏸":
        root._aavc_play_selection_active = False
        root._aavc_play_selection_loop = False
        return False, "Preview native gagal memulai Play Selection."

    fps = max(1, int(project.fps))
    native_interval = max(15, int(round(1000 / fps)))
    playback_timer = next(
        (
            timer
            for timer in root.findChildren(QTimer)
            if timer is not reverse_timer
            and timer.isActive()
            and timer.interval() == native_interval
        ),
        None,
    )

    guard = QTimer(root)
    guard.setInterval(max(8, native_interval // 2))
    root._aavc_play_selection_guard_timer = guard
    root._aavc_play_selection_native_timer = playback_timer

    def fallback_global_seconds() -> float:
        row = int(scene_list.currentRow())
        if row < 0 or row >= len(durations):
            return 0.0
        local = preview_scrub_seconds(
            progress_slider.value(),
            progress_slider.maximum(),
            durations[row],
        )
        return timeline_marker_global_seconds(durations, row, local)

    def current_global_seconds() -> float:
        if timecode_label is not None:
            current_text = timecode_label.text().split(" / ", 1)[0].strip()
            parsed = timeline_timecode_seconds(current_text, fps)
            if parsed is not None:
                return parsed
        return fallback_global_seconds()

    def deactivate_selection() -> None:
        guard.stop()
        root._aavc_play_selection_active = False
        root._aavc_play_selection_loop = False

    def finish_selection() -> None:
        deactivate_selection()
        native = getattr(root, "_aavc_play_selection_native_timer", None)
        if native is not None:
            native.stop()
        try:
            from PySide6.QtMultimedia import QMediaPlayer
        except ImportError:
            pass
        else:
            for player in root.findChildren(QMediaPlayer):
                player.pause()
        play_button.setText("▶")
        status_bar = owner.statusBar() if hasattr(owner, "statusBar") else None
        if status_bar is not None:
            status_bar.showMessage(
                f"Play Selection selesai pada Out {out_seconds:.3f} detik.",
                5000,
            )

    def restart_loop() -> bool:
        if not seek_to_global_seconds(in_seconds):
            deactivate_selection()
            return False
        play_button.click()
        if play_button.text() != "⏸":
            deactivate_selection()
            return False
        return True

    def guard_tick() -> None:
        playback_active = play_button.text() == "⏸"
        current = current_global_seconds() if playback_active else 0.0
        outcome = timeline_play_selection_outcome(
            playback_active=playback_active,
            reached_out=(
                current >= out_seconds - PLAY_SELECTION_EPSILON_SECONDS
                if playback_active
                else False
            ),
            loop_enabled=loop,
        )
        if outcome == "continue":
            return
        if outcome == "restart":
            if restart_loop():
                return
            status_bar = owner.statusBar() if hasattr(owner, "statusBar") else None
            if status_bar is not None:
                status_bar.showMessage(
                    "Loop Selection dihentikan karena In point tidak dapat diputar ulang.",
                    6000,
                )
            return
        if playback_active:
            finish_selection()
        else:
            deactivate_selection()

    guard.timeout.connect(guard_tick)
    guard.start()
    mode_label = "Loop Selection" if loop else "Play Selection"
    shortcut = "Ctrl+Shift+Space" if loop else "Ctrl+Space"
    return (
        True,
        f"{mode_label} {in_seconds:.3f}–{out_seconds:.3f} detik dimulai ({shortcut}).",
    )
