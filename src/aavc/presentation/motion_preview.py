from __future__ import annotations

from dataclasses import dataclass

from aavc.animation import (
    CropVisibility,
    evaluate_assignment_advanced_keyframe,
    evaluate_assignment_blur,
    evaluate_assignment_crop_visibility,
    evaluate_assignment_keyframe,
    evaluate_effect,
)
from aavc.animation.compiler import (
    is_native_visual_alpha_effect,
    is_native_visual_motion_effect,
    is_native_visual_rotation_effect,
    is_native_visual_scale_effect,
)
from aavc.animation.contract import ResolvedAnimationKeyframeContract
from aavc.domain.project.models import AnimationAssignment


@dataclass(frozen=True, slots=True)
class PreviewMotionOffset:
    x: float = 0.0
    y: float = 0.0


def preview_scrub_seconds(
    value: int,
    maximum: int,
    duration_seconds: float,
) -> float:
    """Map a preview slider position to a clamped scene-local time."""

    duration = max(0.0, float(duration_seconds))
    if duration == 0.0:
        return 0.0
    upper = max(1, int(maximum))
    clamped = max(0, min(int(value), upper))
    return duration * (clamped / upper)


def preview_narration_seconds(
    scene_durations: tuple[float, ...],
    scene_index: int,
    local_seconds: float,
) -> float:
    """Map a Scene-local preview time to the global narration timeline."""

    index = int(scene_index)
    if index < 0 or index >= len(scene_durations):
        return 0.0
    normalized = tuple(max(0.0, float(duration)) for duration in scene_durations)
    scene_duration = normalized[index]
    local = max(0.0, min(float(local_seconds), scene_duration))
    return sum(normalized[:index]) + local


def preview_timecode(seconds: float, fps: int) -> str:
    """Format a non-negative preview position as HH:MM:SS:FF."""

    rate = max(1, int(fps))
    position = max(0.0, float(seconds))
    total_frames = max(0, int(round(position * rate)))
    total_seconds, frames = divmod(total_frames, rate)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"


def preview_neighbor_scene_index(
    current_index: int,
    scene_count: int,
    step: int,
) -> int | None:
    """Return an adjacent preview Scene index, or None when navigation hits a boundary."""

    count = max(0, int(scene_count))
    current = int(current_index)
    if count == 0 or current < 0 or current >= count or step == 0:
        return None
    target = current + (1 if step > 0 else -1)
    if target < 0 or target >= count:
        return None
    return target


def preview_continuation_scene_index(
    current_index: int,
    scene_count: int,
) -> int | None:
    """Return the next Scene for continuous playback, or None at project end."""

    return preview_neighbor_scene_index(current_index, scene_count, 1)


def native_visual_preview_opacity(
    assignment: AnimationAssignment | None,
    *,
    time_seconds: float,
    duration_seconds: float,
    animation_keyframe_contract: ResolvedAnimationKeyframeContract = "legacy-v3",
) -> float:
    """Evaluate legacy alpha plus K1 opacity using scene-local timing."""

    if assignment is None:
        return 1.0

    duration = max(0.001, float(duration_seconds))
    current = max(0.0, min(float(time_seconds), duration))
    window = min(0.25, duration / 2.0)
    opacity = 1.0

    if assignment.intensity > 0:
        for effect, entering in (
            (assignment.enter_effect, True),
            (assignment.exit_effect, False),
        ):
            if not is_native_visual_alpha_effect(effect):
                continue
            if entering:
                progress = current / window
            else:
                exit_start = max(0.0, duration - window)
                progress = (current - exit_start) / window
            opacity *= evaluate_effect(effect, progress, entering=entering).opacity

    if animation_keyframe_contract == "advanced-v1":
        keyframe_opacity = evaluate_assignment_advanced_keyframe(
            assignment,
            "opacity",
            current / duration,
        )
        if keyframe_opacity is not None:
            opacity *= keyframe_opacity

    return max(0.0, min(1.0, opacity))


def native_visual_preview_crop(
    assignment: AnimationAssignment | None,
    *,
    time_seconds: float,
    duration_seconds: float,
    animation_keyframe_contract: ResolvedAnimationKeyframeContract = "legacy-v3",
) -> CropVisibility:
    """Evaluate K2 crop without changing the asset canvas geometry."""

    if assignment is None or animation_keyframe_contract != "advanced-v1":
        return CropVisibility()

    duration = max(0.001, float(duration_seconds))
    current = max(0.0, min(float(time_seconds), duration))
    return evaluate_assignment_crop_visibility(
        assignment,
        current / duration,
    )


