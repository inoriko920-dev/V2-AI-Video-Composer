from __future__ import annotations

from aavc.animation.keyframes import (
    KEYFRAME_PROPERTY_LIMITS,
    find_keyframe_track,
    is_supported_keyframe_track,
)
from aavc.domain.animation import AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment

_NATIVE_VISUAL_EFFECT_CAPABILITIES = (
    ("Rise", frozenset({"motion"})),
    ("Pan", frozenset({"motion"})),
    ("Fade", frozenset({"alpha"})),
    ("Pop", frozenset({"alpha", "scale"})),
    ("Wipe", frozenset({"alpha", "motion"})),
    ("Blur", frozenset({"alpha", "scale"})),
    ("Succession", frozenset({"alpha", "motion"})),
    ("Breathe", frozenset({"scale"})),
    ("Baseline", frozenset({"alpha", "motion"})),
    ("Drift", frozenset({"motion"})),
    ("Tectonic", frozenset({"motion"})),
    ("Tumble", frozenset({"rotation"})),
    ("Neon", frozenset({"alpha", "scale"})),
    ("Scrapbook", frozenset({"alpha", "scale", "rotation"})),
    ("Stomp", frozenset({"alpha", "scale"})),
    ("Brush", frozenset({"alpha", "motion"})),
    ("Ink", frozenset({"alpha", "scale"})),
    ("Digital", frozenset({"alpha", "motion"})),
    ("Spray Paint", frozenset({"alpha", "scale", "motion"})),
    ("Sketch", frozenset({"alpha", "rotation"})),
    ("Gradient", frozenset({"alpha", "motion"})),
)

NATIVE_VISUAL_EFFECT_NAMES = tuple(
    name for name, _capabilities in _NATIVE_VISUAL_EFFECT_CAPABILITIES
)


def _native_effects_with(capability: str) -> frozenset[str]:
    return frozenset(
        name
        for name, capabilities in _NATIVE_VISUAL_EFFECT_CAPABILITIES
        if capability in capabilities
    )


NATIVE_VISUAL_MOTION_EFFECTS = _native_effects_with("motion")
NATIVE_VISUAL_ALPHA_EFFECTS = _native_effects_with("alpha")
NATIVE_VISUAL_SCALE_EFFECTS = _native_effects_with("scale")
NATIVE_VISUAL_ROTATION_EFFECTS = _native_effects_with("rotation")
NATIVE_VISUAL_EFFECTS = frozenset(NATIVE_VISUAL_EFFECT_NAMES)


def native_visual_effect_names() -> tuple[str, ...]:
    """Return render-backed asset effects in deterministic Auto Motion order."""

    return NATIVE_VISUAL_EFFECT_NAMES


def is_native_visual_motion_effect(name: str) -> bool:
    return name in NATIVE_VISUAL_MOTION_EFFECTS


def is_native_visual_alpha_effect(name: str) -> bool:
    return name in NATIVE_VISUAL_ALPHA_EFFECTS


def is_native_visual_scale_effect(name: str) -> bool:
    return name in NATIVE_VISUAL_SCALE_EFFECTS


def is_native_visual_rotation_effect(name: str) -> bool:
    return name in NATIVE_VISUAL_ROTATION_EFFECTS


def is_native_visual_effect(name: str) -> bool:
    return name in NATIVE_VISUAL_EFFECTS


def _has_supported_keyframe(
    assignment: AnimationAssignment | None,
    *property_names: str,
) -> bool:
    if assignment is None:
        return False
    return any(
        (
            track := find_keyframe_track(assignment, property_name)
        ) is not None
        and is_supported_keyframe_track(track)
        for property_name in property_names
    )


def assignment_has_native_motion(
    assignment: AnimationAssignment | None,
) -> bool:
    if assignment is None:
        return False
    legacy = assignment.intensity > 0 and (
        is_native_visual_motion_effect(assignment.enter_effect)
        or is_native_visual_motion_effect(assignment.exit_effect)
    )
    return legacy or _has_supported_keyframe(
        assignment,
        "position_x",
        "position_y",
    )


