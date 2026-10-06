from __future__ import annotations

from aavc.presentation.windows.help_window import format_quick_help


def test_quick_help_formats_live_shortcuts_and_timeline_gestures() -> None:
    text = format_quick_help(
        (
            ("Undo", "Ctrl+Z"),
            ("Duplikasi Scene", "Ctrl+D"),
        )
    )

    assert "Ctrl+Z — Undo" in text
    assert "Ctrl+D — Duplikasi Scene" in text
    assert "Drag blok Scene — ubah urutan Scene." in text
    assert "Drag tepi kanan blok — ubah durasi Scene." in text


def test_quick_help_handles_no_shortcuts() -> None:
    text = format_quick_help(())

    assert "Belum ada shortcut keyboard aktif." in text
