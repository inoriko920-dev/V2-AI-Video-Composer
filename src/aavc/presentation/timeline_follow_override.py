from __future__ import annotations

from typing import Any

DEFAULT_TIMELINE_FOLLOW_MANUAL_OVERRIDE = False
TIMELINE_FOLLOW_MANUAL_OVERRIDE_PROPERTY = "aavcTimelineFollowManualOverride"
TIMELINE_FOLLOW_OVERRIDE_INSTALLED_PROPERTY = "aavcManualFollowOverrideInstalled"


def normalize_timeline_follow_manual_override(value: object) -> bool:
    """Normalize the session-only manual-scroll override flag."""

    if value is None:
        return DEFAULT_TIMELINE_FOLLOW_MANUAL_OVERRIDE
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
    return DEFAULT_TIMELINE_FOLLOW_MANUAL_OVERRIDE


def timeline_follow_may_scroll(
    *,
    requested_follow: bool,
    follow_enabled: bool,
    manual_override: object,
) -> bool:
    """Return whether Follow Playhead may move the viewport for this update."""

    return (
        bool(requested_follow)
        and bool(follow_enabled)
        and not normalize_timeline_follow_manual_override(manual_override)
    )


def timeline_follow_button_text(
    *,
    follow_enabled: bool,
    manual_override: object,
) -> str:
    """Return the compact header label for the effective Follow state."""

    if not follow_enabled:
        return "Follow OFF"
    if normalize_timeline_follow_manual_override(manual_override):
        return "Follow PAUSE"
    return "Follow ON"


def install_timeline_manual_follow_override(root: Any) -> bool:
    """Pause Follow Playhead after manual scrollbar input until playback restarts."""

    from PySide6.QtCore import QAbstractAnimation, QTimer
    from PySide6.QtWidgets import QPushButton, QScrollArea

    from aavc.presentation.timeline_zoom_scroll import (
        TIMELINE_FOLLOW_PLAYHEAD_PROPERTY,
        normalize_timeline_follow_playhead,
    )

    scroll = root.findChild(QScrollArea, "TimelineSceneScrollArea")
    follow_button = root.findChild(QPushButton, "TimelineFollowPlayhead")
    if scroll is None or follow_button is None:
        return False

    bar = scroll.horizontalScrollBar()
    owner: Any = scroll.window()
    override = normalize_timeline_follow_manual_override(
        owner.property(TIMELINE_FOLLOW_MANUAL_OVERRIDE_PROPERTY)
    )
    owner.setProperty(TIMELINE_FOLLOW_MANUAL_OVERRIDE_PROPERTY, override)

    def follow_enabled() -> bool:
        return normalize_timeline_follow_playhead(
            owner.property(TIMELINE_FOLLOW_PLAYHEAD_PROPERTY)
        )

    def refresh_button() -> None:
        follow_button.setText(
            timeline_follow_button_text(
                follow_enabled=follow_enabled(),
                manual_override=owner.property(
                    TIMELINE_FOLLOW_MANUAL_OVERRIDE_PROPERTY
                ),
            )
        )

    follow_animation = getattr(root, "_aavc_timeline_follow_animation", None)

    def set_override(active: bool, *, announce: bool) -> None:
        normalized = bool(active) and follow_enabled()
        previous = normalize_timeline_follow_manual_override(
            owner.property(TIMELINE_FOLLOW_MANUAL_OVERRIDE_PROPERTY)
        )
        owner.setProperty(TIMELINE_FOLLOW_MANUAL_OVERRIDE_PROPERTY, normalized)
        if normalized and follow_animation is not None:
            follow_animation.stop()
        refresh_button()
        if announce and normalized != previous:
            status_bar = owner.statusBar() if hasattr(owner, "statusBar") else None
            if status_bar is not None:
                if normalized:
                    status_bar.showMessage(
                        "Follow Playhead dijeda sementara karena timeline digeser manual. "
                        "Tekan Play lagi untuk melanjutkan Follow.",
                        6000,
                    )
                else:
                    status_bar.showMessage("Follow Playhead aktif kembali.", 3500)

    root._aavc_timeline_set_manual_follow_override = set_override

    def mark_manual_override(*_args: Any) -> None:
        if follow_enabled():
            set_override(True, announce=True)

    if not bool(bar.property(TIMELINE_FOLLOW_OVERRIDE_INSTALLED_PROPERTY)):
        bar.sliderPressed.connect(mark_manual_override)
        bar.actionTriggered.connect(mark_manual_override)
        bar.setProperty(TIMELINE_FOLLOW_OVERRIDE_INSTALLED_PROPERTY, True)

    if follow_animation is not None:
        def guard_follow_animation(
            new_state: QAbstractAnimation.State,
            _old_state: QAbstractAnimation.State,
        ) -> None:
            if (
                new_state == QAbstractAnimation.State.Running
                and normalize_timeline_follow_manual_override(
                    owner.property(TIMELINE_FOLLOW_MANUAL_OVERRIDE_PROPERTY)
                )
            ):
                follow_animation.stop()

        follow_animation.stateChanged.connect(guard_follow_animation)
        root._aavc_timeline_follow_override_animation_guard = guard_follow_animation

    follow_button.pressed.connect(lambda: set_override(False, announce=False))
    follow_button.toggled.connect(lambda _checked: refresh_button())

    play_button = next(
        (
            button
            for button in root.findChildren(QPushButton)
            if button.text() in {"▶", "⏸"}
            and "Putar preview kontinu" in button.toolTip()
        ),
        None,
    )
    if play_button is not None:
        def reset_after_playback_start(_checked: bool = False) -> None:
            def finish_reset() -> None:
                if play_button.text() == "⏸":
                    set_override(False, announce=True)

            QTimer.singleShot(0, finish_reset)

        play_button.clicked.connect(reset_after_playback_start)
        root._aavc_timeline_follow_override_play_button = play_button
        root._aavc_timeline_follow_override_play_slot = reset_after_playback_start

    refresh_button()
    return True
