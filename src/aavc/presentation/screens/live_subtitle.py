from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from aavc.domain.project.models import SubtitleAnimationSettings, SubtitleStyle
from aavc.presentation.widgets.editor_shell import create_editor_shell, remove_tabs_by_label
from aavc.presentation.widgets.live_subtitle import create_live_subtitle_inspector
from aavc.presentation.widgets.subtitle_cue_edit import create_subtitle_cue_edit_page
from aavc.subtitles import SubtitleCue


def create_live_subtitle_screen(
    source: str | Path,
    *,
    style: SubtitleStyle | None = None,
    animation: SubtitleAnimationSettings | None = None,
    on_apply_style: Callable[[SubtitleStyle], None] | None = None,
    on_apply_animation: Callable[[SubtitleAnimationSettings], None] | None = None,
    on_reload: Callable[[], None] | None = None,
    on_save_copy: Callable[[tuple[SubtitleCue, ...]], None] | None = None,
    on_working_copy_dirty_changed: Callable[[bool], None] | None = None,
) -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget

    source_path = Path(source).resolve()
    cue_working_copy_dirty = False

    def set_cue_working_copy_dirty(is_dirty: bool) -> None:
        nonlocal cue_working_copy_dirty
        cue_working_copy_dirty = is_dirty
        if on_working_copy_dirty_changed is not None:
            on_working_copy_dirty_changed(is_dirty)

    def reload_with_working_copy_guard() -> None:
        if on_reload is None:
            return
        if not cue_working_copy_dirty:
            on_reload()
            return
        answer = QMessageBox.question(
            None,
            "Buang edit working copy?",
            "Working copy subtitle atau form cue aktif memiliki perubahan yang belum disimpan "
            "sebagai salinan. Muat ulang SRT akan membuang perubahan tersebut. Lanjutkan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            on_reload()

    parts = create_editor_shell("subtitle")
    remove_tabs_by_label(parts.right_tabs, {"AI Agent"})
    inspector = create_live_subtitle_inspector(
        source_path,
        style=style,
        animation=animation,
        on_apply_style=on_apply_style,
        on_apply_animation=on_apply_animation,
        on_reload=reload_with_working_copy_guard if on_reload is not None else None,
    )
    inspector.addTab(
        create_subtitle_cue_edit_page(
            source_path,
            on_save_copy=on_save_copy,
            on_dirty_changed=set_cue_working_copy_dirty,
        ),
        "Edit Cue",
    )

    parts.right_tabs.removeTab(0)
    parts.right_tabs.insertTab(0, inspector, "Subtitle")
    parts.right_tabs.setCurrentIndex(0)

    parts.left_tabs.clear()
    source_page = QWidget()
    source_layout = QVBoxLayout(source_page)
    source_layout.addWidget(QLabel("Subtitle Project Aktif"))
    source_name = QLabel(source_path.name)
    source_name.setWordWrap(True)
    source_name.setStyleSheet("font-weight:700;")
    source_layout.addWidget(source_name)
    source_note = QLabel(
        "Daftar cue, gaya, animasi, dan editor cue berada pada panel kanan. Kembali ke "
        "Editor untuk memilih Scene atau melihat timeline project."
    )
    source_note.setWordWrap(True)
    source_note.setStyleSheet("color:#64748B;")
    source_layout.addWidget(source_note)
    source_layout.addStretch(1)
    parts.left_tabs.addTab(source_page, "SRT")

    parts.preview_label.clear()
    parts.preview_label.setText(
        "Preview burn-in subtitle tersedia pada Editor Overview.\n"
        "Tab Edit Cue menyimpan salinan SRT baru; source asli tidak ditimpa oleh flow tersebut."
    )
    parts.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    parts.preview_label.setStyleSheet(
        "border:1px solid #CBD5E1; background:#F8FAFD; color:#64748B; padding:24px;"
    )
    parts.timeline.setVisible(False)
    parts.status_label.setText(
        f"Subtitle aktif: {source_path.name}   ·   Edit cue → salinan SRT   ·   "
        "Gaya + animasi subtitle render-backed"
    )
    return parts.root
