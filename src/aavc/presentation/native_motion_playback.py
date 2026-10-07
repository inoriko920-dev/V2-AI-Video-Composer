from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from aavc.animation.contract import (
    ResolvedAnimationKeyframeContract,
    validate_project_animation_contract,
)
from aavc.domain.project.models import AnimationAssignment, ProjectState
from aavc.presentation.motion_preview import (
    native_motion_preview_offset,
    native_visual_preview_blur_sigma,
    native_visual_preview_crop,
    native_visual_preview_glow,
    native_visual_preview_opacity,
    native_visual_preview_rotation,
    native_visual_preview_scale,
    native_visual_preview_shadow,
    preview_narration_seconds,
    preview_neighbor_scene_index,
    preview_scrub_seconds,
    preview_timecode,
)
from aavc.presentation.scene_preview import ScenePreviewPlan, build_scene_preview_plan
from aavc.presentation.subtitle_preview import (
    active_subtitle_cue,
    overlay_subtitle_pixmap,
)
from aavc.subtitles.srt import SubtitleCue, parse_srt


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


def _rotate_pixmap_same_size(pixmap: Any, angle_degrees: float) -> Any:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPainter, QPixmap

    if abs(angle_degrees) < 1e-9:
        return pixmap
    rotated = QPixmap(pixmap.size())
    rotated.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rotated)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.translate(rotated.width() / 2, rotated.height() / 2)
    painter.rotate(angle_degrees)
    painter.translate(-pixmap.width() / 2, -pixmap.height() / 2)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return rotated


def _clip_pixmap_visibility(pixmap: Any, crop: Any) -> Any:
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QPainter, QPixmap

    if (
        crop.left <= 0.0
        and crop.top <= 0.0
        and crop.right <= 0.0
        and crop.bottom <= 0.0
    ):
        return pixmap

    clipped = QPixmap(pixmap.size())
    clipped.fill(Qt.GlobalColor.transparent)
    painter = QPainter(clipped)
    width = pixmap.width()
    height = pixmap.height()
    left = width * crop.left
    top = height * crop.top
    visible_width = max(0.0, width * crop.visible_width)
    visible_height = max(0.0, height * crop.visible_height)
    painter.setClipRect(QRectF(left, top, visible_width, visible_height))
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return clipped


def _blur_pixmap_approx(pixmap: Any, sigma: float) -> Any:
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QPainter, QPixmap
    from PySide6.QtWidgets import (
        QGraphicsBlurEffect,
        QGraphicsPixmapItem,
        QGraphicsScene,
    )

    if sigma <= 0.01:
        return pixmap

    output = QPixmap(pixmap.size())
    output.fill(Qt.GlobalColor.transparent)
    scene = QGraphicsScene()
    source_rect = QRectF(0.0, 0.0, float(pixmap.width()), float(pixmap.height()))
    scene.setSceneRect(source_rect)
    item = QGraphicsPixmapItem(pixmap)
    effect = QGraphicsBlurEffect()
    effect.setBlurRadius(max(0.5, float(sigma) * 2.0))
    item.setGraphicsEffect(effect)
    scene.addItem(item)

    painter = QPainter(output)
    scene.render(painter, source_rect, source_rect)
    painter.end()
    return output


def _drop_shadow_pixmap_approx(
    pixmap: Any,
    *,
    color: str,
    alpha: float,
    blur_radius: float,
    offset: float,
) -> Any:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QColor, QPainter, QPixmap
    from PySide6.QtWidgets import (
        QGraphicsDropShadowEffect,
        QGraphicsPixmapItem,
        QGraphicsScene,
    )

    if alpha <= 0.001:
        return pixmap

    output = QPixmap(pixmap.size())
    output.fill(Qt.GlobalColor.transparent)
    scene = QGraphicsScene()
    source_rect = QRectF(0.0, 0.0, float(pixmap.width()), float(pixmap.height()))
    scene.setSceneRect(source_rect)
    item = QGraphicsPixmapItem(pixmap)
    effect = QGraphicsDropShadowEffect()
    effect_color = QColor(color)
    effect_color.setAlphaF(max(0.0, min(1.0, float(alpha))))
    effect.setColor(effect_color)
    effect.setBlurRadius(max(0.5, float(blur_radius) * 2.0))
    effect.setOffset(QPointF(float(offset), float(offset)))
    item.setGraphicsEffect(effect)
    scene.addItem(item)

    painter = QPainter(output)
    scene.render(painter, source_rect, source_rect)
    painter.end()
    return output


