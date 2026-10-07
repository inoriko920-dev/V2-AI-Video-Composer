from __future__ import annotations

from dataclasses import dataclass

from aavc.domain.project.models import AnimationAssignment

from .keyframes import evaluate_assignment_advanced_keyframe

_SHADOW_ALPHA_SCALE = 0.55
_SHADOW_OFFSET_SCALE = 0.012
_SHADOW_SIGMA_SCALE = 0.014
_GLOW_ALPHA_SCALE = 0.65
_GLOW_SIGMA_SCALE = 0.018


@dataclass(frozen=True, slots=True)
class ShadowState:
    intensity: float = 0.0
    alpha: float = 0.0
    offset: float = 0.0
    sigma: float = 0.0


@dataclass(frozen=True, slots=True)
class GlowState:
    intensity: float = 0.0
    alpha: float = 0.0
    sigma: float = 0.0


def _shortest_canvas_side(canvas_width: int, canvas_height: int) -> float:
    return max(1.0, float(min(int(canvas_width), int(canvas_height))))


def evaluate_assignment_shadow(
    assignment: AnimationAssignment | None,
    normalized_time: float,
    *,
    canvas_width: int,
    canvas_height: int,
) -> ShadowState:
    intensity = evaluate_assignment_advanced_keyframe(
        assignment,
        "shadow",
        normalized_time,
    )
    if intensity is None:
        return ShadowState()
    value = max(0.0, min(1.0, float(intensity)))
    shortest = _shortest_canvas_side(canvas_width, canvas_height)
    return ShadowState(
        intensity=value,
        alpha=_SHADOW_ALPHA_SCALE * value,
        offset=_SHADOW_OFFSET_SCALE * shortest * value,
        sigma=_SHADOW_SIGMA_SCALE * shortest * value,
    )


def evaluate_assignment_glow(
    assignment: AnimationAssignment | None,
    normalized_time: float,
    *,
    canvas_width: int,
    canvas_height: int,
) -> GlowState:
    intensity = evaluate_assignment_advanced_keyframe(
        assignment,
        "glow",
        normalized_time,
    )
    if intensity is None:
        return GlowState()
    value = max(0.0, min(1.0, float(intensity)))
    shortest = _shortest_canvas_side(canvas_width, canvas_height)
    return GlowState(
        intensity=value,
        alpha=_GLOW_ALPHA_SCALE * value,
        sigma=_GLOW_SIGMA_SCALE * shortest * value,
    )
