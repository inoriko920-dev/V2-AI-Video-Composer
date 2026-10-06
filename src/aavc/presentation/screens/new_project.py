from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aavc.presentation.widgets.common import make_primary_button, muted_label


def create_new_project_screen(
    on_back: Callable[[], None],
    on_continue: Callable[[str], None],
) -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    root = QWidget()
    page = QHBoxLayout(root)
    page.setContentsMargins(0, 0, 0, 0)
    page.setSpacing(0)

    sidebar = QFrame()
    sidebar.setFixedWidth(260)
    sidebar.setStyleSheet("background:#F7FAFE; border-right:1px solid #D8E2EE;")
    side = QVBoxLayout(sidebar)
    side.setContentsMargins(18, 26, 18, 26)
    side.setSpacing(12)
    brand = QLabel("▣  AI Automatic\n    Video Composer")
    brand.setStyleSheet("font-size:16px; font-weight:700; padding:8px;")
    side.addWidget(brand)
    side.addSpacing(12)
    section = QLabel("＋  Proyek Baru")
    section.setMinimumHeight(48)
    section.setStyleSheet(
        "padding:10px 14px; background:#DBEAFE; color:#1D4ED8; "
        "border:1px solid #BFDBFE; border-radius:8px; font-weight:650;"
    )
    side.addWidget(section)
    side.addStretch(1)
    page.addWidget(sidebar)

    content = QWidget()
    outer = QVBoxLayout(content)
    outer.setContentsMargins(90, 42, 90, 42)
    outer.setSpacing(0)

    card = QFrame()
    card.setProperty("panel", True)
    card.setMaximumWidth(1240)
    inner = QVBoxLayout(card)
    inner.setContentsMargins(36, 28, 36, 28)
    inner.setSpacing(18)

    stepper = QHBoxLayout()
    stepper.setSpacing(12)
    steps = [("1", "Scene DOCX", True), ("2", "Folder Aset", False), ("3", "Media", False)]
    for index, (number, label, active) in enumerate(steps):
        circle = QLabel(number)
        circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circle.setFixedSize(38, 38)
        circle.setStyleSheet(
            (
                "background:#2563EB; color:white; border-radius:19px; font-weight:700;"
            )
            if active
            else (
                "background:#F8FAFC; color:#64748B; border:1px solid #CBD5E1; "
                "border-radius:19px; font-weight:700;"
            )
        )
        text = QLabel(label)
        text.setStyleSheet(
            "font-weight:650; color:#1D4ED8;" if active else "color:#64748B;"
        )
        stepper.addWidget(circle)
        stepper.addWidget(text)
        if index < len(steps) - 1:
            line = QFrame()
            line.setFixedHeight(1)
            line.setMinimumWidth(120)
            line.setStyleSheet("background:#CBD5E1;")
            stepper.addWidget(line, 1)
    inner.addLayout(stepper)

    rule = QFrame()
    rule.setFixedHeight(1)
    rule.setStyleSheet("background:#D8E2EE;")
    inner.addWidget(rule)

    title = QLabel("Pilih Scene DOCX")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("font-size:26px; font-weight:750; margin-top:8px;")
    description = muted_label("Unggah file DOCX yang berisi daftar scene beserta mapping aset.")
    description.setAlignment(Qt.AlignmentFlag.AlignCenter)
    description.setStyleSheet("font-size:14px; color:#64748B;")
    inner.addWidget(title)
    inner.addWidget(description)

    dropzone = QFrame()
    dropzone.setMinimumHeight(285)
    dropzone.setStyleSheet(
        "QFrame {background:#F8FBFF; border:1px dashed #7FB2F4; border-radius:10px;} "
        "QLabel {background:transparent;}"
    )
    drop = QVBoxLayout(dropzone)
    drop.setContentsMargins(24, 26, 24, 26)
    drop.setSpacing(10)
    drop.addStretch(1)
    doc_icon = QLabel("DOCX")
    doc_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    doc_icon.setStyleSheet(
        "font-size:20px; font-weight:800; color:white; background:#2563EB; "
        "border-radius:7px; padding:14px;"
    )
    icon_row = QHBoxLayout()
    icon_row.addStretch(1)
    icon_row.addWidget(doc_icon)
    icon_row.addStretch(1)
    drop.addLayout(icon_row)
    hint = QLabel("Tarik file DOCX ke sini atau pilih file")
    hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
    hint.setStyleSheet("color:#64748B; font-size:15px;")
    drop.addWidget(hint)

    path = QLineEdit()
    path.setPlaceholderText("scene_asset_[Judul].docx")
    path.setVisible(False)
    drop.addWidget(path)
    browse = QPushButton("▱  Pilih DOCX")
    browse.setMinimumWidth(170)
    browse.setStyleSheet(
        "color:#1D4ED8; border:1px solid #2563EB; border-radius:7px; "
        "padding:9px 18px; font-weight:650; background:white;"
    )

    def browse_file() -> None:
        chosen, _ = QFileDialog.getOpenFileName(
            root,
            "Pilih Scene DOCX",
            "",
            "DOCX (*.docx)",
        )
        if chosen:
            path.setText(chosen)
            path.setVisible(True)
            next_button.setEnabled(True)

    browse.clicked.connect(browse_file)
    browse_row = QHBoxLayout()
    browse_row.addStretch(1)
    browse_row.addWidget(browse)
    browse_row.addStretch(1)
    drop.addLayout(browse_row)
    drop.addStretch(1)
    inner.addWidget(dropzone)

    info = QFrame()
    info.setStyleSheet("background:#F4F8FD; border:1px solid #D8E2EE; border-radius:8px;")
    info_layout = QHBoxLayout(info)
    info_layout.setContentsMargins(18, 14, 18, 14)
    info_icon = QLabel("ⓘ")
    info_icon.setStyleSheet("font-size:22px; color:#2563EB;")
    info_text = QVBoxLayout()
    info_title = QLabel("Persyaratan File DOCX")
    info_title.setStyleSheet("font-weight:700;")
    info_desc = muted_label(
        "File harus berisi daftar scene dan mapping aset sesuai format Prompt 1. "
        "Setiap scene wajib memiliki 1 atau 2 Asset ID canonical Axxx."
    )
    info_text.addWidget(info_title)
    info_text.addWidget(info_desc)
    info_layout.addWidget(info_icon)
    info_layout.addLayout(info_text, 1)
    inner.addWidget(info)

    footer_rule = QFrame()
    footer_rule.setFixedHeight(1)
    footer_rule.setStyleSheet("background:#D8E2EE;")
    inner.addWidget(footer_rule)
    footer = QHBoxLayout()
    cancel_button = QPushButton("Batal")
    cancel_button.clicked.connect(on_back)
    next_button = make_primary_button("Lanjut")
    next_button.setEnabled(False)
    next_button.clicked.connect(lambda _checked=False: on_continue(path.text()))
    footer.addWidget(cancel_button)
    footer.addStretch(1)
    footer.addWidget(next_button)
    inner.addLayout(footer)

    centered = QHBoxLayout()
    centered.addStretch(1)
    centered.addWidget(card, 1)
    centered.addStretch(1)
    outer.addLayout(centered, 1)
    page.addWidget(content, 1)
    return root
