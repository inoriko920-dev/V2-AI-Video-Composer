from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from aavc.domain.project.models import ProjectState
from aavc.presentation.project_view import (
    AssetView,
    SceneView,
    build_asset_views,
    build_project_summary,
    build_scene_views,
    format_duration,
)
from aavc.presentation.scene_inspector import (
    build_scene_inspector_view,
    scene_index_for_number,
)
from aavc.presentation.scene_preview import ScenePreviewPlan, build_scene_preview_plan
from aavc.presentation.timeline_view import TimelinePlan, build_timeline_plan
from aavc.presentation.widgets.common import make_primary_button, muted_label, section_title
from aavc.presentation.widgets.editor_shell import create_editor_shell, remove_tabs_by_label


def _scene_page(scenes: tuple[SceneView, ...]) -> Any:
    from PySide6.QtWidgets import QListWidget, QListWidgetItem

    widget = QListWidget()
    widget.setSpacing(4)
    for scene in scenes:
        assets = ", ".join(scene.asset_ids)
        item = QListWidgetItem(
            f"{scene.scene_number:02d}. Scene {scene.scene_number:02d}     {scene.mode}\n"
            f"Aset: {assets}\nDurasi: {scene.duration_label}"
        )
        widget.addItem(item)
    return widget


def _asset_page(assets: tuple[AssetView, ...]) -> Any:
    from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(8, 8, 8, 8)
    ready = sum(asset.status == "READY" for asset in assets)
    layout.addWidget(
        QLabel(
            f"Aset project: {len(assets)} · READY {ready} · "
            f"Belum READY {len(assets) - ready}"
        )
    )

    listing = QListWidget()
    listing.setSpacing(3)
    for asset in assets:
        status_icon = "✓" if asset.status == "READY" else "⚠"
        quote = asset.source_quote.replace("\\N", " ")
        item = QListWidgetItem(
            f"{status_icon} {asset.asset_id} · {asset.status}\n"
            f"{asset.file_label}\n{quote}"
        )
        listing.addItem(item)
    layout.addWidget(listing, 1)
    return page


def _overview_page(project: ProjectState) -> Any:
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

    summary = build_project_summary(project)
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(12)
    layout.addWidget(section_title("Project Overview"))

    card = QFrame()
    card.setProperty("panel", True)
    card_layout = QVBoxLayout(card)
    title = QLabel(summary.title)
    title.setStyleSheet("font-size:15px; font-weight:700;")
    card_layout.addWidget(title)
    for text in [
        f"Resolusi        {summary.resolution}",
        f"Frame Rate      {summary.fps} fps",
        f"Durasi          {summary.duration_label} ({summary.scene_count} scene)",
        f"Aset             {summary.ready_count}/{summary.asset_count} READY",
        f"Narasi           {summary.narration_label}",
        f"Subtitle         {summary.subtitle_label}",
    ]:
        card_layout.addWidget(muted_label(text))
    layout.addWidget(card)

    if summary.not_ready_count:
        warning = QLabel(f"⚠ {summary.not_ready_count} aset belum READY")
        warning.setStyleSheet(
            "color:#B45309; background:#FFFBEB; border:1px solid #FDE68A; "
            "border-radius:6px; padding:8px; font-weight:650;"
        )
        layout.addWidget(warning)
    else:
        ready = QLabel("✓ Semua aset READY")
        ready.setStyleSheet(
            "color:#15803D; background:#F0FDF4; border:1px solid #BBF7D0; "
            "border-radius:6px; padding:8px; font-weight:650;"
        )
        layout.addWidget(ready)

    layout.addStretch(1)
    return page