def assignment_has_native_alpha(
    assignment: AnimationAssignment | None,
) -> bool:
    if assignment is None or assignment.intensity <= 0:
        return False
    return (
        is_native_visual_alpha_effect(assignment.enter_effect)
        or is_native_visual_alpha_effect(assignment.exit_effect)
    )


def assignment_has_native_scale(
    assignment: AnimationAssignment | None,
) -> bool:
    if assignment is None:
        return False
    legacy = assignment.intensity > 0 and (
        is_native_visual_scale_effect(assignment.enter_effect)
        or is_native_visual_scale_effect(assignment.exit_effect)
    )
    return legacy or _has_supported_keyframe(assignment, "scale")


def assignment_has_native_rotation(
    assignment: AnimationAssignment | None,
) -> bool:
    if assignment is None:
        return False
    legacy = assignment.intensity > 0 and (
        is_native_visual_rotation_effect(assignment.enter_effect)
        or is_native_visual_rotation_effect(assignment.exit_effect)
    )
    return legacy or _has_supported_keyframe(
        assignment,
        "rotation_degrees",
    )


def compile_native_alpha_filters(
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
) -> tuple[str, ...]:
    """Compile render-safe per-asset alpha transitions for native alpha effects."""

    if not assignment_has_native_alpha(assignment) or assignment is None:
        return ()

    duration = max(0.001, float(duration_seconds))
    window = min(0.25, duration / 2.0)
    filters: list[str] = ["format=rgba"]
    if is_native_visual_alpha_effect(assignment.enter_effect):
        filters.append(f"fade=t=in:st=0:d={window:.6f}:alpha=1")
    if is_native_visual_alpha_effect(assignment.exit_effect):
        exit_start = max(0.0, duration - window)
        filters.append(
            f"fade=t=out:st={exit_start:.6f}:d={window:.6f}:alpha=1"
        )
    return tuple(filters)


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


def _segment_expression(
    start_value: float,
    end_value: float,
    *,
    start_seconds: float,
    end_seconds: float,
    interpolation: str,
    easing: str,
) -> str:
    if interpolation == "hold":
        return _number(start_value)
    span = max(0.000001, end_seconds - start_seconds)
    fraction = f"(t-{_number(start_seconds)})/{_number(span)}"
    eased = _easing_expression(easing, fraction)
    delta = end_value - start_value
    return f"{_number(start_value)}+({_number(delta)})*({eased})"


def _compile_keyframe_track_expression(
    track: AnimationKeyframeTrack,
    *,
    duration_seconds: float,
) -> str | None:
    if not is_supported_keyframe_track(track):
        return None

    duration = max(0.001, float(duration_seconds))
    points = track.keyframes
    expression = _number(points[-1].value)
    for start, end in reversed(tuple(zip(points, points[1:], strict=False))):
        segment = _segment_expression(
            start.value,
            end.value,
            start_seconds=start.time * duration,
            end_seconds=end.time * duration,
            interpolation=start.interpolation,
            easing=start.easing,
        )
        expression = (
            f"if(lt(t,{_number(end.time * duration)}),"
            f"{segment},{expression})"
        )
    if points[0].time > 0:
        expression = (
            f"if(lt(t,{_number(points[0].time * duration)}),"
            f"{_number(points[0].value)},{expression})"
        )

    limits = KEYFRAME_PROPERTY_LIMITS.get(track.property_name)
    if limits is None:
        return expression
    lower, upper = limits
    return (
        f"min({_number(upper)},max({_number(lower)},"
        f"({expression})))"
    )


def compile_keyframe_value_expression(
    assignment: AnimationAssignment | None,
    property_name: str,
    *,
    duration_seconds: float,
) -> str | None:
    track = find_keyframe_track(assignment, property_name)
    if track is None:
        return None
    return _compile_keyframe_track_expression(
        track,
        duration_seconds=duration_seconds,
    )


def _scale_floor(effect: str) -> float | None:
    floors = {
        "Pop": 0.85,
        "Stomp": 0.85,
        "Breathe": 0.98,
        "Blur": 1.06,
        "Neon": 0.96,
        "Scrapbook": 0.92,
        "Ink": 0.90,
        "Spray Paint": 0.94,
    }
    return floors.get(effect)


