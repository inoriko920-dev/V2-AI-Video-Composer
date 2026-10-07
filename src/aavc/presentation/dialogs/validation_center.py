from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from aavc.application.services.validation import ValidationIssue
from aavc.presentation.widgets.common import make_primary_button, muted_label


@dataclass(frozen=True, slots=True)
class ValidationSummary:
    errors: int
    warnings: int

    @property
    def total(self) -> int:
        return self.errors + self.warnings

    @property
    def ok(self) -> bool:
        return self.total == 0


def summarize_validation_issues(issues: tuple[ValidationIssue, ...]) -> ValidationSummary:
    return ValidationSummary(
        errors=sum(issue.severity == "ERROR" for issue in issues),
        warnings=sum(issue.severity == "WARNING" for issue in issues),
    )


def validation_category(issue: ValidationIssue) -> str:
    if issue.code in {"ASSET_NOT_READY", "NARRATION_NOT_FOUND", "SUBTITLE_NOT_FOUND"}:
        return "Media"
    if issue.code == "SCENE_DURATION_SHORT":
        return "Scene"
    if issue.code in {
        "VISUAL_EFFECT_FALLBACK",
        "KEYFRAME_TRACK_FALLBACK",
        "ADVANCED_TRACK_DORMANT",
        "ADVANCED_BACKEND_UNAVAILABLE",
        "ADVANCED_PARAMETER_MISMATCH",
        "ADVANCED_CROP_NORMALIZED",
        "ADVANCED_VALUE_CLAMPED",
    }:
        return "Render"
    return "Project"


def validation_issue_action(issue: ValidationIssue) -> tuple[str, str] | None:
    if issue.code == "ASSET_NOT_READY" and issue.asset_id:
        return ("Relink", issue.asset_id)
    if issue.code in {"NARRATION_NOT_FOUND", "SUBTITLE_NOT_FOUND"}:
        return ("Impor Media", "")
    if (
        issue.scene_number is not None
        and issue.code
        in {
            "SCENE_DURATION_SHORT",
            "VISUAL_EFFECT_FALLBACK",
            "KEYFRAME_TRACK_FALLBACK",
            "ADVANCED_TRACK_DORMANT",
            "ADVANCED_BACKEND_UNAVAILABLE",
            "ADVANCED_PARAMETER_MISMATCH",
            "ADVANCED_CROP_NORMALIZED",
            "ADVANCED_VALUE_CLAMPED",
        }
    ):
        return ("Buka Scene", str(issue.scene_number))
    return None


