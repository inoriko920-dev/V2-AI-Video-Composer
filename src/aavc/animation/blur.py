from __future__ import annotations

from dataclasses import dataclass

from aavc.domain.project.models import AnimationAssignment

from .keyframes import evaluate_assignment_advanced_keyframe

_BLUR_SIGMA_SCALE = 0.022222
_BLUR_SIGMA_MIN = 8.0
_BLUR_SIGMA_MAX = 48.0


@dataclass(frozen=True, slots=True)
class BlurState:
    intensity: float = 0.0
    sigma: float = 0.0


def blur_sigma_limit(canvas_width: int, canvas_height: int) -> float:
    shortest = max(1.0, float(min(int(canvas_width), int(canvas_height))))
    mapped = _BLUR_SIGMA_SCALE * shortest
    return max(_BLUR_SIGMA_MIN, min(_BLUR_SIGMA_MAX, mapped))


def evaluate_assignment_blur(
    assignment: AnimationAssignment | None,
    normalized_time: float,
    *,
    canvas_width: int,
    canvas_height: int,
) -> BlurState:
    intensity = evaluate_assignment_advanced_keyframe(
        assignment,
        "blur",
        normalized_time,
    )
    if intensity is None:
        return BlurState()
    clamped = max(0.0, min(1.0, float(intensity)))
    return BlurState(
        intensity=clamped,
        sigma=clamped * blur_sigma_limit(canvas_width, canvas_height),
    )
