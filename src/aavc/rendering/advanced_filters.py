from __future__ import annotations

from typing import TYPE_CHECKING

from aavc.animation.blur import blur_sigma_limit
from aavc.animation.shadow_glow import (
    evaluate_assignment_glow,
    evaluate_assignment_shadow,
)
from aavc.animation.crop import (
    CROP_PROPERTIES,
    assignment_has_supported_crop,
    evaluate_assignment_crop_visibility,
)
from aavc.animation.keyframes import (
    KEYFRAME_PROPERTY_LIMITS,
    clamp_keyframe_value,
    evaluate_advanced_keyframe_track,
    find_keyframe_track,
    is_supported_advanced_keyframe_track,
)
from aavc.domain.project.models import AnimationAssignment

if TYPE_CHECKING:
    from .render_plan import RenderPlan

K1_ACTIVE_RENDER_PROPERTIES = frozenset({"opacity"})
K2_ACTIVE_RENDER_PROPERTIES = frozenset(CROP_PROPERTIES)
K3_ACTIVE_RENDER_PROPERTIES = frozenset({"blur"})
K4_ACTIVE_RENDER_PROPERTIES = frozenset({"shadow", "glow"})


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


def _crop_clamp_expression(expression: str) -> str:
    """Clamp to 0..0.45 without commas so sendcmd can parse the argument."""

    return (
        f"(abs({expression})-abs(({expression})-0.450000)+0.450000)/2"
    )


def _crop_easing_expression(easing: str) -> str:
    if easing == "ease_in":
        return "TI*TI"
    if easing == "ease_out":
        return "1-(1-TI)*(1-TI)"
    if easing == "ease_in_out":
        x = "2*TI-1"
        tail = f"(1-abs({x}))"
        return f"0.5+sgn({x})*(1-({tail})*({tail}))/2"
    return "TI"


def _crop_segment_expression(
    start_value: float,
    end_value: float,
    *,
    interpolation: str,
    easing: str,
) -> str:
    if interpolation == "hold":
        raw = _number(start_value)
    else:
        eased = _crop_easing_expression(easing)
        delta = end_value - start_value
        raw = f"{_number(start_value)}+({_number(delta)})*({eased})"
    return _crop_clamp_expression(raw)


def _constant_crop_expression(value: float) -> str:
    return _crop_clamp_expression(_number(value))


def _crop_track_command_intervals(
    assignment: AnimationAssignment | None,
    property_name: str,
    *,
    duration_seconds: float,
    target: str,
    command: str,
    dimension: str,
    invert: bool = False,
) -> tuple[str, ...]:
    track = find_keyframe_track(assignment, property_name)
    if track is None or not is_supported_advanced_keyframe_track(track):
        return ()

    duration = max(0.001, float(duration_seconds))
    points = track.keyframes
    intervals: list[tuple[float, float, str]] = []

    first_seconds = points[0].time * duration
    if first_seconds > 0.0:
        intervals.append(
            (0.0, first_seconds, _constant_crop_expression(points[0].value))
        )

    if len(points) == 1:
        intervals.append(
            (
                first_seconds,
                duration,
                _constant_crop_expression(points[0].value),
            )
        )
    else:
        for start, end in zip(points, points[1:], strict=False):
            intervals.append(
                (
                    start.time * duration,
                    end.time * duration,
                    _crop_segment_expression(
                        start.value,
                        end.value,
                        interpolation=start.interpolation,
                        easing=start.easing,
                    ),
                )
            )
        last_seconds = points[-1].time * duration
        if last_seconds < duration:
            intervals.append(
                (
                    last_seconds,
                    duration,
                    _constant_crop_expression(points[-1].value),
                )
            )

    commands: list[str] = []
    for start_seconds, end_seconds, value_expr in intervals:
        if end_seconds <= start_seconds:
            continue
        pixel_expr = (
            f"ceil({dimension}*(1-({value_expr})))"
            if invert
            else f"ceil({dimension}*({value_expr}))"
        )
        commands.append(
            f"{_number(start_seconds)}-{_number(end_seconds)} "
            f"[expr] {target} {command} {pixel_expr}"
        )
    return tuple(commands)


def _crop_enable_expression(
    assignment: AnimationAssignment | None,
    property_name: str,
    *,
    duration_seconds: float,
) -> str:
    value = _advanced_time_expression(
        assignment,
        property_name,
        duration_seconds=duration_seconds,
        time_variable="t",
    )
    return f"gt(({value}),0.000001)"


