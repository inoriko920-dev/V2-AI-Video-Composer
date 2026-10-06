from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aavc.presentation.widgets.common import make_primary_button, muted_label


def create_home_screen(
    on_new_project: Callable[[], None],
    on_open_editor: Callable[[], None],
    on_quick_help: Callable[[], None] | None = None,
) -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    root = QWidget()
    outer = QVBoxLayout(root)
    outer.setContentsMargins(30, 20, 30, 34)
    outer.setSpacing(20)

    header = QHBoxLayout()
    brand = QLabel("▣   AI Automatic Video Composer")
    brand.setStyleSheet("font-size:20px; font-weight:700;")
    quick_help = QPushButton("?  Bantuan Cepat")
    quick_help.setStyleSheet("color:#2563EB; border:none; font-weight:600;")
    if on_quick_help is None:
        quick_help.setVisible(False)
    else:
        quick_help.clicked.connect(on_quick_help)
    header.addWidget(brand)
    header.addStretch(1)
    header.addWidget(quick_help)
    outer.addLayout(header)

    hero = QVBoxLayout()
    hero.setSpacing(6)
    title = QLabel("Mulai Proyek")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("font-size:34px; font-weight:750; margin-top:12px;")
    subtitle = muted_label(
        "Buat proyek baru atau buka proyek yang sudah ada untuk mulai mengedit video "
        "dengan bantuan AI."
    )
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle.setStyleSheet("font-size:15px; color:#64748B;")
    hero.addWidget(title)
    hero.addWidget(subtitle)
    outer.addLayout(hero)

    action_row = QHBoxLayout()
    action_row.setSpacing(18)
    action_row.addStretch(1)

    new_card = QFrame()
    new_card.setMinimumSize(460, 130)
    new_card.setMaximumWidth(560)
    new_card.setStyleSheet(
        "QFrame {background:#2563EB; border-radius:12px;} "
        "QLabel {color:white; background:transparent;}"
    )
    new_layout = QHBoxLayout(new_card)
    new_layout.setContentsMargins(34, 24, 34, 24)
    new_icon = QLabel("＋")
    new_icon.setStyleSheet("font-size:42px; font-weight:300;")
    new_text = QVBoxLayout()
    new_title = QLabel("Proyek Baru")
    new_title.setStyleSheet("font-size:20px; font-weight:700;")
    new_desc = QLabel("Buat proyek video baru\ndengan bantuan AI")
    new_desc.setStyleSheet("font-size:14px;")
    new_text.addWidget(new_title)
    new_text.addWidget(new_desc)
    new_layout.addWidget(new_icon)
    new_layout.addSpacing(18)
    new_layout.addLayout(new_text, 1)
    new_button = make_primary_button("Mulai")
    new_button.clicked.connect(on_new_project)
    new_button.setMaximumWidth(90)
    new_layout.addWidget(new_button)

    open_card = QFrame()
    open_card.setProperty("panel", True)
    open_card.setMinimumSize(460, 130)
    open_card.setMaximumWidth(560)
    open_layout = QHBoxLayout(open_card)
    open_layout.setContentsMargins(34, 24, 34, 24)
    open_icon = QLabel("▱")
    open_icon.setStyleSheet("font-size:42px; color:#2563EB;")
    open_text = QVBoxLayout()
    open_title = QLabel("Buka Proyek")
    open_title.setStyleSheet("font-size:20px; font-weight:700;")
    open_desc = muted_label("Buka proyek yang sudah ada\ndari perangkat Anda")
    open_desc.setStyleSheet("font-size:14px; color:#64748B;")
    open_text.addWidget(open_title)
    open_text.addWidget(open_desc)
    open_layout.addWidget(open_icon)
    open_layout.addSpacing(18)
    open_layout.addLayout(open_text, 1)
    open_button = QPushButton("Buka")
    open_button.clicked.connect(on_open_editor)
    open_button.setMaximumWidth(90)
    open_layout.addWidget(open_button)

    action_row.addWidget(new_card)
    action_row.addWidget(open_card)
    action_row.addStretch(1)
    outer.addLayout(action_row)

    project_panel = QFrame()
    project_panel.setProperty("panel", True)
    project_panel.setMaximumWidth(980)
    project_layout = QHBoxLayout(project_panel)
    project_layout.setContentsMargins(28, 22, 28, 22)

    project_text = QVBoxLayout()
    project_title = QLabel("Project dari Perangkat")
    project_title.setStyleSheet("font-size:20px; font-weight:700;")
    project_text.addWidget(project_title)
    project_text.addWidget(
        muted_label(
            "Pilih file .aavcproj yang sudah ada. Home runtime tidak menampilkan project "
            "contoh atau riwayat palsu."
        )
    )
    project_layout.addLayout(project_text, 1)

    open_existing = QPushButton("Buka Proyek…")
    open_existing.clicked.connect(on_open_editor)
    project_layout.addWidget(open_existing)

    project_wrap = QHBoxLayout()
    project_wrap.addStretch(1)
    project_wrap.addWidget(project_panel, 1)
    project_wrap.addStretch(1)
    outer.addLayout(project_wrap, 1)
    return root