def _enter_scale_expression(effect: str, window: str) -> str | None:
    floor = _scale_floor(effect)
    if floor is None:
        return None
    excursion = 1.0 - floor
    return f"{floor:.2f}{excursion:+.2f}*t/{window}"


def _exit_scale_expression(effect: str, exit_start: str, window: str) -> str | None:
    floor = _scale_floor(effect)
    if floor is None:
        return None
    change = floor - 1.0
    return f"1{change:+.2f}*(t-{exit_start})/{window}"


def _native_scale_factor(
    assignment: AnimationAssignment,
    *,
    duration_seconds: float,
) -> str:
    duration = max(0.001, float(duration_seconds))
    window_seconds = min(0.25, duration / 2.0)
    window = f"{window_seconds:.6f}"
    exit_start_seconds = max(0.0, duration - window_seconds)
    exit_start = f"{exit_start_seconds:.6f}"
    enter_expr = _enter_scale_expression(assignment.enter_effect, window)
    exit_expr = _exit_scale_expression(assignment.exit_effect, exit_start, window)

    if enter_expr is not None and exit_expr is not None:
        return (
            f"if(lt(t,{window}),{enter_expr},"
            f"if(gt(t,{exit_start}),{exit_expr},1))"
        )
    if enter_expr is not None:
        return f"if(lt(t,{window}),{enter_expr},1)"
    if exit_expr is not None:
        return f"if(gt(t,{exit_start}),{exit_expr},1)"
    return "1"


def compile_native_scale_filter(
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
) -> str | None:
    """Compile frame-evaluated per-asset scale for native scale effects."""

    if not assignment_has_native_scale(assignment) or assignment is None:
        return None

    factors: list[str] = []
    if assignment.intensity > 0 and (
        is_native_visual_scale_effect(assignment.enter_effect)
        or is_native_visual_scale_effect(assignment.exit_effect)
    ):
        factors.append(
            _native_scale_factor(
                assignment,
                duration_seconds=duration_seconds,
            )
        )
    keyframe_factor = compile_keyframe_value_expression(
        assignment,
        "scale",
        duration_seconds=duration_seconds,
    )
    if keyframe_factor is not None:
        factors.append(keyframe_factor)
    factor = "*".join(f"({item})" for item in factors) if factors else "1"
    width = f"max(2,trunc(iw*({factor})/2)*2)"
    return f"scale=w='{width}':h=-2:eval=frame"


def _rotation_term(
    effect: str,
    *,
    entering: bool,
    duration_seconds: float,
    window_seconds: float,
    intensity: float,
) -> str | None:
    degrees = {
        "Tumble": 12.0,
        "Scrapbook": 8.0,
        "Sketch": 4.0,
    }.get(effect)
    if degrees is None:
        return None

    window = f"{window_seconds:.6f}"
    max_angle = degrees * 0.017453293 * intensity
    if entering:
        return f"if(lt(t,{window}),-(1-t/{window})*{max_angle:.6f},0)"

    exit_start = max(0.0, duration_seconds - window_seconds)
    start = f"{exit_start:.6f}"
    return f"if(gt(t,{start}),((t-{start})/{window})*{max_angle:.6f},0)"


def compile_native_rotation_filter(
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
) -> str | None:
    """Compile frame-evaluated native rotation without changing base layout size."""

    if not assignment_has_native_rotation(assignment) or assignment is None:
        return None

    duration = max(0.001, float(duration_seconds))
    window = min(0.25, duration / 2.0)
    intensity = max(0.0, min(2.0, float(assignment.intensity)))
    terms: list[str] = []
    if assignment.intensity > 0:
        for effect, entering in (
            (assignment.enter_effect, True),
            (assignment.exit_effect, False),
        ):
            term = _rotation_term(
                effect,
                entering=entering,
                duration_seconds=duration,
                window_seconds=window,
                intensity=intensity,
            )
            if term is not None:
                terms.append(term)

    keyframe_degrees = compile_keyframe_value_expression(
        assignment,
        "rotation_degrees",
        duration_seconds=duration,
    )
    if keyframe_degrees is not None:
        terms.append(f"({keyframe_degrees})*0.017453293")

    if not terms:
        return None
    angle = "+".join(f"({term})" for term in terms)
    return f"rotate=a='{angle}':ow=iw:oh=ih:c=none"


