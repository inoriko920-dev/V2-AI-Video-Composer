from __future__ import annotations

from typing import Any, Literal

TimelineMagnetTargetKind = Literal["marker", "scene", "playhead"]

TIMELINE_MAGNET_ENABLED_PROPERTY = "aavcTimelineMagnetEnabled"
TIMELINE_MAGNET_MARKER_PROPERTY = "aavcTimelineSnapMarkerEnabled"
TIMELINE_MAGNET_SCENE_PROPERTY = "aavcTimelineSnapSceneEnabled"
TIMELINE_MAGNET_PLAYHEAD_PROPERTY = "aavcTimelineSnapPlayheadEnabled"
TIMELINE_MAGNET_TOLERANCE_PROPERTY = "aavcTimelineSnapTolerancePx"
TIMELINE_MAGNET_BUTTON_OBJECT_NAME = "TimelineMagnetToggle"
TIMELINE_SNAP_SETTINGS_BUTTON_OBJECT_NAME = "TimelineSnapSettings"
TIMELINE_MAGNET_TOLERANCE_OPTIONS_PX = (4, 8, 12, 16)
DEFAULT_TIMELINE_MAGNET_TOLERANCE_PX = 8

_TARGET_PROPERTIES: dict[TimelineMagnetTargetKind, str] = {
    "marker": TIMELINE_MAGNET_MARKER_PROPERTY,
    "scene": TIMELINE_MAGNET_SCENE_PROPERTY,
    "playhead": TIMELINE_MAGNET_PLAYHEAD_PROPERTY,
}

_runtime_magnet_enabled = True
_runtime_magnet_bypass = False
_runtime_magnet_tolerance_px = DEFAULT_TIMELINE_MAGNET_TOLERANCE_PX
_runtime_target_enabled: dict[TimelineMagnetTargetKind, bool] = {
    "marker": True,
    "scene": True,
    "playhead": True,
}


def normalize_timeline_magnet_enabled(value: object | None) -> bool:
    """Normalize a session property value; unset means enabled by default."""

    if value is None:
        return True
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
    return bool(value)


def normalize_timeline_magnet_tolerance_px(value: object | None) -> int:
    """Normalize Snap Strength to the nearest supported pixel radius."""

    if value is None or not isinstance(value, (int, float, str)):
        return DEFAULT_TIMELINE_MAGNET_TOLERANCE_PX
    try:
        raw = int(round(float(value)))
    except ValueError:
        return DEFAULT_TIMELINE_MAGNET_TOLERANCE_PX
    return min(
        TIMELINE_MAGNET_TOLERANCE_OPTIONS_PX,
        key=lambda candidate: (abs(candidate - raw), candidate),
    )


def timeline_magnet_active(enabled: bool, *, alt_bypass: bool = False) -> bool:
    """Return whether magnetic snapping should apply for the current gesture."""

    return bool(enabled) and not bool(alt_bypass)


def set_timeline_magnet_runtime_enabled(enabled: bool) -> None:
    global _runtime_magnet_enabled
    _runtime_magnet_enabled = bool(enabled)


def set_timeline_magnet_runtime_bypass(bypass: bool) -> None:
    global _runtime_magnet_bypass
    _runtime_magnet_bypass = bool(bypass)


def set_timeline_magnet_runtime_tolerance_px(value: int | float) -> None:
    global _runtime_magnet_tolerance_px
    _runtime_magnet_tolerance_px = normalize_timeline_magnet_tolerance_px(value)


def timeline_magnet_runtime_tolerance_px() -> int:
    return int(_runtime_magnet_tolerance_px)


def set_timeline_magnet_runtime_target_enabled(
    kind: TimelineMagnetTargetKind,
    enabled: bool,
) -> None:
    _runtime_target_enabled[kind] = bool(enabled)


def timeline_magnet_runtime_target_enabled(kind: TimelineMagnetTargetKind) -> bool:
    return bool(_runtime_target_enabled[kind])


def timeline_magnet_runtime_active(*, alt_bypass: bool | None = None) -> bool:
    """Return process runtime Magnet state, including Alt/transient bypass."""

    bypass = _runtime_magnet_bypass
    if alt_bypass is None:
        try:
            from PySide6.QtCore import Qt
            from PySide6.QtWidgets import QApplication

            alt_bypass = bool(
                QApplication.keyboardModifiers() & Qt.KeyboardModifier.AltModifier
            )
        except (ImportError, RuntimeError):
            alt_bypass = False
    return timeline_magnet_active(
        _runtime_magnet_enabled,
        alt_bypass=bypass or bool(alt_bypass),
    )