def compile_k2_crop_filters(
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
    instance_id: str,
) -> tuple[str, ...]:
    """Compile K2 crop as four runtime transparent edge boxes.

    The frame canvas never changes. Pixels outside the visible rectangle are
    overwritten with transparent black while pixels inside remain untouched,
    preserving the source alpha channel.
    """

    if not assignment_has_supported_crop(assignment):
        return ()

    duration = max(0.001, float(duration_seconds))
    initial = evaluate_assignment_crop_visibility(assignment, 0.0)
    commands: list[str] = []
    filters: list[str] = ["format=rgba"]

    specs = (
        (
            "crop_left",
            "left",
            "w",
            "W",
            False,
            f"x=0:y=0:w=iw*{initial.left:.6f}:h=ih",
        ),
        (
            "crop_top",
            "top",
            "h",
            "H",
            False,
            f"x=0:y=0:w=iw:h=ih*{initial.top:.6f}",
        ),
        (
            "crop_right",
            "right",
            "x",
            "W",
            True,
            f"x=iw*(1-{initial.right:.6f}):y=0:w=iw:h=ih",
        ),
        (
            "crop_bottom",
            "bottom",
            "y",
            "H",
            True,
            f"x=0:y=ih*(1-{initial.bottom:.6f}):w=iw:h=ih",
        ),
    )

    active_specs: list[tuple[str, str, str, str, bool, str]] = []
    for property_name, suffix, command, dimension, invert, geometry in specs:
        track = find_keyframe_track(assignment, property_name)
        if track is None or not is_supported_advanced_keyframe_track(track):
            continue
        target = f"drawbox@{instance_id}_{suffix}"
        commands.extend(
            _crop_track_command_intervals(
                assignment,
                property_name,
                duration_seconds=duration,
                target=target,
                command=command,
                dimension=dimension,
                invert=invert,
            )
        )
        active_specs.append(
            (property_name, suffix, command, dimension, invert, geometry)
        )

    if commands:
        filters.append("sendcmd=c='" + ";".join(commands) + "'")

    for property_name, suffix, _command, _dimension, _invert, geometry in active_specs:
        enable = _crop_enable_expression(
            assignment,
            property_name,
            duration_seconds=duration,
        )
        filters.append(
            f"drawbox@{instance_id}_{suffix}="
            f"{geometry}:color=black@0:t=fill:replace=1:"
            f"enable='{enable}'"
        )

    return tuple(filters)


def assignment_has_k3_blur(
    assignment: AnimationAssignment | None,
) -> bool:
    track = find_keyframe_track(assignment, "blur")
    return track is not None and is_supported_advanced_keyframe_track(track)


def _blur_sigma_samples(
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
    fps: int,
    canvas_width: int,
    canvas_height: int,
) -> tuple[tuple[float, float], ...]:
    track = find_keyframe_track(assignment, "blur")
    if track is None or not is_supported_advanced_keyframe_track(track):
        return ()

    duration = max(0.001, float(duration_seconds))
    rate = max(1, int(fps))
    frame_count = max(1, int(round(duration * rate)))
    sigma_limit = blur_sigma_limit(canvas_width, canvas_height)
    samples: list[tuple[float, float]] = []
    last_sigma: float | None = None

    for frame_index in range(frame_count):
        seconds = frame_index / rate
        normalized = min(1.0, seconds / duration)
        intensity = evaluate_advanced_keyframe_track(track, normalized)
        sigma = round(float(intensity) * sigma_limit, 2)
        if last_sigma is not None and abs(sigma - last_sigma) < 0.005:
            continue
        samples.append((seconds, sigma))
        last_sigma = sigma

    end_sigma = round(
        float(evaluate_advanced_keyframe_track(track, 1.0)) * sigma_limit,
        2,
    )
    if not samples or abs(end_sigma - samples[-1][1]) >= 0.005:
        samples.append((duration, end_sigma))
    return tuple(samples)


def compile_k3_blur_filters(
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
    fps: int,
    canvas_width: int,
    canvas_height: int,
    instance_id: str,
) -> tuple[str, ...]:
    """Compile K3 Blur from canonical frame samples into runtime gblur commands."""

    samples = _blur_sigma_samples(
        assignment,
        duration_seconds=duration_seconds,
        fps=fps,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
    )
    if not samples:
        return ()

    target = f"gblur@{instance_id}"
    initial_sigma = samples[0][1]
    commands = [
        command
        for seconds, sigma in samples[1:]
        for command in (
            f"{_number(seconds)} {target} sigma {sigma:.2f}",
            f"{_number(seconds)} {target} sigmaV {sigma:.2f}",
        )
    ]
    filters: list[str] = ["format=rgba", "premultiply=inplace=1"]
    if commands:
        filters.append("sendcmd=c='" + ";".join(commands) + "'")
    filters.extend(
        (
            (
                f"{target}=sigma={initial_sigma:.2f}:"
                f"sigmaV={initial_sigma:.2f}:steps=2"
            ),
            "unpremultiply=inplace=1",
        )
    )
    return tuple(filters)


