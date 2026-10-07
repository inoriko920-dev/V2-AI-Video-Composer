from __future__ import annotations

from typing import Any

from aavc.application.commands import (
    AdvancedAnimationActivationRequired,
    ApplyAnimationKeyframeEdit,
    RandomizeAnimationAssignments,
    RemoveAnimationAssignment,
    SetProjectTitle,
)
from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.dialogs.asset_motion import (
    NATIVE_MOTION_CHOICES,
    show_asset_motion_dialog,
)
from aavc.presentation.windows.guarded_main_window import GuardedMainWindow


def _stored_animation_seed(metadata: dict[str, str]) -> int:
    raw = metadata.get("animation_seed", "1")
    try:
        value = int(raw)
    except ValueError:
        return 1
    return max(-2147483647, min(2147483647, value))


def legacy_asset_motion_edit_action_enabled(*, has_canonical_editor: bool) -> bool:
    """Keep the legacy Edit-menu action only for windows without the canonical editor."""

    return not has_canonical_editor


class NativeMotionMainWindow(GuardedMainWindow):
    """Guarded editor shell with render-backed asset animation controls."""

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        edit_menu: Any | None = None
        project_menu: Any | None = None
        animation_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "Edit":
                edit_menu = menu_action.menu()
            elif menu_action.text() == "Proyek":
                project_menu = menu_action.menu()
            elif menu_action.text() == "Animasi":
                animation_menu = menu_action.menu()

        if project_menu is not None:
            rename_action = action_type("Ubah Nama Proyek…", self.window)
            rename_action.triggered.connect(
                lambda _checked=False: self.rename_active_project()
            )
            project_menu.addAction(rename_action)

        if animation_menu is not None:
            auto_scene_action = action_type(
                "Auto Motion Scene Terpilih…",
                self.window,
            )
            auto_scene_action.triggered.connect(
                lambda _checked=False: self.randomize_native_motion(selected_only=True)
            )
            animation_menu.addAction(auto_scene_action)

            auto_all_action = action_type(
                "Auto Motion Semua Scene…",
                self.window,
            )
            auto_all_action.triggered.connect(
                lambda _checked=False: self.randomize_native_motion(selected_only=False)
            )
            animation_menu.addAction(auto_all_action)

        if edit_menu is None:
            return
        if not legacy_asset_motion_edit_action_enabled(
            has_canonical_editor=callable(
                getattr(self, "edit_selected_scene_asset_motion", None)
            )
        ):
            return

        edit_menu.addSeparator()
        motion_action = action_type("Animasi Aset…", self.window)
        motion_action.triggered.connect(
            lambda _checked=False: self.open_asset_motion_editor()
        )
        edit_menu.addAction(motion_action)

    def rename_active_project(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Ubah Nama Proyek tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        title, accepted = QInputDialog.getText(
            self.window,
            "Ubah Nama Proyek",
            "Nama proyek baru:\nNama file .aavcproj tidak akan berubah.",
            text=project.title,
        )
        if not accepted:
            return

        normalized = title.strip()
        if normalized == project.title:
            self.window.statusBar().showMessage("Nama proyek tidak berubah.", 4000)
            return

        try:
            session.execute(SetProjectTitle(title))
        except ValueError as error:
            self._show_project_error("Gagal mengubah nama proyek", error)
            return

        self._refresh_window_title()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            "Nama proyek diperbarui. Path file tetap sama; klik Simpan untuk menyimpan "
            "perubahan atau gunakan Simpan Sebagai untuk mengganti nama file.",
            8000,
        )

    def randomize_native_motion(self, *, selected_only: bool) -> None:
        from PySide6.QtWidgets import QInputDialog

        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Auto Motion tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        scene_numbers: tuple[int, ...] | None = None
        scope_label = "semua Scene"
        if selected_only:
            scene_number = self._selected_scene_number
            if scene_number is None:
                self.window.statusBar().showMessage(
                    "Pilih Scene terlebih dahulu sebelum menjalankan Auto Motion.",
                    5000,
                )
                return
            scene_numbers = (scene_number,)
            scope_label = f"Scene {scene_number:02d}"

        seed, accepted = QInputDialog.getInt(
            self.window,
            "Auto Motion",
            (
                f"Acak animasi native untuk {scope_label}.\n"
                f"Efek yang digunakan: {', '.join(NATIVE_MOTION_CHOICES)}.\n"
                "Seed yang sama menghasilkan pola yang sama:"
            ),
            value=_stored_animation_seed(project.metadata),
            minValue=-2147483647,
            maxValue=2147483647,
            step=1,
        )
        if not accepted:
            return

        try:
            session.execute(
                RandomizeAnimationAssignments(
                    seed=seed,
                    scene_numbers=scene_numbers,
                    effect_pool=NATIVE_MOTION_CHOICES,
                )
            )
        except ValueError as error:
            self._show_project_error("Auto Motion gagal", error)
            return

        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(
            f"Auto Motion diterapkan ke {scope_label} dengan seed {seed}. "
            "Gunakan Undo untuk membatalkan atau klik Simpan untuk menyimpan perubahan.",
            8000,
        )

    def _confirm_advanced_animation_activation(
        self,
        error: AdvancedAnimationActivationRequired,
    ) -> tuple[bool, bool]:
        from PySide6.QtWidgets import QCheckBox, QMessageBox

        box = QMessageBox(self.window)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Aktifkan Advanced Animation?")
        changed = ", ".join(error.changed_properties)
        message = (
            "Edit ini membutuhkan schema v4 / advanced-v1. "
            "Project yang sudah disimpan sebagai v4 tidak dapat dibuka oleh v0.2.0. "
            "Pada overwrite v3→v4 pertama, aplikasi membuat backup "
            ".pre-schema-v4.bak.\n\n"
            f"Property yang akan diaktifkan: {changed}."
        )
        if error.dormant_locations:
            message += (
                f"\nDitemukan {len(error.dormant_locations)} track advanced dormant "
                "di project yang ikut menjadi aktif setelah aktivasi."
            )
        box.setText(message)
        acknowledge: QCheckBox | None = None
        if error.requires_dormant_acknowledgement:
            acknowledge = QCheckBox(
                "Saya memahami track advanced dormant lain juga akan menjadi aktif."
            )
            box.setCheckBox(acknowledge)
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        yes_button = box.button(QMessageBox.StandardButton.Yes)
        if yes_button is not None:
            yes_button.setText("Aktifkan & Terapkan")

        if box.exec() != QMessageBox.StandardButton.Yes:
            return False, False
        if acknowledge is not None and not acknowledge.isChecked():
            self._show_project_notice(
                "Aktivasi belum diterapkan",
                "Centang konfirmasi track dormant sebelum mengaktifkan Advanced Animation.",
            )
            return False, False
        return True, acknowledge.isChecked() if acknowledge is not None else True

    def open_asset_motion_editor(self) -> None:
        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Animasi Aset tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            return

        scene_number = self._selected_scene_number
        if scene_number is None:
            self.window.statusBar().showMessage(
                "Pilih Scene terlebih dahulu sebelum mengatur animasi aset.",
                5000,
            )
            return

        scene = next(
            (item for item in project.scenes if item.scene_number == scene_number),
            None,
        )
        if scene is None:
            self.window.statusBar().showMessage(
                f"Scene {scene_number} tidak ditemukan.",
                5000,
            )
            return

        result = show_asset_motion_dialog(
            self.window,
            scene,
            project.animations,
            project_schema_version=project.schema_version,
        )
        if result is None:
            return

        try:
            if result.action == "apply":
                if result.assignment is None:
                    raise ValueError("Assignment animasi tidak tersedia")
                was_legacy = project.schema_version < 4
                try:
                    changed = session.execute(
                        ApplyAnimationKeyframeEdit(result.assignment)
                    )
                except AdvancedAnimationActivationRequired as activation:
                    confirmed, acknowledged = (
                        self._confirm_advanced_animation_activation(activation)
                    )
                    if not confirmed:
                        return
                    changed = session.execute(
                        ApplyAnimationKeyframeEdit(
                            result.assignment,
                            activate_advanced=True,
                            acknowledge_dormant=acknowledged,
                        )
                    )
                promoted = was_legacy and changed.schema_version >= 4
                promotion_text = (
                    " Advanced Animation v4 telah diaktifkan."
                    if promoted
                    else ""
                )
                message = (
                    f"Animasi {result.asset_id} diterapkan pada Scene {scene_number:02d}."
                    f"{promotion_text} Klik Simpan untuk menyimpan perubahan."
                )
            else:
                session.execute(
                    RemoveAnimationAssignment(scene_number, result.asset_id)
                )
                message = (
                    f"Animasi {result.asset_id} dihapus dari Scene {scene_number:02d}. "
                    "Klik Simpan untuk menyimpan perubahan."
                )
        except ValueError as error:
            self._show_project_error("Gagal mengubah animasi aset", error)
            return

        self._selected_scene_number = scene_number
        self._refresh_window_title()
        self._refresh_validation_badge()
        self.refresh_editor_overview()
        self.window.statusBar().showMessage(message, 7000)


def create_native_motion_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> NativeMotionMainWindow:
    return NativeMotionMainWindow(services, initial_state=initial_state)