def native_visual_preview_blur_sigma(
    assignment: AnimationAssignment | None,
    *,
    time_seconds: float,
    duration_seconds: float,
    canvas_width: int,
    canvas_height: int,
    animation_keyframe_contract: ResolvedAnimationKeyframeContract = "legacy-v3",
) -> float:
    """Evaluate K3 Blur sigma for responsive Qt Approx preview."""

    if assignment is None or animation_keyframe_contract != "advanced-v1":
        return 0.0

    duration = max(0.001, float(duration_seconds))
    current = max(0.0, min(float(time_seconds), duration))
    state = evaluate_assignment_blur(
        assignment,
        current / duration,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
    )
    return state.sigma


def native_visual_preview_scale(
    assignment: AnimationAssignment | None,
    *,
    time_seconds: float,
    duration_seconds: float,
) -> float:
    """Evaluate native scale using the same timing window as FFmpeg."""

    if assignment is None:
        return 1.0

    duration = max(0.001, float(duration_seconds))
    current = max(0.0, min(float(time_seconds), duration))
    window = min(0.25, duration / 2.0)
    scale = 1.0

    if assignment.intensity > 0:
        for effect, entering in (
            (assignment.enter_effect, True),
            (assignment.exit_effect, False),
        ):
            if not is_native_visual_scale_effect(effect):
                continue
            if entering:
                progress = current / window
            else:
                exit_start = max(0.0, duration - window)
                progress = (current - exit_start) / window
            scale *= evaluate_effect(effect, progress, entering=entering).scale

    keyframe_scale = evaluate_assignment_keyframe(
        assignment,
        "scale",
        current / duration,
    )
    if keyframe_scale is not None:
        scale *= keyframe_scale
    return max(0.01, scale)


def native_visual_preview_rotation(
    assignment: AnimationAssignment | None,
    *,
    time_seconds: float,
    duration_seconds: float,
) -> float:
    """Evaluate native Tumble rotation using the same timing window as FFmpeg."""

    if assignment is None:
        return 0.0

    duration = max(0.001, float(duration_seconds))
    current = max(0.0, min(float(time_seconds), duration))
    window = min(0.25, duration / 2.0)
    intensity = max(0.0, min(2.0, float(assignment.intensity)))
    rotation = 0.0

    if assignment.intensity > 0:
        for effect, entering in (
            (assignment.enter_effect, True),
            (assignment.exit_effect, False),
        ):
            if not is_native_visual_rotation_effect(effect):
                continue
            if entering:
                progress = current / window
            else:
                exit_start = max(0.0, duration - window)
                progress = (current - exit_start) / window
            rotation += (
                evaluate_effect(effect, progress, entering=entering).rotation_degrees
                * intensity
            )

    keyframe_rotation = evaluate_assignment_keyframe(
        assignment,
        "rotation_degrees",
        current / duration,
    )
    if keyframe_rotation is not None:
        rotation += keyframe_rotation
    return rotation


def native_motion_preview_offset(
    assignment: AnimationAssignment | None,
    *,
    time_seconds: float,
    duration_seconds: float,
) -> PreviewMotionOffset:
    """Evaluate native motion using the same 0.25s timing contract as FFmpeg."""

    if assignment is None:
        return PreviewMotionOffset()

    duration = max(0.001, float(duration_seconds))
    current = max(0.0, min(float(time_seconds), duration))
    window = min(0.25, duration / 2.0)
    intensity = max(0.0, min(2.0, float(assignment.intensity)))
    offset_x = 0.0
    offset_y = 0.0

    if assignment.intensity > 0:
        for effect, entering in (
            (assignment.enter_effect, True),
            (assignment.exit_effect, False),
        ):
            if not is_native_visual_motion_effect(effect):
                continue
            if entering:
                progress = current / window
            else:
                exit_start = max(0.0, duration - window)
                progress = (current - exit_start) / window
            delta = evaluate_effect(effect, progress, entering=entering)
            offset_x += delta.offset_x * intensity
            offset_y += delta.offset_y * intensity

    normalized_time = current / duration
    keyframe_x = evaluate_assignment_keyframe(
        assignment,
        "position_x",
        normalized_time,
    )
    keyframe_y = evaluate_assignment_keyframe(
        assignment,
        "position_y",
        normalized_time,
    )
    if keyframe_x is not None:
        offset_x += keyframe_x
    if keyframe_y is not None:
        offset_y += keyframe_y
    return PreviewMotionOffset(offset_x, offset_y)
