"""Frozen STEP 09 presentation tokens.

This module deliberately contains no Qt import so geometry/color contracts can be
validated without a GUI runtime.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Colors:
    app_bg: str = "#F4F7FB"
    surface: str = "#FFFFFF"
    panel: str = "#F8FAFD"
    border: str = "#D8E2EE"
    primary: str = "#2563EB"
    primary_hover: str = "#1D4ED8"
    focus: str = "#93C5FD"
    selection: str = "#DBEAFE"
    text: str = "#172033"
    muted: str = "#64748B"
    disabled_bg: str = "#F1F5F9"
    disabled_text: str = "#94A3B8"
    success: str = "#16A34A"
    warning: str = "#F59E0B"
    error: str = "#DC2626"
    monitor_matte: str = "#171C24"


@dataclass(frozen=True, slots=True)
class Metrics:
    title_bar_h: int = 32
    menu_h: int = 34
    toolbar_h: int = 48
    left_ref_w: int = 300
    left_min_w: int = 240
    right_ref_w: int = 360
    right_max_w: int = 480
    timeline_ref_h: int = 300
    timeline_min_h: int = 180
    status_h: int = 26
    radius: int = 8
    border: int = 1
    spacing: int = 8


COLORS = Colors()
METRICS = Metrics()


def app_stylesheet() -> str:
    """Return the canonical QSS used by STEP 09 widgets."""
    c = COLORS
    return f"""
    QMainWindow, QWidget {{
        background: {c.app_bg}; color: {c.text};
        font-family: 'Segoe UI'; font-size: 12px;
    }}
    QMenuBar {{ background: {c.surface}; border-bottom: 1px solid {c.border}; }}
    QMenuBar::item {{ padding: 7px 10px; background: transparent; }}
    QMenuBar::item:selected {{ background: {c.selection}; color: {c.primary_hover}; }}
    QMenu::item:disabled {{ color: {c.disabled_text}; }}
    QToolBar {{ background: {c.surface}; border: none; border-bottom: 1px solid {c.border}; spacing: 6px; padding: 4px 8px; }}
    QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: 6px; padding: 6px 9px; }}
    QToolButton:hover {{ background: {c.selection}; border-color: {c.border}; }}
    QToolButton:focus {{ border-color: {c.focus}; }}
    QToolButton:disabled {{ color: {c.disabled_text}; background: transparent; }}
    QPushButton {{ background: {c.surface}; border: 1px solid {c.border}; border-radius: 7px; padding: 7px 12px; min-height: 18px; }}
    QPushButton:hover {{ border-color: {c.primary}; }}
    QPushButton:focus {{ border-color: {c.focus}; }}
    QPushButton:disabled {{ background: {c.disabled_bg}; color: {c.disabled_text}; border-color: {c.border}; }}
    QPushButton[primary='true'] {{ background: {c.primary}; color: white; border-color: {c.primary}; font-weight: 600; }}
    QPushButton[primary='true']:hover {{ background: {c.primary_hover}; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ background: {c.surface}; border: 1px solid {c.border}; border-radius: 6px; padding: 6px; }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {c.focus}; }}
    QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{ background: {c.disabled_bg}; color: {c.disabled_text}; }}
    QTabWidget::pane {{ border: 1px solid {c.border}; background: {c.surface}; }}
    QTabBar::tab {{ padding: 8px 14px; background: {c.panel}; border-bottom: 2px solid transparent; }}
    QTabBar::tab:selected {{ color: {c.primary}; border-bottom: 2px solid {c.primary}; background: {c.surface}; }}
    QListWidget::item:selected {{ background: {c.selection}; color: {c.text}; }}
    QFrame[panel='true'] {{ background: {c.surface}; border: 1px solid {c.border}; border-radius: 6px; }}
    QLabel[muted='true'] {{ color: {c.muted}; }}
    QLabel[badge='ready'] {{ color: {c.success}; font-weight: 600; }}
    QLabel[badge='warning'] {{ color: {c.warning}; font-weight: 600; }}
    QLabel[badge='error'] {{ color: {c.error}; font-weight: 600; }}
    QStatusBar {{ background: {c.surface}; border-top: 1px solid {c.border}; color: {c.muted}; }}
    QSplitter::handle {{ background: {c.border}; width: 1px; height: 1px; }}
    QScrollArea {{ border: none; background: transparent; }}
    QToolTip {{ background: {c.surface}; color: {c.text}; border: 1px solid {c.border}; padding: 5px; }}
    """
