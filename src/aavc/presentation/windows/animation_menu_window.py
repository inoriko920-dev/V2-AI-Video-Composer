from __future__ import annotations

from typing import Any, Literal

from aavc.application.commands import (
    RandomizeAnimationAssignments,
    RemoveAnimationAssignment,
    SetAnimationAssignment,
)
from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.dialogs.asset_motion import (
    NATIVE_MOTION_CHOICES,
    show_asset_motion_dialog,
)
from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.project_menu_window import ProjectMenuMainWindow

ANIMATION_MODE_ITEMS = ("Auto (AI)", "Random App", "Manual")
AnimationModeAction = Literal["ai_unavailable", "auto_motion_all", "manual_asset"]


def animation_menu_enabled(*, has_project: bool, has_selected_scene: bool) -> bool:
    """Return whether selected-scene animation actions may be used."""

    return has_project and has_selected_scene


def auto_motion_all_enabled(*, has_project: bool) -> bool:
    """Return whether project-wide Auto Motion may be used."""

    return has_project


def animation_mode_enabled(*, has_project: bool) -> bool:
    """Return whether the toolbar animation-mode selector may be used."""

    return has_project


def animation_mode_action(mode: str) -> AnimationModeAction | None:
    """Map the existing toolbar mode labels to live runtime workflows."""

    if mode == "Auto (AI)":
        return "ai_unavailable"
    if mode == "Random App":
        return "auto_motion_all"
    if mode == "Manual":
        return "manual_asset"
    return None


def stored_animation_seed(metadata: dict[str, str]) -> int:
    """Return a Qt-safe deterministic Auto Motion seed from project metadata."""

    raw = metadata.get("animation_seed", "1")
    try:
        value = int(raw)
    except ValueError:
        return 1
    return max(-2147483647, min(2147483647, value))