def _create_reference_validation_dialog(parent: Any = None) -> Any:
    """Frozen no-session fixture used by the STEP09 visual reference capture."""

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    dialog = QDialog(parent)
    dialog.setWindowTitle("Pusat Error / Validasi")
    dialog.resize(650, 900)
    dialog.setMinimumWidth(600)
    dialog.setStyleSheet(
        "QDialog {background:#FFFFFF; border-left:1px solid #CBD5E1;} "
        "QTabWidget::pane {border:none; border-top:1px solid #E2E8F0;}"
    )

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 16, 20, 18)
    layout.setSpacing(14)

    title_row = QHBoxLayout()
    panel_title = QLabel("Pusat Error / Validasi")
    panel_title.setStyleSheet("font-size:20px; font-weight:750;")
    close_button = QPushButton("×")
    close_button.setMaximumWidth(36)
    close_button.clicked.connect(dialog.close)
    close_button.setStyleSheet("border:none; font-size:20px;")
    title_row.addWidget(panel_title)
    title_row.addStretch(1)
    title_row.addWidget(close_button)
    layout.addLayout(title_row)

    summary = QFrame()
    summary.setStyleSheet("background:#FFF7F7; border:1px solid #FECACA; border-radius:9px;")
    summary_layout = QHBoxLayout(summary)
    summary_layout.setContentsMargins(14, 12, 14, 12)
    error_icon = QLabel("!")
    error_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    error_icon.setFixedSize(38, 38)
    error_icon.setStyleSheet(
        "background:#DC2626; color:white; border-radius:19px; font-size:22px; font-weight:800;"
    )
    summary_text = QVBoxLayout()
    summary_title = QLabel("2 Error, 3 Peringatan")
    summary_title.setStyleSheet("font-size:18px; font-weight:750; color:#B91C1C;")
    summary_text.addWidget(summary_title)
    summary_text.addWidget(muted_label("Ditemukan 5 masalah dalam project ini"))
    summary_layout.addWidget(error_icon)
    summary_layout.addLayout(summary_text, 1)
    summary_layout.addWidget(make_primary_button("Validasi Ulang"))
    layout.addWidget(summary)

    tabs = QTabWidget()
    tab_names = [
        "Semua (5)",
        "Project (1)",
        "Media (1)",
        "Scene (1)",
        "AI (1)",
        "Render (1)",
    ]
    issues = [
        (
            "ERROR",
            "A037 MISSING — Scene 12, 13",
            "File media tidak ditemukan. Digunakan di Scene 12 dan Scene 13.",
            "Relink",
        ),
        (
            "ERROR",
            "Subtitle cue tumpang tindih",
            "Terdapat 3 subtitle yang saling tumpang tindih pada Scene 05.",
            "Buka Subtitle",
        ),
        (
            "PERINGATAN",
            "Durasi scene terlalu pendek",
            "Scene 04 hanya 0,8 detik; disarankan minimal 2 detik.",
            "Buka Scene",
        ),
        (
            "PERINGATAN",
            "Audio tidak normalisasi",
            "Audio pada track A1 (voiceover.mp3) belum dinormalisasi.",
            "Perbaiki Audio",
        ),
        (
            "PERINGATAN",
            "Provider Gemini quota",
            "Sisa quota hanya 12%. Proses AI mungkin gagal jika quota habis.",
            "Buka Provider",
        ),
    ]

    for name in tab_names:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(4, 14, 4, 6)
        page_layout.setSpacing(10)
        if name.startswith("Semua"):
            error_heading = QLabel("Error (2)")
            error_heading.setStyleSheet("font-size:15px; font-weight:750;")
            page_layout.addWidget(error_heading)
            for index, (severity, issue_title, description, action) in enumerate(issues):
                if index == 2:
                    warning_heading = QLabel("Peringatan (3)")
                    warning_heading.setStyleSheet("font-size:15px; font-weight:750; margin-top:8px;")
                    page_layout.addWidget(warning_heading)
                row_frame = QFrame()
                is_error = severity == "ERROR"
                accent = "#DC2626" if is_error else "#F59E0B"
                row_frame.setStyleSheet(
                    "QFrame {background:#FFFFFF; border:1px solid #E2E8F0; "
                    f"border-left:4px solid {accent}; border-radius:6px;}}"
                )
                row = QHBoxLayout(row_frame)
                row.setContentsMargins(12, 11, 10, 11)
                badge = QLabel("!" if is_error else "▲")
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge.setFixedSize(30, 30)
                badge.setStyleSheet(
                    f"color:{accent}; background:#FFF7ED; border:none; font-weight:800;"
                )
                block = QVBoxLayout()
                title_label = QLabel(issue_title)
                title_label.setStyleSheet("font-weight:700; border:none;")
                description_label = muted_label(description)
                description_label.setStyleSheet("color:#64748B; border:none;")
                block.addWidget(title_label)
                block.addWidget(description_label)
                action_button = QPushButton(action)
                action_button.setStyleSheet(
                    "color:#1D4ED8; border:none; font-weight:650; background:transparent;"
                )
                row.addWidget(badge)
                row.addLayout(block, 1)
                row.addWidget(action_button)
                page_layout.addWidget(row_frame)
        page_layout.addStretch(1)
        tabs.addTab(page, name)

    layout.addWidget(tabs, 1)
    return dialog


def _issue_title(issue: ValidationIssue) -> str:
    if issue.asset_id and issue.scene_number is not None:
        return f"{issue.asset_id} — Scene {issue.scene_number}"
    if issue.scene_number is not None:
        return f"Scene {issue.scene_number}"
    return issue.code


