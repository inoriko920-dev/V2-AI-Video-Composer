from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal, cast

from aavc.animation.compiler import native_visual_effect_names
from aavc.animation.contract import track_requires_advanced
from aavc.domain.animation import (
    AnimationKeyframe,
    AnimationKeyframeTrack,
    KeyframeEasing,
    KeyframeInterpolation,
    TransformProperty,
)
from aavc.domain.project.models import AnimationAssignment, Scene

NATIVE_MOTION_CHOICES = native_visual_effect_names()


@dataclass(frozen=True, slots=True)
class AssetMotionDialogResult:
    action: Literal["apply", "remove"]
    asset_id: str
    assignment: AnimationAssignment | None = None


@dataclass(frozen=True, slots=True)
class KeyframePropertySpec:
    property_name: TransformProperty
    group: str
    label: str
    minimum: float
    maximum: float
    default: float
    step: float
    decimals: int
    display_scale: float = 1.0
    suffix: str = ""


KEYFRAME_PROPERTY_SPECS: tuple[KeyframePropertySpec, ...] = (
    KeyframePropertySpec("position_x", "Transform", "Position X", -0.10, 0.10, 0.0, 1.0, 2, 100.0, "%"),
    KeyframePropertySpec("position_y", "Transform", "Position Y", -0.10, 0.10, 0.0, 1.0, 2, 100.0, "%"),
    KeyframePropertySpec("scale", "Transform", "Scale", 0.75, 1.50, 1.0, 0.01, 2, 1.0, "x"),
    KeyframePropertySpec("rotation_degrees", "Transform", "Rotation", -30.0, 30.0, 0.0, 0.5, 2, 1.0, "°"),
    KeyframePropertySpec("opacity", "Visibility & Framing", "Opacity", 0.0, 1.0, 1.0, 1.0, 1, 100.0, "%"),
    KeyframePropertySpec("crop_left", "Visibility & Framing", "Crop Left", 0.0, 0.45, 0.0, 1.0, 1, 100.0, "%"),
    KeyframePropertySpec("crop_top", "Visibility & Framing", "Crop Top", 0.0, 0.45, 0.0, 1.0, 1, 100.0, "%"),
    KeyframePropertySpec("crop_right", "Visibility & Framing", "Crop Right", 0.0, 0.45, 0.0, 1.0, 1, 100.0, "%"),
    KeyframePropertySpec("crop_bottom", "Visibility & Framing", "Crop Bottom", 0.0, 0.45, 0.0, 1.0, 1, 100.0, "%"),
    KeyframePropertySpec("mask_progress", "Visibility & Framing", "Reveal / Mask Progress", 0.0, 1.0, 1.0, 1.0, 1, 100.0, "%"),
    KeyframePropertySpec("blur", "Effects", "Blur", 0.0, 1.0, 0.0, 1.0, 1, 100.0, "%"),
    KeyframePropertySpec("shadow", "Effects", "Shadow", 0.0, 1.0, 0.0, 1.0, 1, 100.0, "%"),
    KeyframePropertySpec("glow", "Effects", "Glow", 0.0, 1.0, 0.0, 1.0, 1, 100.0, "%"),
)
_PROPERTY_ORDER = {
    spec.property_name: index for index, spec in enumerate(KEYFRAME_PROPERTY_SPECS)
}


def keyframe_property_spec(property_name: str) -> KeyframePropertySpec:
    return next(
        spec
        for spec in KEYFRAME_PROPERTY_SPECS
        if spec.property_name == property_name
    )


def find_asset_motion_assignment(
    assignments: tuple[AnimationAssignment, ...],
    scene_number: int,
    asset_id: str,
) -> AnimationAssignment | None:
    return next(
        (
            item
            for item in assignments
            if item.scene_number == scene_number and item.asset_id == asset_id
        ),
        None,
    )