def _scene_inspector_page(
    project: ProjectState,
    scene_number: int,
    on_set_scene_duration: Callable[[int, float], None] | None,
) -> Any:
    from PySide6.QtWidgets import (
        QDoubleSpinBox,
        QFrame,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    view = build_scene_inspector_view(project, scene_number)
    summary = build_project_summary(project)
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(10)

    layout.addWidget(section_title("Scene Terpilih"))
    card = QFrame()
    card.setProperty("panel", True)
    card_layout = QVBoxLayout(card)
    heading = QLabel(f"Scene {view.scene_number:02d} · {view.mode}")
    heading.setStyleSheet("font-size:15px; font-weight:700;")
    card_layout.addWidget(heading)
    card_layout.addWidget(muted_label(f"Aset: {', '.join(view.asset_ids)}"))
    card_layout.addWidget(muted_label(f"Durasi saat ini: {format_duration(view.duration_seconds)}"))
    layout.addWidget(card)

    layout.addWidget(section_title("Durasi Scene"))
    duration = QDoubleSpinBox()
    duration.setRange(0.001, 86400.0)
    duration.setDecimals(3)
    duration.setSingleStep(0.1)
    duration.setSuffix(" detik")
    duration.setValue(view.duration_seconds)
    layout.addWidget(duration)

    apply_button: QPushButton = make_primary_button("Terapkan Durasi")
    if on_set_scene_duration is None:
        apply_button.setEnabled(False)
        apply_button.setToolTip("Perubahan durasi belum terhubung pada sesi ini.")
    else:
        apply_button.clicked.connect(
            lambda: on_set_scene_duration(view.scene_number, float(duration.value()))
        )
    layout.addWidget(apply_button)

    note = QLabel(
        "Perubahan masuk Undo/Redo. Setelah selesai, klik Simpan untuk menulis perubahan ke file project."
    )
    note.setWordWrap(True)
    note.setStyleSheet("color:#64748B; font-size:9px;")
    layout.addWidget(note)

    layout.addWidget(section_title("Project"))
    layout.addWidget(muted_label(f"Total durasi: {summary.duration_label}"))
    layout.addWidget(muted_label(f"Resolusi: {summary.resolution} · {summary.fps} fps"))
    layout.addStretch(1)
    return page


def _replace_layout_tab(tab_widget: Any, replacement: Any) -> None:
    previous = tab_widget.widget(0)
    tab_widget.removeTab(0)
    tab_widget.insertTab(0, replacement, "Layout")
    tab_widget.setCurrentIndex(0)
    if previous is not None:
        previous.deleteLater()


def _draw_missing_asset(painter: Any, asset: Any, width: int, height: int) -> None:
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QPen

    box_w = max(160, int(width * asset.max_width * 0.82))
    box_h = max(120, int(height * asset.max_height * 0.72))
    x = int(width * asset.anchor_x - box_w / 2)
    y = int(height * asset.anchor_y - box_h / 2)
    rect = QRectF(x, y, box_w, box_h)
    painter.setPen(QPen(QColor("#D97706"), 3))
    painter.setBrush(QColor("#FFFBEB"))
    painter.drawRoundedRect(rect, 12, 12)
    painter.setPen(QColor("#92400E"))
    painter.drawText(
        rect,
        int(Qt.AlignmentFlag.AlignCenter),
        f"{asset.asset_id}\n{asset.status}\nFile tidak tersedia",
    )


def _render_scene_pixmap(plan: ScenePreviewPlan, width: int = 1280, height: int = 720) -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPainter, QPixmap

    canvas = QPixmap(width, height)
    canvas.fill(QColor("#F4F7FB"))
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    for asset in plan.assets:
        if asset.status != "READY" or asset.path is None:
            _draw_missing_asset(painter, asset, width, height)
            continue
        source = QPixmap(asset.path)
        if source.isNull():
            _draw_missing_asset(painter, asset, width, height)
            continue

        max_width = max(1, int(width * asset.max_width))
        max_height = max(1, int(height * asset.max_height))
        scaled = source.scaled(
            max_width,
            max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = int(width * asset.anchor_x - scaled.width() / 2)
        y = int(height * asset.anchor_y - scaled.height() / 2)
        painter.drawPixmap(x, y, scaled)

    painter.end()
    return canvas


def _clear_layout(layout: Any) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif child_layout is not None:
            _clear_layout(child_layout)


def _configure_live_timeline(
    timeline: Any,
    plan: TimelinePlan,
    on_scene_clicked: Any,
) -> tuple[Any, ...]:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

    layout = timeline.layout()
    if layout is None:
        layout = QVBoxLayout(timeline)
    else:
        _clear_layout(layout)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)

    header = QHBoxLayout()
    title = QLabel("Timeline Scene · Read-only")
    title.setStyleSheet("font-weight:700;")
    header.addWidget(title)
    header.addStretch(1)
    header.addWidget(QLabel(f"Total {format_duration(plan.total_duration_seconds)}"))
    layout.addLayout(header)

    if not plan.segments:
        empty = QLabel("Project belum memiliki scene.")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(empty, 1)
        return ()

    track = QHBoxLayout()
    track.setSpacing(3)
    name = QLabel("V1  Scene")
    name.setMinimumWidth(92)
    name.setStyleSheet("font-weight:650;")
    track.addWidget(name)

    group = QButtonGroup(timeline)
    group.setExclusive(True)
    buttons: list[QPushButton] = []
    for segment in plan.segments:
        button = QPushButton(
            f"Sc{segment.scene_number:02d}\n{format_duration(segment.duration_seconds)}"
        )
        button.setCheckable(True)
        button.setMinimumWidth(44)
        button.setToolTip(
            f"Scene {segment.scene_number:02d} · {segment.mode} · "
            f"{format_duration(segment.start_seconds)} → "
            f"{format_duration(segment.end_seconds)}\n"
            "Timeline read-only: klik untuk memilih scene."
        )
        button.setStyleSheet(
            "QPushButton {background:#DBEAFE; border:1px solid #93C5FD; "
            "border-radius:4px; padding:6px 4px;} "
            "QPushButton:checked {background:#BFDBFE; border:2px solid #2563EB; "
            "font-weight:700;}"
        )
        group.addButton(button, segment.scene_index)
        stretch = max(1, int(round(segment.duration_seconds * 1000)))
        track.addWidget(button, stretch)
        buttons.append(button)
    group.idClicked.connect(on_scene_clicked)
    layout.addLayout(track, 1)

    note = QLabel(
        "Lebar blok mengikuti durasi scene. Drag/drop, trim, split, resize, dan scrub belum aktif."
    )
    note.setStyleSheet("color:#64748B; font-size:9px;")
    layout.addWidget(note)
    timeline.setEnabled(True)
    timeline.setToolTip("Timeline scene berasal dari ProjectState aktif dan bersifat read-only.")
    return tuple(buttons)


def create_live_editor_overview(
    project: ProjectState,
    *,
    on_set_scene_duration: Callable[[int, float], None] | None = None,
    selected_scene_number: int | None = None,
    on_scene_selected: Callable[[int], None] | None = None,
) -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel, QPushButton, QSlider

    parts = create_editor_shell("overview")
    remove_tabs_by_label(parts.right_tabs, {"Animasi", "AI Agent"})
    scenes = build_scene_views(project)
    assets = build_asset_views(project)
    summary = build_project_summary(project)
    scene_list = _scene_page(scenes)

    parts.left_tabs.clear()
    parts.left_tabs.addTab(scene_list, "Scene")
    parts.left_tabs.addTab(_asset_page(assets), "Aset")
    parts.left_tabs.setCurrentIndex(0)

    parts.right_tabs.removeTab(0)
    parts.right_tabs.insertTab(0, _overview_page(project), "Layout")
    parts.right_tabs.setCurrentIndex(0)

    preview_header = QLabel()
    preview_header.setStyleSheet(
        "color:#E2E8F0; background:#111827; border:none; padding:6px 10px; "
        "font-weight:650;"
    )
    frame_layout = parts.preview_frame.layout()
    if frame_layout is not None:
        frame_layout.insertWidget(0, preview_header)

    parts.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    parts.preview_label.setStyleSheet(
        "border:1px solid #CBD5E1; background:#F4F7FB; color:#64748B;"
    )

    preview_outer = parts.preview_frame.parentWidget()
    if preview_outer is not None:
        for button in preview_outer.findChildren(QPushButton):
            button.setEnabled(False)
            button.setToolTip("Playback preview belum diaktifkan pada tahap ini.")
        for slider in preview_outer.findChildren(QSlider):
            slider.setEnabled(False)
            slider.setToolTip("Scrubbing preview belum diaktifkan pada tahap ini.")

    timeline_plan = build_timeline_plan(project)
    timeline_buttons = _configure_live_timeline(
        parts.timeline,
        timeline_plan,
        scene_list.setCurrentRow,
    )

    def show_scene(row: int) -> None:
        for index, button in enumerate(timeline_buttons):
            button.setChecked(index == row)
        if row < 0 or row >= len(project.scenes):
            preview_header.setText("Tidak ada scene terpilih")
            parts.preview_label.clear()
            parts.preview_label.setText("Pilih scene untuk melihat preview statis.")
            _replace_layout_tab(parts.right_tabs, _overview_page(project))
            return

        scene = project.scenes[row]
        if on_scene_selected is not None:
            on_scene_selected(scene.scene_number)
        _replace_layout_tab(
            parts.right_tabs,
            _scene_inspector_page(project, scene.scene_number, on_set_scene_duration),
        )
        plan = build_scene_preview_plan(project, scene)
        preview_header.setText(
            f"Scene {scene.scene_number:02d} · {scene.mode} · "
            f"{project.width} × {project.height} · {format_duration(scene.duration_seconds)}"
        )
        parts.preview_label.setPixmap(_render_scene_pixmap(plan))
        parts.preview_label.setToolTip(
            "Preview statis memakai placement yang sama dengan render engine. "
            "Playback, animasi, audio, subtitle overlay, dan scrub timeline belum aktif."
        )

    scene_list.currentRowChanged.connect(show_scene)
    selected_index = scene_index_for_number(project, selected_scene_number)
    if selected_index >= 0:
        scene_list.setCurrentRow(selected_index)
    else:
        show_scene(-1)

    status = (
        "✓ Project siap"
        if summary.not_ready_count == 0
        else f"⚠ {summary.not_ready_count} aset belum READY"
    )
    source_name = Path(project.source_docx).name
    parts.status_label.setText(
        f"{status}   ·   {project.title}   ·   {summary.scene_count} scene   ·   "
        f"{summary.resolution}   ·   {summary.fps} fps   ·   {summary.duration_label}   ·   "
        f"Source: {source_name}"
    )
    return parts.root
