from __future__ import annotations

from dataclasses import dataclass

from aavc.domain.project.models import AnimationAssignment

from .keyframes import (
    evaluate_assignment_advanced_keyframe,
    find_keyframe_track,
    is_supported_advanced_keyframe_track,
)

CROP_PROPERTIES = (
    "crop_left",
    "crop_top",
    "crop_right",
    "crop_bottom",
)
MAX_CROP_SIDE = 0.45
MAX_CROP_PAIR = 0.90


@dataclass(frozen=True, slots=True)
class CropVisibility:
    left: float = 0.0
    top: float = 0.0
    right: float = 0.0
    bottom: float = 0.0
    normalized: bool = False

    @property
    def visible_width(self) -> float:
        return max(0.0, 1.0 - self.left - self.right)

    @property
    def visible_height(self) -> float:
        return max(0.0, 1.0 - self.top - self.bottom)


def assignment_has_supported_crop(
    assignment: AnimationAssignment | None,
) -> bool:
    if assignment is None:
        return False
    return any(
        (track := find_keyframe_track(assignment, property_name)) is not None
        and is_supported_advanced_keyframe_track(track)
        for property_name in CROP_PROPERTIES
    )


def _normalize_pair(first: float, second: float) -> tuple[float, float, bool]:
    total = first + second
    if total <= MAX_CROP_PAIR or total <= 0.0:
        return first, second, False
    scale = MAX_CROP_PAIR / total
    return first * scale, second * scale, True


def normalize_crop_visibility(
    left: float,
    top: float,
    right: float,
    bottom: float,
) -> CropVisibility:
    left = max(0.0, min(MAX_CROP_SIDE, float(left)))
    top = max(0.0, min(MAX_CROP_SIDE, float(top)))
    right = max(0.0, min(MAX_CROP_SIDE, float(right)))
    bottom = max(0.0, min(MAX_CROP_SIDE, float(bottom)))

    left, right, horizontal = _normalize_pair(left, right)
    top, bottom, vertical = _normalize_pair(top, bottom)
    return CropVisibility(
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        normalized=horizontal or vertical,
    )


def evaluate_assignment_crop_visibility(
    assignment: AnimationAssignment | None,
    normalized_time: float,
) -> CropVisibility:
    if assignment is None:
        return CropVisibility()

    values: dict[str, float] = {}
    for property_name in CROP_PROPERTIES:
        value = evaluate_assignment_advanced_keyframe(
            assignment,
            property_name,
            normalized_time,
        )
        values[property_name] = 0.0 if value is None else value

    return normalize_crop_visibility(
        values["crop_left"],
        values["crop_top"],
        values["crop_right"],
        values["crop_bottom"],
    )


def crop_assignment_has_clamped_keyframes(
    assignment: AnimationAssignment | None,
) -> bool:
    if assignment is None:
        return False
    for property_name in CROP_PROPERTIES:
        track = find_keyframe_track(assignment, property_name)
        if track is None:
            continue
        if any(
            keyframe.value < 0.0 or keyframe.value > MAX_CROP_SIDE
            for keyframe in track.keyframes
        ):
            return True
    return False


def crop_assignment_has_pair_normalization(
    assignment: AnimationAssignment | None,
) -> bool:
    if assignment is None or not assignment_has_supported_crop(assignment):
        return False

    sample_times = {0.0, 1.0}
    for property_name in CROP_PROPERTIES:
        track = find_keyframe_track(assignment, property_name)
        if track is not None:
            sample_times.update(keyframe.time for keyframe in track.keyframes)

    ordered = sorted(sample_times)
    midpoints = {
        (start + end) / 2.0
        for start, end in zip(ordered, ordered[1:], strict=False)
    }
    for normalized_time in sorted(sample_times | midpoints):
        if evaluate_assignment_crop_visibility(
            assignment,
            normalized_time,
        ).normalized:
            return True
    return False