def build_asset_motion_assignment(
    *,
    scene_number: int,
    asset_id: str,
    enter_effect: str,
    exit_effect: str,
    intensity: float,
    locked: bool,
    existing_assignment: AnimationAssignment | None = None,
    keyframe_tracks: tuple[AnimationKeyframeTrack, ...] | None = None,
) -> AnimationAssignment:
    preserved_tracks = (
        keyframe_tracks
        if keyframe_tracks is not None
        else (
            existing_assignment.keyframe_tracks
            if existing_assignment is not None
            else ()
        )
    )
    return AnimationAssignment(
        scene_number=scene_number,
        asset_id=asset_id,
        enter_effect=enter_effect,
        exit_effect=exit_effect,
        intensity=intensity,
        locked=locked,
        keyframe_tracks=preserved_tracks,
    )


def _sorted_tracks(
    tracks: tuple[AnimationKeyframeTrack, ...],
) -> tuple[AnimationKeyframeTrack, ...]:
    return tuple(
        sorted(
            tracks,
            key=lambda track: _PROPERTY_ORDER.get(track.property_name, 999),
        )
    )


def show_asset_motion_dialog(
    parent: Any,
    scene: Scene,
    assignments: tuple[AnimationAssignment, ...],
    *,
    project_schema_version: int = 3,
) -> AssetMotionDialogResult | None:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    dialog = QDialog(parent)
    dialog.setWindowTitle(f"Animasi Aset — Scene {scene.scene_number:02d}")
    dialog.setModal(True)
    dialog.resize(980, 720)

    originals: dict[str, AnimationAssignment] = {}
    working: dict[str, AnimationAssignment] = {}
    for asset_id in scene.asset_ids:
        existing = find_asset_motion_assignment(
            assignments,
            scene.scene_number,
            asset_id,
        )
        baseline = existing or AnimationAssignment(
            scene_number=scene.scene_number,
            asset_id=asset_id,
        )
        originals[asset_id] = baseline
        working[asset_id] = baseline

    dirty_assets: set[str] = set()
    active_asset = [scene.asset_ids[0]]
    suppress = [False]

    root = QVBoxLayout(dialog)
    top = QHBoxLayout()
    top.addWidget(QLabel("Aset"))
    asset_combo = QComboBox()
    asset_combo.addItems(list(scene.asset_ids))
    top.addWidget(asset_combo, 1)
    contract_badge = QLabel(
        "Advanced v4" if project_schema_version >= 4 else "Legacy v3"
    )
    contract_badge.setStyleSheet(
        "font-weight:600; color:#2563EB; padding:4px 8px;"
        "border:1px solid #BFDBFE; border-radius:4px;"
    )
    top.addWidget(contract_badge)
    dirty_label = QLabel("")
    dirty_label.setStyleSheet("color:#D97706; font-size:9px;")
    top.addWidget(dirty_label)
    root.addLayout(top)

    tabs = QTabWidget()
    root.addWidget(tabs, 1)

    preset_tab = QWidget()
    preset_root = QVBoxLayout(preset_tab)
    intro = QLabel(
        "Preset tetap menjadi jalur pemula. Mengubah Preset tidak menghapus "
        "track Keyframe yang sudah tersimpan."
    )
    intro.setWordWrap(True)
    preset_root.addWidget(intro)
    preset_form = QFormLayout()
    enter_combo = QComboBox()
    enter_combo.addItems(list(NATIVE_MOTION_CHOICES))
    exit_combo = QComboBox()
    exit_combo.addItems(list(NATIVE_MOTION_CHOICES))
    intensity = QDoubleSpinBox()
    intensity.setRange(0.0, 2.0)
    intensity.setDecimals(2)
    intensity.setSingleStep(0.1)
    lock_checkbox = QCheckBox("Kunci dari Auto Motion")
    lock_checkbox.setToolTip(
        "Melindungi assignment dari Auto Motion/AI. Edit manual tetap diizinkan."
    )
    preset_form.addRow("Efek masuk", enter_combo)
    preset_form.addRow("Efek keluar", exit_combo)
    preset_form.addRow("Intensitas", intensity)
    preset_form.addRow("Proteksi", lock_checkbox)
    preset_root.addLayout(preset_form)
    preset_status = QLabel()
    preset_status.setWordWrap(True)
    preset_status.setStyleSheet("color:#64748B; font-size:9px;")
    preset_root.addWidget(preset_status)
    preset_root.addStretch(1)
    tabs.addTab(preset_tab, "Preset")

    keyframe_tab = QWidget()
    keyframe_root = QHBoxLayout(keyframe_tab)

    property_panel = QVBoxLayout()
    property_panel.addWidget(QLabel("Property"))
    property_list = QListWidget()
    property_panel.addWidget(property_list, 1)
    keyframe_root.addLayout(property_panel, 2)

    center_panel = QVBoxLayout()
    center_panel.addWidget(QLabel("Keyframe · waktu Scene 0–100%"))
    keyframe_list = QListWidget()
    center_panel.addWidget(keyframe_list, 1)
    nav = QHBoxLayout()
    add_keyframe = QPushButton("Add")
    delete_keyframe = QPushButton("Delete")
    previous_keyframe = QPushButton("Previous")
    next_keyframe = QPushButton("Next")
    nav.addWidget(add_keyframe)
    nav.addWidget(delete_keyframe)
    nav.addStretch(1)
    nav.addWidget(previous_keyframe)
    nav.addWidget(next_keyframe)
    center_panel.addLayout(nav)
    reset_track = QPushButton("Reset Track")
    center_panel.addWidget(reset_track)
    keyframe_root.addLayout(center_panel, 4)

    value_panel = QVBoxLayout()
    value_panel.addWidget(QLabel("Nilai & Segmen"))
    value_form = QFormLayout()
    time_spin = QDoubleSpinBox()
    time_spin.setRange(0.0, 1.0)
    time_spin.setDecimals(3)
    time_spin.setSingleStep(0.025)
    value_spin = QDoubleSpinBox()
    interpolation_combo = QComboBox()
    interpolation_combo.addItem("Hold", "hold")
    interpolation_combo.addItem("Linear", "linear")
    interpolation_combo.addItem("Bezier", "bezier")
    easing_combo = QComboBox()
    easing_combo.addItem("Linear", "linear")
    easing_combo.addItem("Ease In", "ease_in")
    easing_combo.addItem("Ease Out", "ease_out")
    easing_combo.addItem("Ease In-Out", "ease_in_out")
    velocity_spin = QDoubleSpinBox()
    velocity_spin.setRange(0.0, 4.0)
    velocity_spin.setDecimals(2)
    velocity_spin.setSingleStep(0.1)
    overshoot_spin = QDoubleSpinBox()
    overshoot_spin.setRange(0.0, 50.0)
    overshoot_spin.setDecimals(1)
    overshoot_spin.setSuffix("%")
    overshoot_spin.setSingleStep(1.0)
    value_form.addRow("Time", time_spin)
    value_form.addRow("Value", value_spin)
    value_form.addRow("Interpolation", interpolation_combo)
    value_form.addRow("Easing", easing_combo)
    value_form.addRow("Velocity", velocity_spin)
    value_form.addRow("Overshoot", overshoot_spin)
    value_panel.addLayout(value_form)
    segment_label = QLabel("Segmen ke keyframe berikutnya")
    segment_label.setWordWrap(True)
    value_panel.addWidget(segment_label)
    preview_truth = QLabel()
    preview_truth.setWordWrap(True)
    preview_truth.setStyleSheet("color:#475569; font-size:9px;")
    value_panel.addWidget(preview_truth)
    inline_status = QLabel()
    inline_status.setWordWrap(True)
    inline_status.setStyleSheet("color:#B45309; font-size:9px;")
    value_panel.addWidget(inline_status)
    value_panel.addStretch(1)
    keyframe_root.addLayout(value_panel, 3)
    tabs.addTab(keyframe_tab, "Keyframe")

    buttons = QHBoxLayout()
    remove_button = QPushButton("Hapus Animasi Aset")
    cancel_button = QPushButton("Batal")
    apply_button = QPushButton("Terapkan")
    apply_button.setDefault(True)
    buttons.addWidget(remove_button)
    buttons.addStretch(1)
    buttons.addWidget(cancel_button)
    buttons.addWidget(apply_button)
    root.addLayout(buttons)

    result: list[AssetMotionDialogResult] = []

    def current_assignment() -> AnimationAssignment:
        return working[active_asset[0]]

    def set_dirty() -> None:
        if suppress[0]:
            return
        dirty_assets.add(active_asset[0])
        dirty_label.setText("● perubahan lokal")

    def store_preset_controls() -> None:
        if suppress[0]:
            return
        current = current_assignment()
        updated = build_asset_motion_assignment(
            scene_number=scene.scene_number,
            asset_id=active_asset[0],
            enter_effect=enter_combo.currentText(),
            exit_effect=exit_combo.currentText(),
            intensity=float(intensity.value()),
            locked=lock_checkbox.isChecked(),
            existing_assignment=current,
        )
        if updated != current:
            working[active_asset[0]] = updated
            set_dirty()

    def selected_property_name() -> str | None:
        item = property_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def selected_track() -> AnimationKeyframeTrack | None:
        property_name = selected_property_name()
        if property_name is None:
            return None
        return next(
            (
                track
                for track in current_assignment().keyframe_tracks
                if track.property_name == property_name
            ),
            None,
        )

    def replace_track(track: AnimationKeyframeTrack | None) -> None:
        property_name = selected_property_name()
        if property_name is None:
            return
        assignment = current_assignment()
        tracks = tuple(
            item
            for item in assignment.keyframe_tracks
            if item.property_name != property_name
        )
        if track is not None:
            tracks += (track,)
        updated = replace(assignment, keyframe_tracks=_sorted_tracks(tracks))
        if updated != assignment:
            working[active_asset[0]] = updated
            set_dirty()

    def refresh_property_list() -> None:
        selected = selected_property_name()
        property_list.clear()
        by_name = {
            track.property_name: track
            for track in current_assignment().keyframe_tracks
        }
        for spec in KEYFRAME_PROPERTY_SPECS:
            track = by_name.get(spec.property_name)
            marker = "○"
            if track is not None:
                if track_requires_advanced(track):
                    marker = (
                        "● ADV"
                        if project_schema_version >= 4
                        else "● Dormant"
                    )
                else:
                    marker = "●"
            item = QListWidgetItem(
                f"{marker}  {spec.group} · {spec.label}"
            )
            item.setData(Qt.ItemDataRole.UserRole, spec.property_name)
            property_list.addItem(item)
            if spec.property_name == selected:
                property_list.setCurrentItem(item)
        if property_list.currentRow() < 0 and property_list.count():
            property_list.setCurrentRow(0)

    def refresh_keyframes(preferred_time: float | None = None) -> None:
        suppress[0] = True
        try:
            track = selected_track()
            keyframe_list.clear()
            if track is not None:
                spec = keyframe_property_spec(track.property_name)
                for keyframe in track.keyframes:
                    display_value = keyframe.value * spec.display_scale
                    item = QListWidgetItem(
                        f"{keyframe.time * 100:06.2f}%  ·  "
                        f"{display_value:.{spec.decimals}f}{spec.suffix}"
                    )
                    item.setData(Qt.ItemDataRole.UserRole, keyframe.time)
                    keyframe_list.addItem(item)
                if preferred_time is not None:
                    for index, keyframe in enumerate(track.keyframes):
                        if abs(keyframe.time - preferred_time) < 1e-9:
                            keyframe_list.setCurrentRow(index)
                            break
                if keyframe_list.currentRow() < 0:
                    keyframe_list.setCurrentRow(0)
        finally:
            suppress[0] = False
        refresh_editor_fields()

    def refresh_editor_fields() -> None:
        suppress[0] = True
        try:
            property_name = selected_property_name()
            track = selected_track()
            index = keyframe_list.currentRow()
            has_keyframe = (
                track is not None
                and 0 <= index < len(track.keyframes)
                and property_name is not None
            )
            for widget in (
                time_spin,
                value_spin,
                interpolation_combo,
                easing_combo,
                velocity_spin,
                overshoot_spin,
                delete_keyframe,
                previous_keyframe,
                next_keyframe,
            ):
                widget.setEnabled(has_keyframe)
            reset_track.setEnabled(track is not None)

            if not has_keyframe or track is None or property_name is None:
                inline_status.setText("Tambahkan keyframe untuk property ini.")
                preview_truth.setText("")
                segment_label.setText("Segmen ke keyframe berikutnya")
                return

            spec = keyframe_property_spec(property_name)
            keyframe = track.keyframes[index]
            value_spin.setRange(
                spec.minimum * spec.display_scale,
                spec.maximum * spec.display_scale,
            )
            value_spin.setDecimals(spec.decimals)
            value_spin.setSingleStep(spec.step)
            value_spin.setSuffix(spec.suffix)
            time_spin.setValue(keyframe.time)
            value_spin.setValue(keyframe.value * spec.display_scale)

            interpolation_index = interpolation_combo.findData(
                keyframe.interpolation
            )
            interpolation_combo.setCurrentIndex(max(0, interpolation_index))
            easing_index = easing_combo.findData(keyframe.easing)
            easing_combo.setCurrentIndex(max(0, easing_index))
            velocity_spin.setValue(
                1.0 if keyframe.velocity is None else keyframe.velocity
            )
            overshoot_spin.setValue(
                0.0
                if keyframe.overshoot is None
                else keyframe.overshoot * 100.0
            )

            has_outgoing = index < len(track.keyframes) - 1
            is_bezier = (
                has_outgoing
                and interpolation_combo.currentData() == "bezier"
            )
            interpolation_combo.setEnabled(has_outgoing)
            easing_combo.setEnabled(has_outgoing)
            velocity_spin.setEnabled(is_bezier)
            overshoot_spin.setEnabled(is_bezier)
            segment_label.setText(
                "Segmen ke keyframe berikutnya"
                if has_outgoing
                else "Keyframe terakhir · tidak memiliki segmen keluar"
            )

            heavy = property_name in {"blur", "shadow", "glow"}
            preview_truth.setText(
                "≈ Approx saat interaksi · FFmpeg tetap sumber kebenaran final."
                if heavy
                else "● Live · preview Qt memakai evaluator canonical."
            )
            if project_schema_version < 4 and track_requires_advanced(track):
                inline_status.setText(
                    "Dormant pada Legacy v3. Saat Apply, aplikasi akan meminta "
                    "konfirmasi sebelum mengaktifkan Advanced v4."
                )
            else:
                inline_status.setText("")
        finally:
            suppress[0] = False

    def update_selected_keyframe() -> None:
        if suppress[0]:
            return
        track = selected_track()
        index = keyframe_list.currentRow()
        property_name = selected_property_name()
        if (
            track is None
            or property_name is None
            or not 0 <= index < len(track.keyframes)
        ):
            return

        new_time = float(time_spin.value())
        if any(
            other_index != index
            and abs(other.time - new_time) < 1e-9
            for other_index, other in enumerate(track.keyframes)
        ):
            inline_status.setText("Time keyframe harus unik dalam satu track.")
            return

        interpolation = cast(
            KeyframeInterpolation,
            str(interpolation_combo.currentData()),
        )
        easing = cast(
            KeyframeEasing,
            str(easing_combo.currentData()),
        )
        has_outgoing = index < len(track.keyframes) - 1
        is_bezier = has_outgoing and interpolation == "bezier"
        spec = keyframe_property_spec(property_name)
        edited = AnimationKeyframe(
            time=new_time,
            value=float(value_spin.value()) / spec.display_scale,
            interpolation=interpolation,
            easing=easing,
            velocity=float(velocity_spin.value()) if is_bezier else None,
            overshoot=(
                float(overshoot_spin.value()) / 100.0
                if is_bezier
                else None
            ),
        )
        points = list(track.keyframes)
        points[index] = edited
        points.sort(key=lambda point: point.time)
        replace_track(
            AnimationKeyframeTrack(
                property_name=track.property_name,
                keyframes=tuple(points),
            )
        )
        refresh_property_list()
        refresh_keyframes(preferred_time=edited.time)

    def add_keyframe_for_property() -> None:
        property_name = selected_property_name()
        if property_name is None:
            return
        spec = keyframe_property_spec(property_name)
        track = selected_track()
        if track is None:
            new_time = 0.0
            points: list[AnimationKeyframe] = []
        else:
            points = list(track.keyframes)
            used = sorted(point.time for point in points)
            candidates = [0.0, 1.0]
            candidates.extend(
                (left + right) / 2.0
                for left, right in zip(used, used[1:], strict=False)
            )
            new_time = next(
                (
                    candidate
                    for candidate in candidates
                    if all(abs(candidate - value) > 1e-9 for value in used)
                ),
                None,
            )
            if new_time is None:
                inline_status.setText(
                    "Tidak ada slot waktu sederhana yang tersedia untuk Add."
                )
                return
        points.append(AnimationKeyframe(time=new_time, value=spec.default))
        points.sort(key=lambda point: point.time)
        replace_track(
            AnimationKeyframeTrack(
                property_name=spec.property_name,
                keyframes=tuple(points),
            )
        )
        refresh_property_list()
        refresh_keyframes(preferred_time=new_time)

    def delete_selected_keyframe() -> None:
        track = selected_track()
        index = keyframe_list.currentRow()
        if track is None or not 0 <= index < len(track.keyframes):
            return
        points = list(track.keyframes)
        del points[index]
        if points:
            replace_track(
                AnimationKeyframeTrack(
                    property_name=track.property_name,
                    keyframes=tuple(points),
                )
            )
        else:
            replace_track(None)
        refresh_property_list()
        refresh_keyframes()

    def reset_selected_track() -> None:
        if selected_track() is None:
            return
        replace_track(None)
        refresh_property_list()
        refresh_keyframes()

    def load_asset(asset_id: str) -> None:
        suppress[0] = True
        try:
            assignment = working[asset_id]
            enter_combo.setCurrentText(
                assignment.enter_effect
                if assignment.enter_effect in NATIVE_MOTION_CHOICES
                else "Rise"
            )
            exit_combo.setCurrentText(
                assignment.exit_effect
                if assignment.exit_effect in NATIVE_MOTION_CHOICES
                else "Drift"
            )
            intensity.setValue(max(0.0, min(2.0, assignment.intensity)))
            lock_checkbox.setChecked(assignment.locked)
            remove_button.setEnabled(
                find_asset_motion_assignment(
                    assignments,
                    scene.scene_number,
                    asset_id,
                )
                is not None
            )
            preset_status.setText(
                f"{assignment.enter_effect} → {assignment.exit_effect} · "
                f"{len(assignment.keyframe_tracks)} track Keyframe."
            )
            dirty_label.setText(
                "● perubahan lokal" if asset_id in dirty_assets else ""
            )
        finally:
            suppress[0] = False
        refresh_property_list()
        refresh_keyframes()

    def append_apply_result(asset_id: str) -> None:
        active_asset[0] = asset_id
        store_preset_controls()
        assignment = working[asset_id]
        result.append(
            AssetMotionDialogResult(
                action="apply",
                asset_id=asset_id,
                assignment=assignment,
            )
        )
        dialog.accept()

    def asset_changed(_index: int) -> None:
        if suppress[0]:
            return
        old_asset = active_asset[0]
        new_asset = asset_combo.currentText()
        if old_asset == new_asset:
            return
        if old_asset in dirty_assets:
            box = QMessageBox(dialog)
            box.setWindowTitle("Perubahan belum diterapkan")
            box.setText(
                f"Aset {old_asset} memiliki perubahan lokal. "
                "Terapkan, buang perubahan, atau batalkan perpindahan aset."
            )
            apply_now = box.addButton(
                "Terapkan",
                QMessageBox.ButtonRole.AcceptRole,
            )
            discard = box.addButton(
                "Buang Perubahan",
                QMessageBox.ButtonRole.DestructiveRole,
            )
            cancel = box.addButton(
                "Batal",
                QMessageBox.ButtonRole.RejectRole,
            )
            box.exec()
            clicked = box.clickedButton()
            if clicked is apply_now:
                append_apply_result(old_asset)
                return
            if clicked is discard:
                working[old_asset] = originals[old_asset]
                dirty_assets.discard(old_asset)
            else:
                assert clicked is cancel or clicked is None
                suppress[0] = True
                try:
                    asset_combo.setCurrentText(old_asset)
                finally:
                    suppress[0] = False
                return
        active_asset[0] = new_asset
        load_asset(new_asset)

    def apply_selection() -> None:
        append_apply_result(active_asset[0])

    def remove_selection() -> None:
        existing = find_asset_motion_assignment(
            assignments,
            scene.scene_number,
            active_asset[0],
        )
        if existing is None:
            return
        answer = QMessageBox.question(
            dialog,
            "Hapus Animasi Aset?",
            (
                f"Hapus seluruh Preset dan Keyframe untuk {active_asset[0]}? "
                "Aksi ini dapat di-Undo setelah diterapkan."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        result.append(
            AssetMotionDialogResult(
                action="remove",
                asset_id=active_asset[0],
            )
        )
        dialog.accept()

    def move_keyframe(step: int) -> None:
        count = keyframe_list.count()
        if not count:
            return
        target = max(0, min(count - 1, keyframe_list.currentRow() + step))
        keyframe_list.setCurrentRow(target)

    asset_combo.currentIndexChanged.connect(asset_changed)
    enter_combo.currentIndexChanged.connect(lambda _index: store_preset_controls())
    exit_combo.currentIndexChanged.connect(lambda _index: store_preset_controls())
    intensity.valueChanged.connect(lambda _value: store_preset_controls())
    lock_checkbox.toggled.connect(lambda _checked: store_preset_controls())
    property_list.currentItemChanged.connect(
        lambda _current, _previous: refresh_keyframes()
    )
    keyframe_list.currentRowChanged.connect(lambda _row: refresh_editor_fields())
    add_keyframe.clicked.connect(add_keyframe_for_property)
    delete_keyframe.clicked.connect(delete_selected_keyframe)
    reset_track.clicked.connect(reset_selected_track)
    previous_keyframe.clicked.connect(lambda: move_keyframe(-1))
    next_keyframe.clicked.connect(lambda: move_keyframe(1))
    time_spin.valueChanged.connect(lambda _value: update_selected_keyframe())
    value_spin.valueChanged.connect(lambda _value: update_selected_keyframe())
    interpolation_combo.currentIndexChanged.connect(
        lambda _index: update_selected_keyframe()
    )
    easing_combo.currentIndexChanged.connect(
        lambda _index: update_selected_keyframe()
    )
    velocity_spin.valueChanged.connect(lambda _value: update_selected_keyframe())
    overshoot_spin.valueChanged.connect(lambda _value: update_selected_keyframe())
    apply_button.clicked.connect(apply_selection)
    remove_button.clicked.connect(remove_selection)
    cancel_button.clicked.connect(dialog.reject)

    load_asset(active_asset[0])

    if dialog.exec() != QDialog.DialogCode.Accepted or not result:
        return None
    return result[0]
