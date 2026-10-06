from __future__ import annotations

from aavc.domain.project.models import AnimationAssignment

_NATIVE_VISUAL_EFFECT_CAPABILITIES = (
    ("Fade", frozenset({"alpha"})),
    ("Pop", frozenset({"alpha", "scale"})),
    ("Breathe", frozenset({"scale"})),
    ("Stomp", frozenset({"alpha", "scale"})),
    ("Tumble", frozenset({"rotation"})),
    ("Tectonic", frozenset({"motion"})),
    ("Rise", frozenset({"motion"})),
    ("Pan", frozenset({"motion"})),
    ("Drift", frozenset({"motion"})),
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


def assignment_has_native_motion(
    assignment: AnimationAssignment | None,
) -> bool:
    if assignment is None or assignment.intensity <= 0:
        return False
    return (
        is_native_visual_motion_effect(assignment.enter_effect)
        or is_native_visual_motion_effect(assignment.exit_effect)
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
    if assignment is None or assignment.intensity <= 0:
        return False
    return (
        is_native_visual_scale_effect(assignment.enter_effect)
        or is_native_visual_scale_effect(assignment.exit_effect)
    )


def assignment_has_native_rotation(
    assignment: AnimationAssignment | None,
) -> bool:
    if assignment is None or assignment.intensity <= 0:
        return False
    return (
        is_native_visual_rotation_effect(assignment.enter_effect)
        or is_native_visual_rotation_effect(assignment.exit_effect)
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


def _scale_floor(effect: str) -> float | None:
    if effect in {"Pop", "Stomp"}:
        return 0.85
    if effect == "Breathe":
        return 0.98
    return None


def _enter_scale_expression(effect: str, window: str) -> str | None:
    floor = _scale_floor(effect)
    if floor is None:
        return None
    excursion = 1.0 - floor
    return f"{floor:.2f}+{excursion:.2f}*t/{window}"


def _exit_scale_expression(effect: str, exit_start: str, window: str) -> str | None:
    floor = _scale_floor(effect)
    if floor is None:
        return None
    excursion = 1.0 - floor
    return f"1-{excursion:.2f}*(t-{exit_start})/{window}"


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

    factor = _native_scale_factor(
        assignment,
        duration_seconds=duration_seconds,
    )
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
    if effect != "Tumble":
        return None

    window = f"{window_seconds:.6f}"
    max_angle = 0.209440 * intensity
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
    """Compile frame-evaluated Tumble rotation without changing base layout size."""

    if not assignment_has_native_rotation(assignment) or assignment is None:
        return None

    duration = max(0.001, float(duration_seconds))
    window = min(0.25, duration / 2.0)
    intensity = max(0.0, min(2.0, float(assignment.intensity)))
    terms: list[str] = []
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
    if effect == "Tectonic":
        distance = 0.012 * intensity
        phase = "18.849556"
        if entering:
            expression = (
                f"if(lt(t,{window}),"
                f"cos((t/{window})*{phase})*(1-t/{window})*W*{distance:.6f},0)"
            )
        else:
            exit_start = max(0.0, duration_seconds - window_seconds)
            start = f"{exit_start:.6f}"
            expression = (
                f"if(gt(t,{start}),"
                f"cos(((t-{start})/{window})*{phase})*"
                f"((t-{start})/{window})*W*{distance:.6f},0)"
            )
        return "x", expression

    if effect == "Rise":
        dimension = "H"
        distance = 0.08 * intensity
        axis = "y"
    elif effect in {"Pan", "Drift"}:
        dimension = "W"
        distance = 0.06 * intensity
        axis = "x"
    else:
        return None

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

    return _combine(base_x, x_terms), _combine(base_y, y_terms)
