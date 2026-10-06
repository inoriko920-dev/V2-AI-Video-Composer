from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

from aavc.presentation.design_tokens import COLORS, METRICS
from aavc.presentation.visual_mock import asset_pixmap, scene_pixmap
from aavc.presentation.widgets.common import make_primary_button, muted_label, section_title


@dataclass(slots=True)
class EditorShellParts:
    root: Any
    left_tabs: Any
    preview_frame: Any
    preview_label: Any
    right_tabs: Any
    timeline: Any
    status_label: Any


def remove_tabs_by_label(tab_widget: Any, labels: Collection[str]) -> tuple[str, ...]:
    """Remove reference-only tabs from a live runtime surface."""

    removed: list[str] = []
    for index in range(tab_widget.count() - 1, -1, -1):
        label = tab_widget.tabText(index)
        if label not in labels:
            continue
        widget = tab_widget.widget(index)
        tab_widget.removeTab(index)
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        removed.append(label)
    removed.reverse()
    return tuple(removed)


def _asset_grid() -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

    container = QWidget()
    grid = QGridLayout(container)
    grid.setContentsMargins(6, 6, 6, 6)
    grid.setSpacing(6)
    samples = [
        ("A001", "Pohon", "READY"),
        ("A002", "Rumah", "READY"),
        ("A003", "Awan", "READY"),
        ("A004", "Mobil", "READY"),
        ("A005", "Anak", "READY"),
        ("A006", "Tokoh", "READY"),
        ("A007", "Matahari", "READY"),
        ("A008", "Gunung", "READY"),
        ("A009", "Papan", "READY"),
        ("A010", "Anjing", "READY"),
        ("A011", "Burung", "READY"),
        ("A012", "Semak", "READY"),
        ("A013", "Pagar", "MISSING"),
        ("A014", "Kucing", "READY"),
        ("A015", "Lampu", "READY"),
    ]
    for index, (asset_id, subject, status) in enumerate(samples):
        card = QFrame()
        card.setProperty("panel", True)
        if asset_id == "A014":
            card.setStyleSheet("QFrame {border:2px solid #2563EB; border-radius:6px;}")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        thumb = QLabel()
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setMinimumHeight(54)
        thumb.setPixmap(asset_pixmap(subject))
        thumb.setScaledContents(True)
        thumb.setStyleSheet("border:1px solid #D8E2EE; background:#F8FAFD;")
        info = QLabel(f"{asset_id}  ·  {status}")
        info.setStyleSheet(
            "color:#16A34A; font-size:9px;"
            if status == "READY"
            else "color:#F59E0B; font-size:9px;"
        )
        layout.addWidget(thumb)
        layout.addWidget(info)
        grid.addWidget(card, index // 3, index % 3)
    return container


def _scene_list() -> Any:
    from PySide6.QtWidgets import QListWidget, QListWidgetItem

    widget = QListWidget()
    widget.setSpacing(4)
    samples = [
        (1, "Pembukaan", "Indonesia: Negeri Kepulauan", "00:00 – 00:08", "SINGLE"),
        (2, "Keindahan Alam", "Laut, Gunung, dan Hutan", "00:08 – 00:20", "DOUBLE"),
        (3, "Keanekaragaman Budaya", "Satu Bangsa, Banyak Cerita", "00:20 – 00:32", "DOUBLE"),
        (4, "Potensi Masa Depan", "Energi, Inovasi, Generasi Muda", "00:32 – 00:44", "SINGLE"),
        (5, "Penutup", "Bersama Membangun Indonesia", "00:44 – 01:00", "SINGLE"),
    ]
    for number, title, detail, timing, mode in samples:
        item = QListWidgetItem(
            f"{number:02d}.  {title}     {mode}\n{detail}\n{timing}"
        )
        item.setSizeHint(item.sizeHint().expandedTo(item.sizeHint()))
        widget.addItem(item)
    widget.setCurrentRow(0)
    return widget


def _preview_widget(mode: str) -> tuple[Any, Any, Any]:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSlider,
        QVBoxLayout,
        QWidget,
    )

    outer = QWidget()
    layout = QVBoxLayout(outer)
    layout.setContentsMargins(8, 8, 8, 6)
    layout.setSpacing(6)
    header = QHBoxLayout()
    header.addWidget(QLabel("Pratinjau: 1920 × 1080 (16:9)"))
    header.addStretch(1)
    header.addWidget(QLabel("Sesuaikan     100%     ⛶"))
    layout.addLayout(header)

    frame = QFrame()
    frame.setStyleSheet(
        f"background:{COLORS.monitor_matte}; border:1px solid #111827;"
    )
    frame_layout = QVBoxLayout(frame)
    frame_layout.setContentsMargins(42, 24, 42, 24)
    canvas = QLabel()
    canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
    canvas.setMinimumSize(640, 360)
    canvas.setPixmap(scene_pixmap(mode, 1280, 720))
    canvas.setScaledContents(True)
    canvas.setStyleSheet("border:1px solid #CBD5E1; background:#F8FAFD;")
    frame_layout.addWidget(canvas, 1)
    layout.addWidget(frame, 1)

    transport = QHBoxLayout()
    transport.addWidget(QLabel("00:00:12:08  /  00:01:28:00"))
    transport.addStretch(1)
    for label in ["◀", "▶", "▶|", "🔊"]:
        transport.addWidget(QPushButton(label))
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setValue(34)
    transport.addWidget(slider, 1)
    layout.addLayout(transport)
    return outer, frame, canvas


