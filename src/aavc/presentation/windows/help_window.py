from __future__ import annotations

from typing import Any

from aavc.bootstrap.composition_root import FoundationServices
from aavc.presentation.windows.subtitle_timing_tools_window import (
    SubtitleTimingToolsMainWindow,
)


def format_quick_help(shortcuts: tuple[tuple[str, str], ...]) -> str:
    """Build concise help text from live QAction shortcut metadata."""

    lines = ["SHORTCUT KEYBOARD"]
    if shortcuts:
        lines.extend(f"{shortcut} — {label}" for label, shortcut in shortcuts)
    else:
        lines.append("Belum ada shortcut keyboard aktif.")

    lines.extend(
        [
            "",
            "GESTURE TIMELINE",
            "Klik blok Scene — pilih/seek Scene.",
            "Drag blok Scene — ubah urutan Scene.",
            "Drag tepi kanan blok — ubah durasi Scene.",
            "",
            "Catatan: Undo/Redo dan Simpan tetap mengikuti ProjectHistory/project aktif.",
        ]
    )
    return "\n".join(lines)


class HelpMainWindow(SubtitleTimingToolsMainWindow):
    """Expose live shortcut/gesture help instead of the original placeholder."""

    def _build_menu(self, action_type: Any) -> None:
        super()._build_menu(action_type)

        help_menu: Any | None = None
        for menu_action in self.window.menuBar().actions():
            if menu_action.text() == "Bantuan":
                help_menu = menu_action.menu()
                break
        if help_menu is None:
            return

        help_menu.clear()
        quick_help = action_type("Shortcut & Bantuan Cepat", self.window)
        quick_help.triggered.connect(lambda _checked=False: self.open_quick_help())
        help_menu.addAction(quick_help)

    def _active_shortcuts(self) -> tuple[tuple[str, str], ...]:
        rows: list[tuple[str, str]] = []
        for menu_action in self.window.menuBar().actions():
            menu: Any | None = menu_action.menu()
            if menu is None:
                continue
            for action in menu.actions():
                if action.isSeparator() or not action.isEnabled():
                    continue
                shortcut = action.shortcut().toString()
                label = action.text().replace("&", "").strip()
                if shortcut and label:
                    rows.append((label, shortcut))
        return tuple(rows)

    def open_quick_help(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        box = QMessageBox(self.window)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("Shortcut & Bantuan Cepat")
        box.setText("Kontrol editor yang aktif pada build source ini")
        box.setDetailedText(format_quick_help(self._active_shortcuts()))
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()


def create_help_main_window(
    services: FoundationServices,
    initial_state: str = "UI-002",
) -> HelpMainWindow:
    return HelpMainWindow(services, initial_state=initial_state)
