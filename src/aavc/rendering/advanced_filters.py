from __future__ import annotations

from typing import TYPE_CHECKING

from aavc.animation.crop import CROP_PROPERTIES, assignment_has_supported_crop
from aavc.animation.keyframes import (
    KEYFRAME_PROPERTY_LIMITS,
    clamp_keyframe_value,
    find_keyframe_track,
    is_supported_advanced_keyframe_track,
)
from aavc.domain.project.models import AnimationAssignment

if TYPE_CHECKING:
    from .render_plan import RenderPlan

K1_ACTIVE_RENDER_PROPERTIES = frozenset({"opacity"})
K2_ACTIVE_RENDER_PROPERTIES = frozenset(CROP_PROPERTIES)

def _number(value: float) -> str:
    return f"{float(value):.6f}"

def _easing_expression(easing: str, fraction: str) -> str:
    if easing == "ease_in":
        return f"({fraction})*({fraction})"
    if easing == "ease_out":
        return f"1-(1-({fraction}))*(1-({fraction}))"
    if easing == "ease_in_out":
        return (
            f"if(lt(({fraction}),0.5),"
            f"2*({fraction})*({fraction}),"
            f"1-pow(-2*({fraction})+2,2)/2)"
        )
    return fraction

def _advanced_time_expression(
    assignment: AnimationAssignment | None,
    property_name: str,
    *,
    duration_seconds: float,
    time_variable: str = "T",
    neutral: float = 0.0,
) -> str:
    track = find_keyframe_track(assignment, property_name)
    if track is None or not is_supported_advanced_keyframe_track(track):
        return _number(neutral)

    duration = max(0.001, float(duration_seconds))
    points = track.keyframes
    expression = _number(points[-1].value)
    for start, end in reversed(tuple(zip(points, points[1:], strict=False))):
        if start.interpolation == "hold":
            segment = _number(start.value)
        else:
            start_seconds = start.time * duration
            span = max(0.000001, (end.time - start.time) * duration)
            fraction = (
                f"({time_variable}-{_number(start_seconds)})/"
                f"{_number(span)}"
            )
            eased = _easing_expression(start.easing, fraction)
            delta = end.value - start.value
            segment = f"{_number(start.value)}+({_number(delta)})*({eased})"
        expression = (
            f"if(lt({time_variable},{_number(end.time * duration)}),"
            f"{segment},{expression})"
        )

    if points[0].time > 0:
        expression = (
            f"if(lt({time_variable},{_number(points[0].time * duration)}),"
            f"{_number(points[0].value)},{expression})"
        )

    limits = KEYFRAME_PROPERTY_LIMITS.get(property_name)
    if limits is None:
        return expression
    lower, upper = limits
    return (
        f"min({_number(upper)},max({_number(lower)},"
        f"({expression})))"
    )

def _normalize_crop_pair(first: str, second: str) -> tuple[str, str]:
    total = f"(({first})+({second}))"
    normalized_first = (
        f"if(gt({total},0.900000),"
        f"0.900000*({first})/{total},({first}))"
    )
    normalized_second = (
        f"if(gt({total},0.900000),"
        f"0.900000*({second})/{total},({second}))"
    )
    return normalized_first, normalized_second

def _crop_gate_expression(
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
) -> str | None:
    if not assignment_has_supported_crop(assignment):
        return None

    left = _advanced_time_expression(
        assignment,
        "crop_left",
        duration_seconds=duration_seconds,
    )
    top = _advanced_time_expression(
        assignment,
        "crop_top",
        duration_seconds=duration_seconds,
    )
    right = _advanced_time_expression(
        assignment,
        "crop_right",
        duration_seconds=duration_seconds,
    )
    bottom = _advanced_time_expression(
        assignment,
        "crop_bottom",
        duration_seconds=duration_seconds,
    )
    left, right = _normalize_crop_pair(left, right)
    top, bottom = _normalize_crop_pair(top, bottom)
    return (
        f"gte(X,W*({left}))*"
        f"lt(X,W*(1-({right})))*"
        f"gte(Y,H*({top}))*"
        f"lt(Y,H*(1-({bottom})))"
    )