def _overview_inspector() -> Any:
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(12)
    layout.addWidget(section_title("Project Overview"))

    project = QFrame()
    project.setProperty("panel", True)
    project_layout = QVBoxLayout(project)
    name = QLabel("Dokumenter_Indonesia")
    name.setStyleSheet("font-size:15px; font-weight:700;")
    project_layout.addWidget(name)
    for text in [
        "Resolusi        1920 × 1080 (16:9)",
        "Frame Rate      30 fps",
        "Durasi          01:00 (5 scene)",
        "Warna           SDR (Rec.709)",
    ]:
        project_layout.addWidget(muted_label(text))
    layout.addWidget(project)

    layout.addWidget(section_title("Scene Terpilih"))
    scene = QFrame()
    scene.setProperty("panel", True)
    scene_layout = QVBoxLayout(scene)
    scene_title = QLabel("01.  Pembukaan")
    scene_title.setStyleSheet("font-weight:700;")
    scene_layout.addWidget(scene_title)
    scene_layout.addWidget(muted_label("Indonesia: Negeri Kepulauan"))
    scene_layout.addWidget(muted_label("Durasi  00:00 – 00:08  (8,0 detik)"))
    layout.addWidget(scene)

    layout.addWidget(section_title("Aset pada Scene"))
    for label, count in [("Video", 2), ("Gambar", 1), ("Teks", 2), ("Audio", 1), ("Subtitle", 1)]:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addStretch(1)
        row.addWidget(muted_label(str(count)))
        row.addWidget(QLabel("›"))
        layout.addLayout(row)
    layout.addStretch(1)
    return widget


