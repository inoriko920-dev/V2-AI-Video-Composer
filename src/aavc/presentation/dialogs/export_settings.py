from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from aavc.application.services.export_service import ExportOptions
from aavc.presentation.widgets.common import make_primary_button, muted_label, section_title

_CODEC_BY_LABEL = {
    "MP4 (H.264)": "libx264",
    "MP4 (H.265)": "libx265",
}
_PRESET_BY_LABEL = {
    "Kualitas Tinggi (Rekomendasi)": "slow",
    "YouTube Clean": "medium",
    "Documentary Crisp": "medium",
}
_RESOLUTION_BY_LABEL = {
    "1920 × 1080 (Full HD)": (1920, 1080),
    "2560 × 1440": (2560, 1440),
    "3840 × 2160 (4K)": (3840, 2160),
}
_FPS_BY_LABEL = {"30 fps": 30, "60 fps": 60}
_SHARPEN_BY_LABEL = {
    "Normal": 0.0,
    "Tajam Ringan": 0.10,
    "Documentary Crisp": 0.18,
}


def quality_slider_to_crf(value: int) -> int:
    clamped = max(0, min(100, value))
    return round(30 - (clamped * 15 / 100))


def build_export_options(
    *,
    output_directory: str,
    output_name: str,
    format_label: str,
    preset_label: str,
    resolution_label: str,
    fps_label: str,
    quality_value: int,
    sharpen_label: str,
    burn_subtitles: bool,
) -> ExportOptions:
    directory_text = output_directory.strip()
    name = output_name.strip()
    if not directory_text:
        raise ValueError("Lokasi output wajib diisi")
    if not name:
        raise ValueError("Nama file output wajib diisi")
    # The name input is a filename, not another path selector. Windows treats
    # backslashes, device names and special characters differently from POSIX,
    # so validate portably before joining the chosen output directory.
    if any(
        character in '<>:"/|?*' or character == chr(92) or ord(character) < 32
        for character in name
    ):
        raise ValueError("Nama file output tidak boleh berisi path atau karakter terlarang")
    stem = name[:-4] if name.lower().endswith(".mp4") else name
    device_name = stem.split(".", 1)[0].upper()
    if (
        not stem.strip(". ")
        or device_name in {"CON", "PRN", "AUX", "NUL"}
        or re.fullmatch(r"(?:COM|LPT)[1-9]", device_name)
    ):
        raise ValueError("Nama file output tidak valid atau khusus Windows")

    filename = name if name.lower().endswith(".mp4") else f"{name}.mp4"
    width, height = _RESOLUTION_BY_LABEL[resolution_label]
    return ExportOptions(
        output_path=str(Path(directory_text).expanduser() / filename),
        video_codec=_CODEC_BY_LABEL[format_label],
        encoder_preset=_PRESET_BY_LABEL[preset_label],
        crf=quality_slider_to_crf(quality_value),
        width=width,
        height=height,
        fps=_FPS_BY_LABEL[fps_label],
        sharpen_amount=_SHARPEN_BY_LABEL[sharpen_label],
        burn_subtitles=burn_subtitles,
    )


def create_export_dialog(
    parent: Any = None,
    *,
    default_directory: str = r"D:\Video Projects\Liburan ke Bromo\Hasil Akhir",
    default_name: str = "Liburan ke Bromo - Final",
    on_render: Callable[[ExportOptions], bool] | None = None,
) -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QFormLayout,
        QHBoxLayout,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSlider,
        QVBoxLayout,
    )

    dialog = QDialog(parent)
    dialog.setWindowTitle("Ekspor Video")
    dialog.resize(980, 690)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.addWidget(section_title("Ekspor Video"))
    layout.addWidget(
        muted_label(
            "Atur kualitas final. Preview boleh lebih ringan; render final menggunakan kualitas penuh."
        )
    )

    form = QFormLayout()
    output_path = QLineEdit(default_directory)
    output_name = QLineEdit(default_name)
    format_box = QComboBox()
    format_box.addItems(list(_CODEC_BY_LABEL))
    preset = QComboBox()
    preset.addItems(list(_PRESET_BY_LABEL))
    resolution = QComboBox()
    resolution.addItems(list(_RESOLUTION_BY_LABEL))
    fps = QComboBox()
    fps.addItems(list(_FPS_BY_LABEL))
    form.addRow("Lokasi Output", output_path)
    form.addRow("Nama File", output_name)
    form.addRow("Format", format_box)
    form.addRow("Preset", preset)
    form.addRow("Resolusi", resolution)
    form.addRow("Frame Rate", fps)
    layout.addLayout(form)

    quality = QSlider(Qt.Orientation.Horizontal)
    quality.setRange(0, 100)
    quality.setValue(78)
    form2 = QFormLayout()
    form2.addRow("Bitrate / Kualitas", quality)
    sharpen = QComboBox()
    sharpen.addItems(list(_SHARPEN_BY_LABEL))
    form2.addRow("Ketajaman Video", sharpen)
    subtitle = QComboBox()
    subtitle.addItems(["Sertakan Subtitle (Burn-in ke Video)", "Tanpa Subtitle"])
    form2.addRow("Subtitle", subtitle)
    layout.addLayout(form2)

    layout.addStretch(1)

    footer = QHBoxLayout()
    cancel = QPushButton("Batal")
    cancel.clicked.connect(dialog.reject)
    render = make_primary_button("Mulai Render")

    def submit_render() -> None:
        try:
            options = build_export_options(
                output_directory=output_path.text(),
                output_name=output_name.text(),
                format_label=format_box.currentText(),
                preset_label=preset.currentText(),
                resolution_label=resolution.currentText(),
                fps_label=fps.currentText(),
                quality_value=quality.value(),
                sharpen_label=sharpen.currentText(),
                burn_subtitles=subtitle.currentIndex() == 0,
            )
        except (KeyError, ValueError) as error:
            QMessageBox.warning(dialog, "Pengaturan ekspor tidak valid", str(error))
            return

        if on_render is None:
            QMessageBox.information(
                dialog,
                "Render belum terhubung",
                "Tidak ada render callback untuk dialog ini.",
            )
            return
        if on_render(options):
            dialog.accept()

    render.clicked.connect(submit_render)
    footer.addStretch(1)
    footer.addWidget(cancel)
    footer.addWidget(render)
    layout.addLayout(footer)
    return dialog