def _create_live_validation_dialog(
    parent: Any,
    issues: tuple[ValidationIssue, ...],
    on_revalidate: Callable[[], None] | None,
    on_relink: Callable[[str], None] | None,
    on_open_scene: Callable[[int], None] | None,
    on_import_media: Callable[[], None] | None,
) -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    dialog = QDialog(parent)
    dialog.setWindowTitle("Pusat Error / Validasi")
    dialog.resize(650, 900)
    dialog.setMinimumWidth(600)
    dialog.setStyleSheet(
        "QDialog {background:#FFFFFF; border-left:1px solid #CBD5E1;} "
        "QTabWidget::pane {border:none; border-top:1px solid #E2E8F0;}"
    )

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 16, 20, 18)
    layout.setSpacing(14)

    title_row = QHBoxLayout()
    panel_title = QLabel("Pusat Error / Validasi")
    panel_title.setStyleSheet("font-size:20px; font-weight:750;")
    close_button = QPushButton("×")
    close_button.setMaximumWidth(36)
    close_button.clicked.connect(dialog.close)
    close_button.setStyleSheet("border:none; font-size:20px;")
    title_row.addWidget(panel_title)
    title_row.addStretch(1)
    title_row.addWidget(close_button)
    layout.addLayout(title_row)

    counts = summarize_validation_issues(issues)
    summary = QFrame()
    summary_layout = QHBoxLayout(summary)
    summary_layout.setContentsMargins(14, 12, 14, 12)
    icon = QLabel()
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setFixedSize(38, 38)
    summary_text = QVBoxLayout()

    if counts.errors:
        accent = "#DC2626"
        summary.setStyleSheet("background:#FFF7F7; border:1px solid #FECACA; border-radius:9px;")
        icon.setText("!")
        icon.setStyleSheet(
            "background:#DC2626; color:white; border-radius:19px; font-size:22px; font-weight:800;"
        )
        headline = f"{counts.errors} Error, {counts.warnings} Peringatan"
        detail = f"Ditemukan {counts.total} masalah dalam project ini"
    elif counts.warnings:
        accent = "#B45309"
        summary.setStyleSheet("background:#FFFBEB; border:1px solid #FDE68A; border-radius:9px;")
        icon.setText("▲")
        icon.setStyleSheet(
            "background:#F59E0B; color:white; border-radius:19px; font-size:18px; font-weight:800;"
        )
        headline = f"0 Error, {counts.warnings} Peringatan"
        detail = f"Ditemukan {counts.warnings} peringatan dalam project ini"
    else:
        accent = "#15803D"
        summary.setStyleSheet("background:#F0FDF4; border:1px solid #BBF7D0; border-radius:9px;")
        icon.setText("✓")
        icon.setStyleSheet(
            "background:#16A34A; color:white; border-radius:19px; font-size:20px; font-weight:800;"
        )
        headline = "Project Valid"
        detail = "Tidak ada error atau peringatan yang terdeteksi"

    summary_title = QLabel(headline)
    summary_title.setStyleSheet(f"font-size:18px; font-weight:750; color:{accent};")
    summary_text.addWidget(summary_title)
    summary_text.addWidget(muted_label(detail))
    summary_layout.addWidget(icon)
    summary_layout.addLayout(summary_text, 1)

    revalidate = make_primary_button("Validasi Ulang")

    def run_revalidate() -> None:
        dialog.close()
        if on_revalidate is not None:
            on_revalidate()

    revalidate.clicked.connect(run_revalidate)
    summary_layout.addWidget(revalidate)
    layout.addWidget(summary)

    categories = ("Semua", "Project", "Media", "Scene", "AI", "Render")
    categorized = {
        category: tuple(
            issue
            for issue in issues
            if category == "Semua" or validation_category(issue) == category
        )
        for category in categories
    }

    tabs = QTabWidget()
    for category in categories:
        category_issues = categorized[category]
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(4, 14, 4, 6)
        page_layout.setSpacing(10)

        if not category_issues:
            empty = muted_label("Tidak ada masalah pada kategori ini.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_layout.addWidget(empty)
        else:
            for issue in category_issues:
                row_frame = QFrame()
                is_error = issue.severity == "ERROR"
                row_accent = "#DC2626" if is_error else "#F59E0B"
                row_frame.setStyleSheet(
                    "QFrame {background:#FFFFFF; border:1px solid #E2E8F0; "
                    f"border-left:4px solid {row_accent}; border-radius:6px;}}"
                )
                row = QHBoxLayout(row_frame)
                row.setContentsMargins(12, 11, 10, 11)
                badge = QLabel("!" if is_error else "▲")
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge.setFixedSize(30, 30)
                badge.setStyleSheet(
                    f"color:{row_accent}; background:#FFF7ED; border:none; font-weight:800;"
                )
                block = QVBoxLayout()
                title_label = QLabel(_issue_title(issue))
                title_label.setStyleSheet("font-weight:700; border:none;")
                description_label = muted_label(issue.message)
                description_label.setStyleSheet("color:#64748B; border:none;")
                block.addWidget(title_label)
                block.addWidget(description_label)
                row.addWidget(badge)
                row.addLayout(block, 1)

                action = validation_issue_action(issue)
                if action is not None:
                    label, target = action
                    action_button = QPushButton(label)
                    action_button.setStyleSheet(
                        "color:#1D4ED8; border:none; font-weight:650; background:transparent;"
                    )

                    def run_action(
                        _checked: bool = False,
                        action_label: str = label,
                        action_target: str = target,
                    ) -> None:
                        dialog.close()
                        if action_label == "Relink" and on_relink is not None:
                            on_relink(action_target)
                        elif action_label == "Buka Scene" and on_open_scene is not None:
                            on_open_scene(int(action_target))
                        elif action_label == "Impor Media" and on_import_media is not None:
                            on_import_media()

                    action_button.clicked.connect(run_action)
                    row.addWidget(action_button)

                page_layout.addWidget(row_frame)

        page_layout.addStretch(1)
        tabs.addTab(page, f"{category} ({len(category_issues)})")

    layout.addWidget(tabs, 1)
    return dialog


def create_validation_dialog(
    parent: Any = None,
    *,
    issues: tuple[ValidationIssue, ...] | None = None,
    on_revalidate: Callable[[], None] | None = None,
    on_relink: Callable[[str], None] | None = None,
    on_open_scene: Callable[[int], None] | None = None,
    on_import_media: Callable[[], None] | None = None,
) -> Any:
    if issues is None:
        return _create_reference_validation_dialog(parent)
    return _create_live_validation_dialog(
        parent,
        issues,
        on_revalidate,
        on_relink,
        on_open_scene,
        on_import_media,
    )