def _layout_inspector(mode: str) -> Any:
    from PySide6.QtWidgets import (
        QComboBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.addWidget(section_title("Detail Scene Terpilih" if mode == "double" else "Detail Aset"))
    target = "Scene 02 · A032 + A033" if mode == "double" else "A014 · READY"
    target_label = QLabel(target)
    target_label.setStyleSheet("font-size:14px; font-weight:700;")
    layout.addWidget(target_label)

    form = QFormLayout()
    mode_box = QComboBox()
    mode_box.addItems(["DOUBLE" if mode == "double" else "SINGLE"])
    form.addRow("Mode Layout", mode_box)
    if mode == "double":
        spacing = QSpinBox()
        spacing.setRange(0, 200)
        spacing.setValue(80)
        form.addRow("Jarak Pasangan", spacing)
    for label, value in [("Posisi X", 960), ("Posisi Y", 540), ("Skala", 84)]:
        spin = QSpinBox()
        spin.setRange(-2000, 2000)
        spin.setValue(value)
        form.addRow(label, spin)
    fit = QComboBox()
    fit.addItems(["Pertahankan Rasio", "Fit", "Fill", "Original"])
    form.addRow("Fit", fit)
    layout.addLayout(form)

    if mode == "double":
        layout.addWidget(section_title("Daftar Layer (2)"))
        layout.addWidget(QLabel("A032   ● terlihat"))
        layout.addWidget(QLabel("A033   ● terlihat"))
    row = QHBoxLayout()
    row.addWidget(QPushButton("Reset Layout"))
    row.addWidget(make_primary_button("Terapkan"))
    layout.addLayout(row)
    layout.addStretch(1)
    return widget


def _subtitle_inspector() -> Any:
    from PySide6.QtWidgets import (
        QCheckBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    tabs = QTabWidget()
    text_page = QWidget()
    layout = QVBoxLayout(text_page)
    header = QHBoxLayout()
    header.addWidget(section_title("Daftar Subtitle (8 cue)"))
    header.addStretch(1)
    header.addWidget(QPushButton("＋ Tambah Cue"))
    layout.addLayout(header)
    cue_list = QListWidget()
    cues = [
        "1   00:00:00:00 → 00:00:04:12\nPagi yang cerah di desa Bromo...",
        "2   00:00:04:12 → 00:00:08:20\nIa melihat bunga berwarna-warni...",
        "3   00:00:08:10 → 00:00:12:00  ⚠\nLalu melompat ke arah pagar kayu...",
        "4   00:00:12:00 → 00:00:16:15\nUdara segar membuatnya bersemangat.",
    ]
    for cue in cues:
        cue_list.addItem(QListWidgetItem(cue))
    cue_list.setCurrentRow(2)
    layout.addWidget(cue_list, 1)
    edit_header = QHBoxLayout()
    edit_header.addWidget(section_title("Edit Cue"))
    edit_header.addStretch(1)
    warning = QLabel("⚠ Tumpang tindih dengan cue sebelumnya")
    warning.setStyleSheet("color:#B45309; background:#FEF3C7; padding:4px 8px;")
    edit_header.addWidget(warning)
    layout.addLayout(edit_header)
    text = QTextEdit("Lalu melompat ke arah pagar kayu dengan lincah.")
    text.setMaximumHeight(74)
    layout.addWidget(text)
    form = QFormLayout()
    form.addRow("Waktu Mulai (IN)", QLineEdit("00:00:08:10"))
    form.addRow("Waktu Selesai (OUT)", QLineEdit("00:00:12:00"))
    layout.addLayout(form)
    row = QHBoxLayout()
    row.addWidget(QPushButton("Pisah Cue"))
    row.addWidget(QPushButton("Gabung"))
    row.addWidget(QPushButton("Muat Ulang SRT"))
    layout.addLayout(row)
    layout.addWidget(QCheckBox("Kunci timing"))
    tabs.addTab(text_page, "Teks")
    tabs.addTab(QWidget(), "Gaya")
    tabs.addTab(QWidget(), "Animasi")
    return tabs


def _ai_placeholder() -> Any:
    from PySide6.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QWidget

    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(section_title("AI Agent"))
    layout.addWidget(muted_label("Scope: Seluruh Proyek · Scene 08 · A014"))
    for text in [
        "Acak animasi scene 1–10",
        "Cari aset missing",
        "Atur scene ini lebih rapat",
    ]:
        layout.addWidget(QPushButton(text))
    layout.addStretch(1)
    layout.addWidget(QLineEdit("Tulis perintah..."))
    layout.addWidget(make_primary_button("Kirim"))
    return widget


def _timeline_widget() -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

    outer = QFrame()
    outer.setProperty("panel", True)
    layout = QVBoxLayout(outer)
    layout.setContentsMargins(6, 6, 6, 6)
    layout.addWidget(
        QLabel("Timeline     00:00:00     00:00:20     00:00:40     00:01:00     00:01:20")
    )
    grid = QGridLayout()
    grid.setHorizontalSpacing(3)
    grid.setVerticalSpacing(4)
    tracks = [
        ("V2  Elemen", ["A008", "", "A014", ""]),
        ("V1  Video", ["Sc01  Sc02", "Sc03  Sc04", "Sc05  Sc06", "Sc07"]),
        ("A1  Audio", ["background-music.mp3", "", "", ""]),
        ("A2  Narasi", ["narasi-001.mp3", "", "", ""]),
        (
            "S1  Subtitle",
            ["Pagi yang cerah...", "Seekor kucing...", "Ia melihat bunga...", "Lalu melompat..."],
        ),
        ("B1  Background", ["background_white_paper.jpg", "", "", ""]),
    ]
    for row_index, (name, blocks) in enumerate(tracks):
        name_label = QLabel(name)
        name_label.setMinimumWidth(92)
        grid.addWidget(name_label, row_index, 0)
        for column_index, block in enumerate(blocks, start=1):
            label = QLabel(block)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if row_index in {0, 1, 4}:
                color = "#DBEAFE"
            elif row_index == 2:
                color = "#DCFCE7"
            elif row_index == 3:
                color = "#F3E8FF"
            else:
                color = "#F5F1EA"
            label.setStyleSheet(
                f"background:{color}; border:1px solid #CBD5E1; "
                "border-radius:4px; padding:7px;"
            )
            grid.addWidget(label, row_index, column_index)
    layout.addLayout(grid, 1)
    return outer


def create_editor_shell(mode: str = "overview") -> EditorShellParts:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLineEdit, QSplitter, QTabWidget, QVBoxLayout, QWidget

    root = QWidget()
    vertical = QVBoxLayout(root)
    vertical.setContentsMargins(0, 0, 0, 0)
    vertical.setSpacing(0)
    upper = QSplitter(Qt.Orientation.Horizontal)

    left = QTabWidget()
    left.setMinimumWidth(METRICS.left_min_w)
    left.setMaximumWidth(520)
    left.addTab(_scene_list(), "Scene")
    assets_page = QWidget()
    assets_layout = QVBoxLayout(assets_page)
    assets_layout.setContentsMargins(8, 8, 8, 8)
    search = QLineEdit()
    search.setPlaceholderText("Cari Asset ID...")
    assets_layout.addWidget(search)
    assets_layout.addWidget(_asset_grid(), 1)
    left.addTab(assets_page, "Aset")
    left.setCurrentIndex(0 if mode == "overview" else 1)

    preview_mode = mode if mode in {"single", "double", "subtitle"} else "overview"
    preview, frame, preview_label = _preview_widget(preview_mode)

    right = QTabWidget()
    right.setMinimumWidth(300)
    right.setMaximumWidth(METRICS.right_max_w)
    if mode == "subtitle":
        right.addTab(_subtitle_inspector(), "Subtitle")
        right.addTab(_ai_placeholder(), "AI Agent")
    elif mode == "overview":
        right.addTab(_overview_inspector(), "Layout")
        right.addTab(QWidget(), "Animasi")
        right.addTab(_ai_placeholder(), "AI Agent")
    else:
        right.addTab(_layout_inspector(mode), "Layout")
        right.addTab(QWidget(), "Animasi")
        right.addTab(_ai_placeholder(), "AI Agent")

    upper.addWidget(left)
    upper.addWidget(preview)
    upper.addWidget(right)
    upper.setSizes([METRICS.left_ref_w, 1260, METRICS.right_ref_w])

    timeline = _timeline_widget()
    timeline.setMinimumHeight(METRICS.timeline_min_h)
    outer = QSplitter(Qt.Orientation.Vertical)
    outer.addWidget(upper)
    outer.addWidget(timeline)
    outer.setSizes([660, METRICS.timeline_ref_h])
    vertical.addWidget(outer, 1)

    status = muted_label(
        "✓ Project siap   ·   Auto-saved 10:24:18   ·   ● Provider: Gemini (Online)   ·   "
        "Scene 01/05   ·   1920 × 1080   ·   30 fps   ·   00:00:12:08 / 00:01:28:00"
    )
    status.setMinimumHeight(METRICS.status_h)
    vertical.addWidget(status)
    return EditorShellParts(root, left, frame, preview_label, right, timeline, status)