def render_native_motion_pixmap(
    plan: ScenePreviewPlan,
    assignments: tuple[AnimationAssignment, ...],
    *,
    time_seconds: float | None,
    width: int = 1280,
    height: int = 720,
    animation_keyframe_contract: ResolvedAnimationKeyframeContract = "legacy-v3",
) -> Any:
    """Render one preview frame; None time renders the canonical static layout."""

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPainter, QPixmap

    assignment_by_asset = {
        item.asset_id: item
        for item in assignments
        if item.scene_number == plan.scene_number
    }
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
        assignment = assignment_by_asset.get(asset.asset_id)
        opacity = 1.0
        offset_x = 0.0
        offset_y = 0.0
        if time_seconds is not None:
            offset = native_motion_preview_offset(
                assignment,
                time_seconds=time_seconds,
                duration_seconds=plan.duration_seconds,
            )
            crop = native_visual_preview_crop(
                assignment,
                time_seconds=time_seconds,
                duration_seconds=plan.duration_seconds,
                animation_keyframe_contract=animation_keyframe_contract,
            )
            scaled = _clip_pixmap_visibility(scaled, crop)
            blur_sigma = native_visual_preview_blur_sigma(
                assignment,
                time_seconds=time_seconds,
                duration_seconds=plan.duration_seconds,
                canvas_width=width,
                canvas_height=height,
                animation_keyframe_contract=animation_keyframe_contract,
            )
            scaled = _blur_pixmap_approx(scaled, blur_sigma)
            opacity = native_visual_preview_opacity(
                assignment,
                time_seconds=time_seconds,
                duration_seconds=plan.duration_seconds,
                animation_keyframe_contract=animation_keyframe_contract,
            )
            scale_factor = native_visual_preview_scale(
                assignment,
                time_seconds=time_seconds,
                duration_seconds=plan.duration_seconds,
            )
            if scale_factor != 1.0:
                scaled = scaled.scaled(
                    max(1, int(round(scaled.width() * scale_factor))),
                    max(1, int(round(scaled.height() * scale_factor))),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            rotation_degrees = native_visual_preview_rotation(
                assignment,
                time_seconds=time_seconds,
                duration_seconds=plan.duration_seconds,
            )
            scaled = _rotate_pixmap_same_size(scaled, rotation_degrees)

            glow = native_visual_preview_glow(
                assignment,
                time_seconds=time_seconds,
                duration_seconds=plan.duration_seconds,
                canvas_width=width,
                canvas_height=height,
                animation_keyframe_contract=animation_keyframe_contract,
            )
            scaled = _drop_shadow_pixmap_approx(
                scaled,
                color="#FFFFFF",
                alpha=glow.alpha,
                blur_radius=glow.sigma,
                offset=0.0,
            )
            shadow = native_visual_preview_shadow(
                assignment,
                time_seconds=time_seconds,
                duration_seconds=plan.duration_seconds,
                canvas_width=width,
                canvas_height=height,
                animation_keyframe_contract=animation_keyframe_contract,
            )
            scaled = _drop_shadow_pixmap_approx(
                scaled,
                color="#000000",
                alpha=shadow.alpha,
                blur_radius=shadow.sigma,
                offset=shadow.offset,
            )

            offset_x = width * offset.x
            offset_y = height * offset.y

        x = int(round(width * asset.anchor_x - scaled.width() / 2 + offset_x))
        y = int(round(height * asset.anchor_y - scaled.height() / 2 + offset_y))
        painter.setOpacity(opacity)
        painter.drawPixmap(x, y, scaled)
        painter.setOpacity(1.0)

    painter.end()
    return canvas


def _find_scene_list(root: Any, project: ProjectState) -> Any | None:
    from PySide6.QtWidgets import QListWidget

    for listing in root.findChildren(QListWidget):
        if listing.count() != len(project.scenes) or not project.scenes:
            continue
        first = listing.item(0)
        if first is not None and first.text().startswith(
            f"{project.scenes[0].scene_number:02d}. Scene"
        ):
            return listing
    return None


def _find_preview_canvas(root: Any) -> Any | None:
    from PySide6.QtWidgets import QLabel

    for label in root.findChildren(QLabel):
        minimum = label.minimumSize()
        if minimum.width() >= 640 and minimum.height() >= 360:
            return label
    return None


def _find_preview_timecode_label(root: Any) -> Any | None:
    from PySide6.QtWidgets import QLabel

    for label in root.findChildren(QLabel):
        text = label.text()
        if " / " in text and text.count(":") >= 6:
            return label
    return None


def _load_preview_subtitles(project: ProjectState) -> tuple[SubtitleCue, ...]:
    if not project.subtitle_source:
        return ()
    path = Path(project.subtitle_source).expanduser()
    if not path.is_file():
        return ()
    try:
        return parse_srt(path)
    except (OSError, UnicodeError, ValueError):
        return ()


def _scene_position_for_global_time(
    scene_durations: tuple[float, ...],
    global_seconds: float,
) -> tuple[int, float]:
    if not scene_durations:
        return 0, 0.0

    normalized = tuple(max(0.0, float(value)) for value in scene_durations)
    total = sum(normalized)
    remaining = max(0.0, min(float(global_seconds), total))
    if remaining >= total:
        return len(normalized) - 1, normalized[-1]

    for index, duration in enumerate(normalized):
        if remaining < duration:
            return index, remaining
        remaining -= duration
    return len(normalized) - 1, normalized[-1]


def _elapsed_global_position(
    anchor_global: float,
    anchor_monotonic: float,
    now_monotonic: float,
    total_seconds: float,
) -> float:
    elapsed = max(0.0, float(now_monotonic) - float(anchor_monotonic))
    return min(max(0.0, float(total_seconds)), max(0.0, anchor_global) + elapsed)


def install_native_motion_preview(root: Any, project: ProjectState) -> bool:
    """Enable continuous motion, scrub, narration, timecode, and timed subtitles."""

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import QPushButton, QSlider

    scene_list = _find_scene_list(root, project)
    canvas = _find_preview_canvas(root)
    timecode_label = _find_preview_timecode_label(root)
    buttons = root.findChildren(QPushButton)
    previous_button = next((button for button in buttons if button.text() == "◀"), None)
    play_button = next((button for button in buttons if button.text() == "▶"), None)
    next_button = next((button for button in buttons if button.text() == "▶|"), None)
    audio_button = next(
        (button for button in buttons if button.text() in {"🔊", "🔇"}),
        None,
    )
    sliders = root.findChildren(QSlider)
    progress_slider = sliders[0] if sliders else None
    if (
        scene_list is None
        or canvas is None
        or previous_button is None
        or play_button is None
        or next_button is None
    ):
        return False

    subtitle_cues = _load_preview_subtitles(project)
    animation_keyframe_contract = validate_project_animation_contract(project)
    previous_button.setToolTip("Pilih Scene sebelumnya pada preview.")
    next_button.setToolTip("Pilih Scene berikutnya pada preview.")
    play_button.setToolTip(
        "Putar preview kontinu mulai Scene terpilih sampai akhir project. "
        "Motion native, Fade/Pop, narasi, subtitle, dan animasi subtitle ikut preview bila tersedia."
    )
    if progress_slider is not None:
        progress_slider.setRange(0, 1000)
        progress_slider.setValue(0)
        progress_slider.setToolTip(
            "Geser untuk melihat frame motion/Fade/Pop, subtitle, dan posisi narasi pada waktu tertentu."
        )

    media_player: Any | None = None
    audio_output: Any | None = None
    audio_muted = False
    narration_path = (
        Path(project.narration_audio).expanduser()
        if project.narration_audio
        else None
    )
    if audio_button is not None:
        if narration_path is not None and narration_path.is_file():
            try:
                from PySide6.QtCore import QUrl
                from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
            except ImportError:
                audio_button.setEnabled(False)
                audio_button.setToolTip(
                    "Qt Multimedia tidak tersedia; preview visual tetap dapat digunakan."
                )
            else:
                audio_output = QAudioOutput(root)
                audio_output.setVolume(1.0)
                media_player = QMediaPlayer(root)
                media_player.setAudioOutput(audio_output)
                media_player.setSource(
                    QUrl.fromLocalFile(str(narration_path.resolve()))
                )
                audio_button.setText("🔊")
                audio_button.setToolTip("Mute/unmute narasi preview.")
        else:
            audio_button.setEnabled(False)
            if project.narration_audio:
                audio_button.setToolTip(
                    "File narasi project tidak ditemukan; impor ulang narasi untuk preview audio."
                )
            else:
                audio_button.setToolTip(
                    "Narasi belum diimpor; preview audio belum tersedia."
                )

    timer = QTimer(root)
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    fps = max(1, int(project.fps))
    timer.setInterval(max(15, int(round(1000 / fps))))
    playback_seconds = 0.0
    playback_anchor_global = 0.0
    playback_anchor_monotonic = 0.0
    continuing_across_scene = False
    scene_durations = tuple(scene.duration_seconds for scene in project.scenes)
    total_project_seconds = sum(max(0.0, float(value)) for value in scene_durations)

    def selected_plan() -> ScenePreviewPlan | None:
        row = scene_list.currentRow()
        if row < 0 or row >= len(project.scenes):
            return None
        return build_scene_preview_plan(project, project.scenes[row])

    def project_seconds(local_seconds: float) -> float:
        return preview_narration_seconds(
            scene_durations,
            scene_list.currentRow(),
            local_seconds,
        )

    def update_timecode(local_seconds: float) -> None:
        if timecode_label is None:
            return
        current = project_seconds(local_seconds)
        timecode_label.setText(
            f"{preview_timecode(current, fps)}  /  "
            f"{preview_timecode(total_project_seconds, fps)}"
        )

    def seek_audio(local_seconds: float) -> None:
        if media_player is None:
            return
        global_seconds = project_seconds(local_seconds)
        media_player.setPosition(max(0, int(round(global_seconds * 1000))))

    def pause_audio() -> None:
        if media_player is not None:
            media_player.pause()

    def update_transport_state(row: int) -> None:
        valid_scene = 0 <= row < len(project.scenes)
        previous_button.setEnabled(
            preview_neighbor_scene_index(row, len(project.scenes), -1) is not None
        )
        next_button.setEnabled(
            preview_neighbor_scene_index(row, len(project.scenes), 1) is not None
        )
        play_button.setEnabled(valid_scene)
        if progress_slider is not None:
            progress_slider.setEnabled(valid_scene)
        if audio_button is not None:
            audio_button.setEnabled(valid_scene and media_player is not None)

    def render_frame(time_seconds: float | None) -> None:
        plan = selected_plan()
        if plan is None:
            return
        local_seconds = 0.0 if time_seconds is None else time_seconds
        global_seconds = project_seconds(local_seconds)
        pixmap = render_native_motion_pixmap(
            plan,
            project.animations,
            time_seconds=time_seconds,
            animation_keyframe_contract=animation_keyframe_contract,
        )
        cue = active_subtitle_cue(subtitle_cues, global_seconds)
        pixmap = overlay_subtitle_pixmap(
            pixmap,
            cue,
            project.subtitle_style,
            project_width=project.width,
            project_height=project.height,
            animation=project.subtitle_animation,
            time_seconds=global_seconds,
        )
        canvas.setPixmap(pixmap)
        update_timecode(local_seconds)
        if progress_slider is not None:
            if time_seconds is None or plan.duration_seconds <= 0:
                progress_slider.setValue(0)
            else:
                fraction = max(0.0, min(1.0, time_seconds / plan.duration_seconds))
                progress_slider.setValue(int(round(fraction * 1000)))

    def set_playback_anchor(global_seconds: float) -> None:
        nonlocal playback_anchor_global, playback_anchor_monotonic
        playback_anchor_global = max(
            0.0,
            min(float(global_seconds), total_project_seconds),
        )
        playback_anchor_monotonic = time.monotonic()

    def current_playback_global() -> float:
        if not timer.isActive():
            return project_seconds(playback_seconds)
        return _elapsed_global_position(
            playback_anchor_global,
            playback_anchor_monotonic,
            time.monotonic(),
            total_project_seconds,
        )

    def render_global_position(global_seconds: float) -> None:
        nonlocal continuing_across_scene, playback_seconds
        row, local_seconds = _scene_position_for_global_time(
            scene_durations,
            global_seconds,
        )
        if row != scene_list.currentRow():
            continuing_across_scene = True
            try:
                scene_list.setCurrentRow(row)
            finally:
                continuing_across_scene = False
        playback_seconds = local_seconds
        render_frame(playback_seconds)

    def stop_playback(
        *,
        restore_static: bool = True,
        reset_position: bool = True,
    ) -> None:
        nonlocal playback_seconds
        timer.stop()
        pause_audio()
        if reset_position:
            playback_seconds = 0.0
            set_playback_anchor(project_seconds(0.0))
            seek_audio(0.0)
        else:
            set_playback_anchor(project_seconds(playback_seconds))
        play_button.setText("▶")
        if restore_static:
            render_frame(None)
        elif reset_position and progress_slider is not None:
            progress_slider.setValue(0)

    def pause_playback() -> None:
        if not timer.isActive():
            return
        global_seconds = current_playback_global()
        timer.stop()
        pause_audio()
        render_global_position(global_seconds)
        set_playback_anchor(global_seconds)
        seek_audio(playback_seconds)
        play_button.setText("▶")

    def tick() -> None:
        plan = selected_plan()
        if plan is None:
            stop_playback(restore_static=False)
            return

        global_seconds = current_playback_global()
        if global_seconds >= total_project_seconds:
            timer.stop()
            pause_audio()
            render_global_position(total_project_seconds)
            set_playback_anchor(total_project_seconds)
            seek_audio(playback_seconds)
            play_button.setText("▶")
            return

        render_global_position(global_seconds)

    def toggle_playback() -> None:
        nonlocal playback_seconds
        plan = selected_plan()
        if plan is None:
            return
        if timer.isActive():
            pause_playback()
            return

        start_seconds = playback_seconds
        if progress_slider is not None:
            start_seconds = preview_scrub_seconds(
                progress_slider.value(),
                progress_slider.maximum(),
                plan.duration_seconds,
            )
        if start_seconds >= plan.duration_seconds:
            start_seconds = 0.0

        playback_seconds = start_seconds
        global_seconds = project_seconds(playback_seconds)
        set_playback_anchor(global_seconds)
        play_button.setText("⏸")
        render_frame(playback_seconds)
        seek_audio(playback_seconds)
        if media_player is not None:
            media_player.play()
        timer.start()

    def scrub_to_value(value: int) -> None:
        nonlocal playback_seconds
        if progress_slider is None:
            return
        plan = selected_plan()
        if plan is None:
            return
        timer.stop()
        pause_audio()
        play_button.setText("▶")
        playback_seconds = preview_scrub_seconds(
            value,
            progress_slider.maximum(),
            plan.duration_seconds,
        )
        set_playback_anchor(project_seconds(playback_seconds))
        render_frame(playback_seconds)
        seek_audio(playback_seconds)

    def scrub_started() -> None:
        if timer.isActive():
            pause_playback()
        if progress_slider is not None:
            scrub_to_value(progress_slider.value())

    def scrub_released() -> None:
        if progress_slider is not None:
            scrub_to_value(progress_slider.value())

    def navigate_scene(step: int) -> None:
        target = preview_neighbor_scene_index(
            scene_list.currentRow(),
            len(project.scenes),
            step,
        )
        if target is not None:
            scene_list.setCurrentRow(target)

    def scene_changed(row: int) -> None:
        if continuing_across_scene:
            update_transport_state(row)
            return
        stop_playback(restore_static=False)
        update_transport_state(row)
        update_timecode(0.0)
        render_frame(None)

    def toggle_audio() -> None:
        nonlocal audio_muted
        if audio_button is None or audio_output is None:
            return
        audio_muted = not audio_muted
        audio_output.setMuted(audio_muted)
        audio_button.setText("🔇" if audio_muted else "🔊")
        audio_button.setToolTip(
            "Unmute narasi preview." if audio_muted else "Mute narasi preview."
        )

    timer.timeout.connect(tick)
    previous_button.clicked.connect(lambda: navigate_scene(-1))
    play_button.clicked.connect(toggle_playback)
    next_button.clicked.connect(lambda: navigate_scene(1))
    scene_list.currentRowChanged.connect(scene_changed)
    if progress_slider is not None:
        progress_slider.sliderPressed.connect(scrub_started)
        progress_slider.sliderMoved.connect(scrub_to_value)
        progress_slider.sliderReleased.connect(scrub_released)
    if audio_button is not None:
        audio_button.clicked.connect(toggle_audio)
    update_transport_state(scene_list.currentRow())
    render_frame(None)
    seek_audio(0.0)
    return True