def _motion_term(
    effect: str,
    *,
    entering: bool,
    duration_seconds: float,
    window_seconds: float,
    intensity: float,
) -> tuple[str, str] | None:
    window = f"{window_seconds:.6f}"

    oscillating = {
        "Tectonic": ("x", "W", 0.012, "18.849556"),
        "Digital": ("x", "W", 0.020, "25.132741"),
        "Spray Paint": ("y", "H", 0.015, "12.566371"),
    }.get(effect)
    if oscillating is not None:
        axis, dimension, base_distance, phase = oscillating
        distance = base_distance * intensity
        if entering:
            expression = (
                f"if(lt(t,{window}),"
                f"cos((t/{window})*{phase})*(1-t/{window})*"
                f"{dimension}*{distance:.6f},0)"
            )
        else:
            exit_start = max(0.0, duration_seconds - window_seconds)
            start = f"{exit_start:.6f}"
            expression = (
                f"if(gt(t,{start}),"
                f"cos(((t-{start})/{window})*{phase})*"
                f"((t-{start})/{window})*{dimension}*{distance:.6f},0)"
            )
        return axis, expression

    simple_motion = {
        "Rise": ("y", "H", 0.080),
        "Pan": ("x", "W", 0.060),
        "Drift": ("x", "W", 0.060),
        "Wipe": ("x", "W", 0.100),
        "Succession": ("y", "H", 0.045),
        "Baseline": ("y", "H", -0.030),
        "Brush": ("x", "W", -0.080),
        "Gradient": ("x", "W", 0.030),
    }.get(effect)
    if simple_motion is None:
        return None

    axis, dimension, base_distance = simple_motion
    distance = base_distance * intensity
    if distance < 0:
        distance_expr = f"-{dimension}*{abs(distance):.6f}"
    else:
        distance_expr = f"{dimension}*{distance:.6f}"
    if entering:
        expression = f"if(lt(t,{window}),(1-t/{window})*{distance_expr},0)"
    else:
        exit_start = max(0.0, duration_seconds - window_seconds)
        start = f"{exit_start:.6f}"
        expression = (
            f"if(gt(t,{start}),((t-{start})/{window})*{distance_expr},0)"
        )
    return axis, expression


def _combine(base: str, terms: list[str]) -> str:
    if not terms:
        return base
    return f"({base})+" + "+".join(f"({term})" for term in terms)


def compile_motion_overlay_position(
    *,
    base_x: str,
    base_y: str,
    assignment: AnimationAssignment | None,
    duration_seconds: float,
) -> tuple[str, str]:
    """Compile render-safe per-asset motion into overlay x/y expressions."""

    if not assignment_has_native_motion(assignment) or assignment is None:
        return base_x, base_y

    duration = max(0.001, duration_seconds)
    window = min(0.25, duration / 2.0)
    intensity = max(0.0, min(2.0, assignment.intensity))
    x_terms: list[str] = []
    y_terms: list[str] = []

    if assignment.intensity > 0:
        for effect, entering in (
            (assignment.enter_effect, True),
            (assignment.exit_effect, False),
        ):
            compiled = _motion_term(
                effect,
                entering=entering,
                duration_seconds=duration,
                window_seconds=window,
                intensity=intensity,
            )
            if compiled is None:
                continue
            axis, expression = compiled
            if axis == "x":
                x_terms.append(expression)
            else:
                y_terms.append(expression)

    x_keyframe = compile_keyframe_value_expression(
        assignment,
        "position_x",
        duration_seconds=duration,
    )
    y_keyframe = compile_keyframe_value_expression(
        assignment,
        "position_y",
        duration_seconds=duration,
    )
    if x_keyframe is not None:
        x_terms.append(f"W*({x_keyframe})")
    if y_keyframe is not None:
        y_terms.append(f"H*({y_keyframe})")

    return _combine(base_x, x_terms), _combine(base_y, y_terms)