class AnimationMenuMainWindow(ProjectMenuMainWindow):
    """Expose render-backed asset motion through the current runtime shell."""

    def __init__(
        self,
        services: FoundationServices,
        initial_state: str = "UI-002",
    ) -> None:
        self._asset_motion_action: Any | None = None
        self._auto_motion_scene_action: Any | None = None
        self._auto_motion_all_action: Any | None = None
        self._animation_mode_combo: Any | None = None
        super().__init__(services, initial_state=initial_state)

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        animation_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "Animasi":
                animation_menu = menu_action.menu()
                break
        if animation_menu is None:
            return

        animation_menu.clear()
        asset_motion = action_type("Animasi Aset Scene Terpilih…", self.window)
        asset_motion.setObjectName("AssetMotionAction")
        asset_motion.triggered.connect(
            lambda _checked=False: self.edit_selected_scene_asset_motion()
        )
        animation_menu.addAction(asset_motion)
        self._asset_motion_action = asset_motion

        animation_menu.addSeparator()
        auto_scene = action_type("Auto Motion Scene Terpilih…", self.window)
        auto_scene.setObjectName("AutoMotionSelectedSceneAction")
        auto_scene.triggered.connect(
            lambda _checked=False: self.randomize_native_motion(selected_only=True)
        )
        animation_menu.addAction(auto_scene)
        self._auto_motion_scene_action = auto_scene

        auto_all = action_type("Auto Motion Semua Scene…", self.window)
        auto_all.setObjectName("AutoMotionAllScenesAction")
        auto_all.triggered.connect(
            lambda _checked=False: self.randomize_native_motion(selected_only=False)
        )
        animation_menu.addAction(auto_all)
        self._auto_motion_all_action = auto_all
        self._refresh_animation_menu_state()

    def _build_toolbar(self, toolbar_type: Any, action_type: Any) -> None:
        super()._build_toolbar(toolbar_type, action_type)

        from PySide6.QtWidgets import QComboBox

        for combo in self.window.findChildren(QComboBox):
            items = tuple(combo.itemText(index) for index in range(combo.count()))
            if items != ANIMATION_MODE_ITEMS:
                continue
            combo.setObjectName("AnimationModeCombo")
            combo.setToolTip(
                "Auto (AI): belum tersedia. Random App: Auto Motion semua Scene. "
                "Manual: editor animasi aset Scene terpilih."
            )
            combo.activated.connect(
                lambda index, source=combo: self._activate_animation_mode(
                    source.itemText(index)
                )
            )
            self._animation_mode_combo = combo
            break

    def _activate_animation_mode(self, mode: str) -> None:
        action = animation_mode_action(mode)
        if action == "auto_motion_all":
            self.randomize_native_motion(selected_only=False)
            return
        if action == "manual_asset":
            self.edit_selected_scene_asset_motion()
            return
        if action == "ai_unavailable":
            self._show_project_notice(
                "Auto (AI) belum tersedia",
                "Provider AI untuk Mode Animasi belum terhubung pada build ini. "
                "Gunakan Random App untuk Auto Motion render-backed atau Manual "
                "untuk mengatur animasi aset Scene terpilih.",
            )
            return
        self.window.statusBar().showMessage(
            f"Mode Animasi tidak dikenali: {mode}",
            5000,
        )

    def _refresh_animation_menu_state(self) -> None:
        project = self.services.project_session.current
        has_project = project is not None
        has_selected_scene = self._selected_scene_number is not None
        selected_enabled = animation_menu_enabled(
            has_project=has_project,
            has_selected_scene=has_selected_scene,
        )

        if self._asset_motion_action is not None:
            self._asset_motion_action.setEnabled(selected_enabled)
        if self._auto_motion_scene_action is not None:
            self._auto_motion_scene_action.setEnabled(selected_enabled)
        if self._auto_motion_all_action is not None:
            self._auto_motion_all_action.setEnabled(
                auto_motion_all_enabled(has_project=has_project)
            )
        if self._animation_mode_combo is not None:
            self._animation_mode_combo.setEnabled(
                animation_mode_enabled(has_project=has_project)
            )

    def _remember_selected_scene(self, scene_number: int) -> None:
        super()._remember_selected_scene(scene_number)
        self._refresh_animation_menu_state()

    def show_route(self, route: UiRoute) -> None:
        super().show_route(route)
        self._refresh_animation_menu_state()

    def randomize_native_motion(self, *, selected_only: bool) -> None:
        from PySide6.QtWidgets import QInputDialog

        session = self.services.project_session
        project = session.current
        if project is None:
            self._show_project_notice(
                "Auto Motion tidak tersedia",
                "Buat atau buka proyek terlebih dahulu.",
            )
            self._refresh_animation_menu_state()
            return

        scene_numbers: tuple[int, ...] | None = None
        scope_label = "semua Scene"
        if selected_only:
            scene_number = self._selected_scene_number
            if scene_number is None:
                self._show_project_notice(
                    "Auto Motion Scene tidak tersedia",
                    "Pilih Scene terlebih dahulu.",
                )
                self._refresh_animation_menu_state()
                return
            scene_numbers = (scene_number,)
            scope_label = f"Scene {scene_number:02d}"

        seed, accepted = QInputDialog.getInt(
            self.window,
            "Auto Motion",
            (
                f"Acak animasi native untuk {scope_label}.\n"
                f"Efek: {', '.join(NATIVE_MOTION_CHOICES)}.\n"
                "Assignment yang dikunci tidak akan diganti.\n"
                "Seed yang sama menghasilkan pola yang sama:"
            ),
            value=stored_animation_seed(project.metadata),
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
        self._refresh_animation_menu_state()
        self.window.statusBar().showMessage(
            f"Auto Motion diterapkan ke {scope_label} dengan seed {seed}. "
            "Gunakan Undo untuk membatalkan atau klik Simpan untuk menyimpan perubahan.",
            8000,
        )

    def edit_selected_scene_asset_motion(self) -> None:
        session = self.services.project_session
        project = session.current
        scene_number = self._selected_scene_number
        if project is None or scene_number is None:
            self._show_project_notice(
                "Animasi Aset tidak tersedia",
                "Buat atau buka proyek, lalu pilih Scene terlebih dahulu.",
            )
            self._refresh_animation_menu_state()
            return

        scene = next(
            (item for item in project.scenes if item.scene_number == scene_number),
            None,
        )
        if scene is None:
            self._show_project_notice(
                "Scene tidak ditemukan",
                "Pilih ulang Scene sebelum mengatur animasi aset.",
            )
            return

        result = show_asset_motion_dialog(self.window, scene, project.animations)
        if result is None:
            return

        try:
            if result.action == "apply":
                if result.assignment is None:
                    raise ValueError("Assignment animasi tidak tersedia")
                updated = session.execute(SetAnimationAssignment(result.assignment))
                assignment = next(
                    item
                    for item in updated.animations
                    if item.scene_number == scene_number
                    and item.asset_id == result.asset_id
                )
                message = (
                    f"Animasi {result.asset_id} diterapkan: "
                    f"{assignment.enter_effect} → {assignment.exit_effect}. "
                    "Klik Simpan untuk menyimpan perubahan."
                )
            else:
                session.execute(RemoveAnimationAssignment(scene_number, result.asset_id))
                message = (
                    f"Animasi {result.asset_id} dihapus. "
                    "Klik Simpan untuk menyimpan perubahan."
                )
        except ValueError as error:
            self._show_project_error("Gagal mengubah animasi aset", error)
            return

        self._refresh_window_title()
        self.refresh_editor_overview()
        self._refresh_animation_menu_state()
        self.window.statusBar().showMessage(message, 7000)


def create_animation_menu_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> AnimationMenuMainWindow:
    return AnimationMenuMainWindow(services, initial_state=initial_state)
