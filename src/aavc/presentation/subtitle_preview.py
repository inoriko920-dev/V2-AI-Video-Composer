from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aavc.domain.project.models import SubtitleAnimationSettings, SubtitleStyle
from aavc.subtitles.srt import SubtitleCue


@dataclass(frozen=True, slots=True)
class SubtitlePreviewTransform:
    opacity: float = 1.0
    scale: float = 1.0
    vertical_offset: float = 0.0


def active_subtitle_cue(
    cues: tuple[SubtitleCue, ...],
    time_seconds: float,
) -> SubtitleCue | None:
    """Return the SRT cue active at a global project time."""

    current = max(0.0, float(time_seconds))
    for cue in cues:
        if cue.start_seconds <= current < cue.end_seconds:
            return cue
    return None


def subtitle_animation_transform(
    cue: SubtitleCue,
    time_seconds: float,
    animation: SubtitleAnimationSettings,
) -> SubtitlePreviewTransform:
    """Approximate the current ASS animation tags used by the final renderer."""

    start = float(cue.start_seconds)
    end = max(start, float(cue.end_seconds))
    current = float(time_seconds)
    if current < start or current >= end or end <= start:
        return SubtitlePreviewTransform(opacity=0.0)

    local = current - start
    remaining = end - current
    enter_seconds = max(0, int(animation.enter_duration_ms)) / 1000.0
    exit_seconds = max(0, int(animation.exit_duration_ms)) / 1000.0

    enter_alpha = 1.0 if enter_seconds <= 0 else max(0.0, min(1.0, local / enter_seconds))
    exit_alpha = 1.0 if exit_seconds <= 0 else max(0.0, min(1.0, remaining / exit_seconds))
    opacity = min(enter_alpha, exit_alpha)

    scale = 1.05 if animation.preset == "Pop" else 1.0
    vertical_offset = 0.0
    if animation.preset == "Slide Up" and enter_seconds > 0:
        enter_progress = max(0.0, min(1.0, local / enter_seconds))
        vertical_offset = 80.0 * (1.0 - enter_progress)

    return SubtitlePreviewTransform(
        opacity=opacity,
        scale=scale,
        vertical_offset=vertical_offset,
    )


def _alignment_flags(alignment: int) -> Any:
    from PySide6.QtCore import Qt

    horizontal = {
        1: Qt.AlignmentFlag.AlignLeft,
        2: Qt.AlignmentFlag.AlignHCenter,
        3: Qt.AlignmentFlag.AlignRight,
        4: Qt.AlignmentFlag.AlignLeft,
        5: Qt.AlignmentFlag.AlignHCenter,
        6: Qt.AlignmentFlag.AlignRight,
        7: Qt.AlignmentFlag.AlignLeft,
        8: Qt.AlignmentFlag.AlignHCenter,
        9: Qt.AlignmentFlag.AlignRight,
    }.get(alignment, Qt.AlignmentFlag.AlignHCenter)
    vertical = {
        1: Qt.AlignmentFlag.AlignBottom,
        2: Qt.AlignmentFlag.AlignBottom,
        3: Qt.AlignmentFlag.AlignBottom,
        4: Qt.AlignmentFlag.AlignVCenter,
        5: Qt.AlignmentFlag.AlignVCenter,
        6: Qt.AlignmentFlag.AlignVCenter,
        7: Qt.AlignmentFlag.AlignTop,
        8: Qt.AlignmentFlag.AlignTop,
        9: Qt.AlignmentFlag.AlignTop,
    }.get(alignment, Qt.AlignmentFlag.AlignBottom)
    return horizontal | vertical | Qt.TextFlag.TextWordWrap


def overlay_subtitle_pixmap(
    pixmap: Any,
    cue: SubtitleCue | None,
    style: SubtitleStyle,
    *,
    project_width: int,
    project_height: int,
    animation: SubtitleAnimationSettings | None = None,
    time_seconds: float | None = None,
) -> Any:
    """Paint a conservative subtitle preview onto an existing pixmap copy."""

    if cue is None or pixmap.isNull():
        return pixmap

    from PySide6.QtCore import QRect, Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPen

    transform = (
        subtitle_animation_transform(cue, time_seconds, animation)
        if animation is not None and time_seconds is not None
        else SubtitlePreviewTransform()
    )
    if transform.opacity <= 0:
        return pixmap

    result = pixmap.copy()
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setOpacity(max(0.0, min(1.0, transform.opacity)))

    height_scale = result.height() / max(1, int(project_height))
    width_scale = result.width() / max(1, int(project_width))
    scale = min(height_scale, width_scale)
    font = QFont(style.font_family)
    font.setPixelSize(
        max(8, int(round(style.font_size * scale * transform.scale)))
    )
    font.setBold(style.preset_name in {"Dokumenter", "Social"})
    painter.setFont(font)

    margin_h = max(8, int(round(80 * width_scale)))
    margin_v = max(0, int(round(style.margin_v * height_scale)))
    vertical_offset = int(round(transform.vertical_offset * height_scale))
    rect = QRect(
        margin_h,
        margin_v + vertical_offset,
        max(1, result.width() - margin_h * 2),
        max(1, result.height() - margin_v * 2),
    )
    flags = _alignment_flags(style.alignment)
    text = cue.text.replace("\\N", "\n")
    bounds = painter.fontMetrics().boundingRect(rect, int(flags), text)

    if style.background_box and style.background_opacity > 0:
        padding = max(4, int(round(8 * scale)))
        background = bounds.adjusted(-padding, -padding, padding, padding)
        opacity = max(0, min(100, int(style.background_opacity)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, int(round(255 * opacity / 100))))
        painter.drawRoundedRect(background, padding, padding)

    fill = QColor(style.fill_color)
    outline = QColor(style.outline_color)
    if not fill.isValid():
        fill = QColor("#FFFFFF")
    if not outline.isValid():
        outline = QColor("#111111")

    shadow_px = max(0, int(round(style.shadow * scale)))
    if shadow_px:
        painter.setPen(QColor(0, 0, 0, 160))
        painter.drawText(rect.translated(shadow_px, shadow_px), int(flags), text)

    outline_px = max(0, min(8, int(round(style.outline_width * scale))))
    if outline_px:
        painter.setPen(QPen(outline, max(1, outline_px)))
        for dx, dy in (
            (-outline_px, 0),
            (outline_px, 0),
            (0, -outline_px),
            (0, outline_px),
        ):
            painter.drawText(rect.translated(dx, dy), int(flags), text)

    painter.setPen(fill)
    painter.drawText(rect, int(flags), text)
    painter.end()
    return result
