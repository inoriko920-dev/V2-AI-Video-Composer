from __future__ import annotations

from aavc.presentation.design_tokens import COLORS, app_stylesheet
from aavc.presentation.windows.animation_menu_window import animation_mode_enabled
from aavc.presentation.windows.background_work_window import (
    background_cancel_action_enabled,
)
from aavc.presentation.windows.guarded_main_window import GuardedMainWindow


def test_animation_mode_selector_requires_active_project() -> None:
    assert animation_mode_enabled(has_project=False) is False
    assert animation_mode_enabled(has_project=True) is True


def test_background_cancel_action_tracks_busy_state() -> None:
    assert background_cancel_action_enabled(background_busy=False) is False
    assert background_cancel_action_enabled(background_busy=True) is True


def test_wave_h_stylesheet_has_focus_and_disabled_contracts() -> None:
    qss = app_stylesheet()

    assert COLORS.focus in qss
    assert COLORS.disabled_text in qss
    assert "QToolButton:focus" in qss
    assert "QPushButton:disabled" in qss
    assert "QLineEdit:focus" in qss
    assert "QComboBox:disabled" in qss
    assert "QToolTip" in qss


def test_guarded_runtime_menu_builder_owns_scene_animation_copy_paste() -> None:
    # The Guarded layer rebuilds Edit after MainWindow, so these methods must be
    # directly referenced by its menu builder or the actions disappear at runtime.
    names = GuardedMainWindow._build_menu.__code__.co_names
    constants = GuardedMainWindow._build_menu.__code__.co_consts

    assert "copy_selected_scene_animation" in names
    assert "paste_animation_to_selected_scene" in names
    assert "Salin Animasi Scene" in constants
    assert "Tempel Animasi Scene" in constants