def timeline_magnet_enabled(owner: Any) -> bool:
    """Read the session-only Magnet master state from the owning window."""

    return normalize_timeline_magnet_enabled(
        owner.property(TIMELINE_MAGNET_ENABLED_PROPERTY)
    )


def timeline_magnet_target_enabled(
    owner: Any,
    kind: TimelineMagnetTargetKind,
) -> bool:
    """Read one session-only target state; every target defaults to enabled."""

    return normalize_timeline_magnet_enabled(owner.property(_TARGET_PROPERTIES[kind]))


def timeline_magnet_tolerance_px(owner: Any) -> int:
    """Read the session-only Snap Strength pixel radius from the owning window."""

    return normalize_timeline_magnet_tolerance_px(
        owner.property(TIMELINE_MAGNET_TOLERANCE_PROPERTY)
    )


def timeline_magnet_active_for_owner(
    owner: Any,
    *,
    alt_bypass: bool = False,
) -> bool:
    return timeline_magnet_active(
        timeline_magnet_enabled(owner),
        alt_bypass=alt_bypass,
    )


def install_timeline_magnet_control(root: Any) -> bool:
    """Install the session-only Magnet master switch and per-target Snap menu."""

    from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut
    from PySide6.QtWidgets import QMenu, QSpinBox, QToolButton

    zoom_box = root.findChild(QSpinBox, "TimelineZoomPercent")
    if zoom_box is None:
        return False
    timeline = zoom_box.parentWidget()
    if timeline is None or timeline.layout() is None:
        return False

    owner: Any = timeline.window()
    enabled = timeline_magnet_enabled(owner)
    owner.setProperty(TIMELINE_MAGNET_ENABLED_PROPERTY, enabled)
    set_timeline_magnet_runtime_enabled(enabled)

    tolerance_px = timeline_magnet_tolerance_px(owner)
    owner.setProperty(TIMELINE_MAGNET_TOLERANCE_PROPERTY, tolerance_px)
    set_timeline_magnet_runtime_tolerance_px(tolerance_px)

    target_states: dict[TimelineMagnetTargetKind, bool] = {}
    for kind, property_name in _TARGET_PROPERTIES.items():
        target_enabled = timeline_magnet_target_enabled(owner, kind)
        owner.setProperty(property_name, target_enabled)
        set_timeline_magnet_runtime_target_enabled(kind, target_enabled)
        target_states[kind] = target_enabled

    header_layout = timeline.layout().itemAt(0).layout() if timeline.layout().count() else None
    if header_layout is None:
        return False

    def hide_snap_guide() -> None:
        from aavc.presentation.timeline_snap_guide import hide_timeline_snap_guide

        hide_timeline_snap_guide(root)

    def status(message: str) -> None:
        status_bar = owner.statusBar() if hasattr(owner, "statusBar") else None
        if status_bar is not None:
            status_bar.showMessage(message, 4500)

    existing_magnet = root.findChild(QToolButton, TIMELINE_MAGNET_BUTTON_OBJECT_NAME)
    existing_settings = root.findChild(
        QToolButton,
        TIMELINE_SNAP_SETTINGS_BUTTON_OBJECT_NAME,
    )
    if existing_magnet is not None and existing_settings is not None:
        existing_magnet.setChecked(enabled)
        return True

    magnet_button = QToolButton(timeline)
    magnet_button.setObjectName(TIMELINE_MAGNET_BUTTON_OBJECT_NAME)
    magnet_button.setCheckable(True)
    magnet_button.setChecked(enabled)
    magnet_button.setToolTip(
        "Master magnetic snapping timeline. Matikan untuk edit bebas; tahan Alt untuk bypass sementara."
    )

    def apply_master_state(checked: bool, *, announce: bool) -> None:
        owner.setProperty(TIMELINE_MAGNET_ENABLED_PROPERTY, bool(checked))
        set_timeline_magnet_runtime_enabled(bool(checked))
        magnet_button.setText("Magnet ON" if checked else "Magnet OFF")
        magnet_button.setStyleSheet(
            "QToolButton { padding: 2px 7px; font-size: 9px; }"
            "QToolButton:checked { color: #1D4ED8; font-weight: 600; }"
        )
        if not checked:
            hide_snap_guide()
        if announce:
            state = "aktif" if checked else "nonaktif"
            status(
                f"Magnet timeline {state}. Tahan Alt untuk bypass sementara saat Magnet aktif."
            )

    magnet_button.toggled.connect(
        lambda checked: apply_master_state(bool(checked), announce=True)
    )
    apply_master_state(enabled, announce=False)

    settings_button = QToolButton(timeline)
    settings_button.setObjectName(TIMELINE_SNAP_SETTINGS_BUTTON_OBJECT_NAME)
    settings_button.setText("Snap ▾")
    settings_button.setToolTip(
        "Pilih target magnetic snapping dan kekuatan/toleransi magnet."
    )
    settings_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    settings_button.setStyleSheet("QToolButton { padding: 2px 7px; font-size: 9px; }")
    settings_menu = QMenu(settings_button)
    settings_button.setMenu(settings_menu)

    target_labels: dict[TimelineMagnetTargetKind, str] = {
        "marker": "Marker / In-Out",
        "scene": "Scene Edge",
        "playhead": "Playhead",
    }

    def apply_target_state(
        kind: TimelineMagnetTargetKind,
        checked: bool,
        *,
        announce: bool,
    ) -> None:
        owner.setProperty(_TARGET_PROPERTIES[kind], bool(checked))
        set_timeline_magnet_runtime_target_enabled(kind, bool(checked))
        if not checked:
            hide_snap_guide()
        if announce:
            state = "ON" if checked else "OFF"
            status(f"Snap target {target_labels[kind]}: {state}.")

    target_actions: dict[TimelineMagnetTargetKind, QAction] = {}
    for kind in ("marker", "scene", "playhead"):
        action = QAction(target_labels[kind], settings_menu)
        action.setCheckable(True)
        action.setChecked(target_states[kind])
        action.toggled.connect(
            lambda checked, active_kind=kind: apply_target_state(
                active_kind,
                bool(checked),
                announce=True,
            )
        )
        settings_menu.addAction(action)
        target_actions[kind] = action
        apply_target_state(kind, target_states[kind], announce=False)

    settings_menu.addSeparator()
    strength_menu = settings_menu.addMenu("Snap Strength")
    strength_group = QActionGroup(strength_menu)
    strength_group.setExclusive(True)
    strength_actions: dict[int, QAction] = {}

    def apply_tolerance(value: int, *, announce: bool) -> None:
        normalized = normalize_timeline_magnet_tolerance_px(value)
        owner.setProperty(TIMELINE_MAGNET_TOLERANCE_PROPERTY, normalized)
        set_timeline_magnet_runtime_tolerance_px(normalized)
        hide_snap_guide()
        if announce:
            status(f"Snap Strength: {normalized} px.")

    for value in TIMELINE_MAGNET_TOLERANCE_OPTIONS_PX:
        action = QAction(f"{value} px", strength_menu)
        action.setCheckable(True)
        action.setChecked(value == tolerance_px)
        strength_group.addAction(action)
        strength_menu.addAction(action)
        action.triggered.connect(
            lambda checked, active_value=value: (
                apply_tolerance(active_value, announce=True) if checked else None
            )
        )
        strength_actions[value] = action
    apply_tolerance(tolerance_px, announce=False)

    insert_at = max(0, header_layout.count() - 2)
    header_layout.insertWidget(insert_at, magnet_button)
    header_layout.insertWidget(insert_at + 1, settings_button)
    root._aavc_timeline_magnet_button = magnet_button
    root._aavc_timeline_snap_settings_button = settings_button
    root._aavc_timeline_snap_target_actions = target_actions
    root._aavc_timeline_snap_strength_actions = strength_actions
    root._aavc_timeline_snap_strength_group = strength_group

    def split_without_magnet() -> None:
        split_action = next(
            (
                action
                for action in owner.findChildren(QAction)
                if action.text() == "Split Scene di Playhead"
            ),
            None,
        )
        if split_action is None:
            return
        set_timeline_magnet_runtime_bypass(True)
        try:
            split_action.trigger()
        finally:
            set_timeline_magnet_runtime_bypass(False)

    bypass_shortcut = QShortcut(QKeySequence("Ctrl+Alt+B"), root)
    bypass_shortcut.activated.connect(split_without_magnet)
    root._aavc_timeline_split_without_magnet_shortcut = bypass_shortcut
    return True