def assignment_has_k4_shadow(
    assignment: AnimationAssignment | None,
) -> bool:
    track = find_keyframe_track(assignment, "shadow")
    return track is not None and is_supported_advanced_keyframe_track(track)


def assignment_has_k4_glow(
    assignment: AnimationAssignment | None,
) -> bool:
    track = find_keyframe_track(assignment, "glow")
    return track is not None and is_supported_advanced_keyframe_track(track)


def _k4_intensity_samples(
    assignment: AnimationAssignment | None,
    property_name: str,
    *,
    duration_seconds: float,
    fps: int,
) -> tuple[tuple[float, float], ...]:
    track = find_keyframe_track(assignment, property_name)
    if track is None or not is_supported_advanced_keyframe_track(track):
        return ()

    duration = max(0.001, float(duration_seconds))
    rate = max(1, int(fps))
    frame_count = max(1, int(round(duration * rate)))
    samples: list[tuple[float, float]] = []
    last_value: float | None = None
    for frame_index in range(frame_count):
        seconds = frame_index / rate
        normalized = min(1.0, seconds / duration)
        value = round(
            float(evaluate_advanced_keyframe_track(track, normalized)),
            4,
        )
        if last_value is not None and abs(value - last_value) < 0.00005:
            continue
        samples.append((seconds, value))
        last_value = value

    end_value = round(float(evaluate_advanced_keyframe_track(track, 1.0)), 4)
    if not samples or abs(end_value - samples[-1][1]) >= 0.00005:
        samples.append((duration, end_value))
    return tuple(samples)


def _k4_branch_commands(
    samples: tuple[tuple[float, float], ...],
    *,
    sigma_scale: float,
    alpha_scale: float,
    blur_target: str,
    gain_target: str,
) -> tuple[str, ...]:
    commands: list[str] = []
    for seconds, intensity in samples[1:]:
        sigma = round(sigma_scale * intensity, 2)
        alpha = round(alpha_scale * intensity, 4)
        commands.extend(
            (
                f"{_number(seconds)} {blur_target} sigma {sigma:.2f}",
                f"{_number(seconds)} {blur_target} sigmaV {sigma:.2f}",
                f"{_number(seconds)} {gain_target} aa {alpha:.4f}",
            )
        )
    return tuple(commands)


