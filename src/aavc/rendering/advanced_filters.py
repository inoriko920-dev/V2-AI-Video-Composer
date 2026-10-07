from __future__ import annotations

from aavc.animation.keyframes import (
    clamp_keyframe_value,
    find_keyframe_track,
    is_supported_advanced_keyframe_track,
)
from aavc.domain.project.models import AnimationAssignment


K1_ACTIVE_RENDER_PROPERTIES = frozenset({"opacity"})


def assignment_has_k1_opacity(
    assignment: AnimationAssignment | None,
) -> bool:
    track = find_keyframe_track(assignment, "opacity")
    return track is not None and is_supported_advanced_keyframe_track(track)


def _number(value: float) -> str:
    return f"{float(value):.6f}"


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