def compile_k2_crop_mask_filter(
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
) -> str | None:
    """Compile the alpha-plane crop gate while keeping RGB untouched."""

    gate = _crop_gate_expression(
        assignment,
        duration_seconds=duration_seconds,
    )
    if gate is None:
        return None
    return f"geq=lum='p(X,Y)*({gate})'"

def assignment_has_k1_opacity(
    assignment: AnimationAssignment | None,
) -> bool:
    track = find_keyframe_track(assignment, "opacity")
    return track is not None and is_supported_advanced_keyframe_track(track)

def _eased_ti_expression(easing: str) -> str:
    if easing == "ease_in":
        return "TI*TI"
    if easing == "ease_out":
        return "1-(1-TI)*(1-TI)"
    if easing == "ease_in_out":
        # Quadratic ease-in-out without commas keeps sendcmd parsing stable.
        x = "2*TI-1"
        tail = f"(1-abs({x}))"
        return f"0.5+sgn({x})*(1-({tail})*({tail}))/2"
    return "TI"

def _segment_gain_expression(
    start_value: float,
    end_value: float,
    *,
    interpolation: str,
    easing: str,
) -> str:
    start = clamp_keyframe_value("opacity", start_value)
    end = clamp_keyframe_value("opacity", end_value)
    if interpolation == "hold":
        return _number(start)
    eased = _eased_ti_expression(easing)
    delta = end - start
    return f"{_number(start)}+({_number(delta)})*({eased})"

def compile_k1_opacity_filters(
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
    instance_id: str,
) -> tuple[str, ...]:
    """Compile advanced-v1 opacity using runtime alpha gain commands.

    Existing source alpha is preserved because colorchannelmixer multiplies
    the alpha channel by the runtime aa value instead of replacing it.
    """

    track = find_keyframe_track(assignment, "opacity")
    if track is None or not is_supported_advanced_keyframe_track(track):
        return ()

    duration = max(0.001, float(duration_seconds))
    target = f"colorchannelmixer@{instance_id}"
    points = track.keyframes
    initial = clamp_keyframe_value("opacity", points[0].value)
    commands: list[str] = []

    first_seconds = points[0].time * duration
    if first_seconds > 0:
        commands.append(
            f"0-{_number(first_seconds)} [expr] {target} aa {_number(initial)}"
        )

    for start, end in zip(points, points[1:], strict=False):
        start_seconds = start.time * duration
        end_seconds = end.time * duration
        expression = _segment_gain_expression(
            start.value,
            end.value,
            interpolation=start.interpolation,
            easing=start.easing,
        )
        commands.append(
            f"{_number(start_seconds)}-{_number(end_seconds)} "
            f"[expr] {target} aa {expression}"
        )

    last_seconds = points[-1].time * duration
    if len(points) == 1:
        commands.append(
            f"{_number(first_seconds)}-{_number(duration)} "
            f"[expr] {target} aa {_number(initial)}"
        )
    elif last_seconds < duration:
        last = clamp_keyframe_value("opacity", points[-1].value)
        commands.append(
            f"{_number(last_seconds)}-{_number(duration)} "
            f"[expr] {target} aa {_number(last)}"
        )

    if not commands:
        commands.append(
            f"0-{_number(duration)} [expr] {target} aa {_number(initial)}"
        )

    command_text = ";".join(commands)
    return (
        "format=rgba",
        "sendcmd=c='" + command_text + "'",
        f"{target}=aa={_number(initial)}",
    )

def render_plan_requires_k1_opacity(plan: RenderPlan) -> bool:
    if plan.animation_keyframe_contract != "advanced-v1":
        return False
    return any(
        assignment is not None and assignment_has_k1_opacity(assignment)
        for scene in plan.scenes
        for assignment in scene.animations
    )

def render_plan_requires_k2_crop(plan: RenderPlan) -> bool:
    if plan.animation_keyframe_contract != "advanced-v1":
        return False
    return any(
        assignment is not None and assignment_has_supported_crop(assignment)
        for scene in plan.scenes
        for assignment in scene.animations
    )