def compile_k4_shadow_glow_clauses(
    input_label: str,
    output_label: str,
    assignment: AnimationAssignment | None,
    *,
    duration_seconds: float,
    fps: int,
    canvas_width: int,
    canvas_height: int,
    instance_id: str,
) -> tuple[str, ...]:
    """Build K4 Shadow/Glow branches behind the post-rotation source."""

    shadow = assignment_has_k4_shadow(assignment)
    glow = assignment_has_k4_glow(assignment)
    if not shadow and not glow:
        return ()

    shortest = max(1.0, float(min(int(canvas_width), int(canvas_height))))
    branch_names: list[str] = []
    if shadow:
        branch_names.append(f"{instance_id}_shadow_src")
    if glow:
        branch_names.append(f"{instance_id}_glow_src")

    main = f"{instance_id}_main"
    blank_src = f"{instance_id}_blank_src"
    split_outputs = "".join(
        f"[{name}]" for name in (main, blank_src, *branch_names)
    )
    clauses: list[str] = [
        f"[{input_label}]format=rgba,split={2 + len(branch_names)}{split_outputs}"
    ]
    blank = f"{instance_id}_blank"
    clauses.append(
        f"[{blank_src}]colorchannelmixer=aa=0[{blank}]"
    )

    layers: list[tuple[str, str, str]] = []

    if glow:
        samples = _k4_intensity_samples(
            assignment,
            "glow",
            duration_seconds=duration_seconds,
            fps=fps,
        )
        initial = samples[0][1]
        sigma_scale = 0.018 * shortest
        alpha_scale = 0.65
        blur_target = f"gblur@{instance_id}_glow_blur"
        gain_target = f"colorchannelmixer@{instance_id}_glow_gain"
        commands = _k4_branch_commands(
            samples,
            sigma_scale=sigma_scale,
            alpha_scale=alpha_scale,
            blur_target=blur_target,
            gain_target=gain_target,
        )
        glow_color_src = f"{instance_id}_glow_color_src"
        glow_alpha_src = f"{instance_id}_glow_alpha_src"
        glow_mask = f"{instance_id}_glow_mask"
        glow_color = f"{instance_id}_glow_color"
        glow_merged = f"{instance_id}_glow_merged"
        glow_layer = f"{instance_id}_glow_layer"
        clauses.append(
            f"[{instance_id}_glow_src]split=2"
            f"[{glow_color_src}][{glow_alpha_src}]"
        )
        alpha_chain = f"[{glow_alpha_src}]alphaextract"
        if commands:
            alpha_chain += ",sendcmd=c='" + ";".join(commands) + "'"
        alpha_chain += (
            f",{blur_target}=sigma={sigma_scale * initial:.2f}:"
            f"sigmaV={sigma_scale * initial:.2f}:steps=2"
            f"[{glow_mask}]"
        )
        clauses.append(alpha_chain)
        clauses.append(
            f"[{glow_color_src}]lutrgb=r=255:g=255:b=255[{glow_color}]"
        )
        clauses.append(
            f"[{glow_color}][{glow_mask}]alphamerge[{glow_merged}]"
        )
        clauses.append(
            f"[{glow_merged}]{gain_target}=aa={alpha_scale * initial:.4f}"
            f"[{glow_layer}]"
        )
        layers.append((glow_layer, "0", "0"))

    if shadow:
        samples = _k4_intensity_samples(
            assignment,
            "shadow",
            duration_seconds=duration_seconds,
            fps=fps,
        )
        initial = samples[0][1]
        sigma_scale = 0.014 * shortest
        alpha_scale = 0.55
        blur_target = f"gblur@{instance_id}_shadow_blur"
        gain_target = f"colorchannelmixer@{instance_id}_shadow_gain"
        commands = _k4_branch_commands(
            samples,
            sigma_scale=sigma_scale,
            alpha_scale=alpha_scale,
            blur_target=blur_target,
            gain_target=gain_target,
        )
        shadow_color_src = f"{instance_id}_shadow_color_src"
        shadow_alpha_src = f"{instance_id}_shadow_alpha_src"
        shadow_mask = f"{instance_id}_shadow_mask"
        shadow_color = f"{instance_id}_shadow_color"
        shadow_merged = f"{instance_id}_shadow_merged"
        shadow_layer = f"{instance_id}_shadow_layer"
        clauses.append(
            f"[{instance_id}_shadow_src]split=2"
            f"[{shadow_color_src}][{shadow_alpha_src}]"
        )
        alpha_chain = f"[{shadow_alpha_src}]alphaextract"
        if commands:
            alpha_chain += ",sendcmd=c='" + ";".join(commands) + "'"
        alpha_chain += (
            f",{blur_target}=sigma={sigma_scale * initial:.2f}:"
            f"sigmaV={sigma_scale * initial:.2f}:steps=2"
            f"[{shadow_mask}]"
        )
        clauses.append(alpha_chain)
        clauses.append(
            f"[{shadow_color_src}]lutrgb=r=0:g=0:b=0[{shadow_color}]"
        )
        clauses.append(
            f"[{shadow_color}][{shadow_mask}]alphamerge[{shadow_merged}]"
        )
        clauses.append(
            f"[{shadow_merged}]{gain_target}=aa={alpha_scale * initial:.4f}"
            f"[{shadow_layer}]"
        )
        intensity_expr = _advanced_time_expression(
            assignment,
            "shadow",
            duration_seconds=duration_seconds,
            time_variable="t",
        )
        offset_scale = 0.012 * shortest
        offset_expr = f"{offset_scale:.6f}*({intensity_expr})"
        layers.append((shadow_layer, offset_expr, offset_expr))

    current = blank
    for index, (layer, x_expr, y_expr) in enumerate(layers):
        next_label = f"{instance_id}_bg_{index}"
        clauses.append(
            f"[{current}][{layer}]overlay="
            f"x='{x_expr}':y='{y_expr}':eval=frame:shortest=1:format=auto"
            f"[{next_label}]"
        )
        current = next_label

    clauses.append(
        f"[{current}][{main}]overlay=x=0:y=0:shortest=1:format=auto"
        f"[{output_label}]"
    )
    return tuple(clauses)


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


def render_plan_requires_k3_blur(plan: RenderPlan) -> bool:
    if plan.animation_keyframe_contract != "advanced-v1":
        return False
    return any(
        assignment is not None and assignment_has_k3_blur(assignment)
        for scene in plan.scenes
        for assignment in scene.animations
    )


def render_plan_requires_k4_shadow_glow(plan: RenderPlan) -> bool:
    if plan.animation_keyframe_contract != "advanced-v1":
        return False
    return any(
        assignment is not None
        and (
            assignment_has_k4_shadow(assignment)
            or assignment_has_k4_glow(assignment)
        )
        for scene in plan.scenes
        for assignment in scene.animations
    )
