from __future__ import annotations

import math

from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment

ACTIVE_KEYFRAME_PROPERTIES = frozenset(
    {"position_x", "position_y", "scale", "rotation_degrees"}
)
K1_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES = frozenset({"opacity"})
K2_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES = frozenset(
    {"crop_left", "crop_top", "crop_right", "crop_bottom"}
)
K3_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES = frozenset({"blur"})
K4_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES = frozenset({"shadow", "glow"})
K5_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES = frozenset({"mask_progress"})
ACTIVE_ADVANCED_KEYFRAME_PROPERTIES = (
    K1_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES
    | K2_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES
    | K3_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES
    | K4_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES
    | K5_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES
)
SUPPORTED_KEYFRAME_INTERPOLATIONS = frozenset({"hold", "linear"})
ADVANCED_KEYFRAME_INTERPOLATIONS = frozenset({"hold", "linear", "bezier"})
KEYFRAME_VELOCITY_LIMITS = (0.0, 4.0)
KEYFRAME_OVERSHOOT_LIMITS = (0.0, 0.50)
KEYFRAME_PROPERTY_LIMITS: dict[str, tuple[float, float]] = {
    "position_x": (-0.10, 0.10),
    "position_y": (-0.10, 0.10),
    "scale": (0.75, 1.50),
    "rotation_degrees": (-30.0, 30.0),
    "opacity": (0.0, 1.0),
    "crop_left": (0.0, 0.45),
    "crop_top": (0.0, 0.45),
    "crop_right": (0.0, 0.45),
    "crop_bottom": (0.0, 0.45),
    "blur": (0.0, 1.0),
    "shadow": (0.0, 1.0),
    "glow": (0.0, 1.0),
    "mask_progress": (0.0, 1.0),
}


def find_keyframe_track(
    assignment: AnimationAssignment | None,
    property_name: str,
) -> AnimationKeyframeTrack | None:
    if assignment is None:
        return None
    return next(
        (
            track
            for track in assignment.keyframe_tracks
            if track.property_name == property_name
        ),
        None,
    )


def _track_support_reason(
    track: AnimationKeyframeTrack,
    *,
    active_properties: frozenset[str],
    advanced_semantics: bool,
) -> str | None:
    if track.property_name not in active_properties:
        return f"property {track.property_name} belum aktif"

    interpolations = (
        ADVANCED_KEYFRAME_INTERPOLATIONS
        if advanced_semantics
        else SUPPORTED_KEYFRAME_INTERPOLATIONS
    )
    for keyframe in track.keyframes:
        if keyframe.interpolation not in interpolations:
            return (
                f"interpolation {keyframe.interpolation} belum aktif untuk "
                f"{track.property_name}"
            )
        if not advanced_semantics and keyframe.velocity is not None:
            return f"velocity belum aktif untuk {track.property_name}"
        if not advanced_semantics and keyframe.overshoot is not None:
            return f"overshoot belum aktif untuk {track.property_name}"
    return None


def keyframe_track_support_reason(track: AnimationKeyframeTrack) -> str | None:
    reason = _track_support_reason(
        track,
        active_properties=ACTIVE_KEYFRAME_PROPERTIES,
        advanced_semantics=False,
    )
    if reason is not None and track.property_name not in ACTIVE_KEYFRAME_PROPERTIES:
        return f"property {track.property_name} belum aktif di Wave E"
    return reason


def advanced_keyframe_track_support_reason(
    track: AnimationKeyframeTrack,
) -> str | None:
    return _track_support_reason(
        track,
        active_properties=(
            ACTIVE_KEYFRAME_PROPERTIES | ACTIVE_ADVANCED_KEYFRAME_PROPERTIES
        ),
        advanced_semantics=True,
    )


def is_supported_keyframe_track(track: AnimationKeyframeTrack) -> bool:
    return keyframe_track_support_reason(track) is None


def is_supported_advanced_keyframe_track(track: AnimationKeyframeTrack) -> bool:
    return advanced_keyframe_track_support_reason(track) is None


def clamp_keyframe_value(property_name: str, value: float) -> float:
    limits = KEYFRAME_PROPERTY_LIMITS.get(property_name)
    if limits is None:
        return float(value)
    lower, upper = limits
    return max(lower, min(upper, float(value)))


def clamp_keyframe_velocity(value: float | None) -> float:
    raw = 1.0 if value is None else float(value)
    lower, upper = KEYFRAME_VELOCITY_LIMITS
    return max(lower, min(upper, raw))


def clamp_keyframe_overshoot(value: float | None) -> float:
    raw = 0.0 if value is None else float(value)
    lower, upper = KEYFRAME_OVERSHOOT_LIMITS
    return max(lower, min(upper, raw))


def keyframe_parameter_mismatches(
    track: AnimationKeyframeTrack,
) -> tuple[str, ...]:
    """Return K6 configuration mismatches without changing evaluation."""

    issues: list[str] = []
    points = track.keyframes
    for index, keyframe in enumerate(points):
        previous_is_bezier = (
            index > 0 and points[index - 1].interpolation == "bezier"
        )
        outgoing_is_bezier = (
            index < len(points) - 1 and keyframe.interpolation == "bezier"
        )
        if (
            keyframe.velocity is not None
            and not previous_is_bezier
            and not outgoing_is_bezier
        ):
            issues.append(
                f"velocity keyframe {index + 1} tidak terpakai karena "
                "tidak bersebelahan dengan segmen Bezier"
            )
        if (
            keyframe.overshoot is not None
            and not outgoing_is_bezier
        ):
            issues.append(
                f"overshoot keyframe {index + 1} hanya berlaku pada "
                "segmen Bezier keluar"
            )
    return tuple(issues)


def keyframe_parameter_clamps(
    track: AnimationKeyframeTrack,
) -> tuple[str, ...]:
    issues: list[str] = []
    for index, keyframe in enumerate(track.keyframes):
        if keyframe.velocity is not None and not (
            KEYFRAME_VELOCITY_LIMITS[0]
            <= keyframe.velocity
            <= KEYFRAME_VELOCITY_LIMITS[1]
        ):
            issues.append(
                f"velocity keyframe {index + 1} di-clamp ke rentang 0–4"
            )
        if keyframe.overshoot is not None and not (
            KEYFRAME_OVERSHOOT_LIMITS[0]
            <= keyframe.overshoot
            <= KEYFRAME_OVERSHOOT_LIMITS[1]
        ):
            issues.append(
                f"overshoot keyframe {index + 1} di-clamp ke rentang 0–0,50"
            )
    return tuple(issues)


def _bezier_segment_value(
    start: AnimationKeyframe,
    end: AnimationKeyframe,
    eased: float,
) -> float:
    delta = end.value - start.value
    if delta == 0.0:
        base = start.value
    else:
        m0 = clamp_keyframe_velocity(start.velocity) * delta
        m1 = clamp_keyframe_velocity(end.velocity) * delta
        p0 = start.value
        p1 = start.value + m0 / 3.0
        p2 = end.value - m1 / 3.0
        p3 = end.value
        one_minus = 1.0 - eased
        base = (
            (one_minus ** 3) * p0
            + 3.0 * (one_minus ** 2) * eased * p1
            + 3.0 * one_minus * (eased ** 2) * p2
            + (eased ** 3) * p3
        )

    overshoot = clamp_keyframe_overshoot(start.overshoot)
    if overshoot <= 0.0 or delta == 0.0:
        return base
    return (
        base
        + delta
        * overshoot
        * math.sin(math.pi * eased)
        * eased
    )


def _eased_fraction(easing: str, fraction: float) -> float:
    u = max(0.0, min(1.0, float(fraction)))
    if easing == "ease_in":
        return u * u
    if easing == "ease_out":
        return 1.0 - (1.0 - u) * (1.0 - u)
    if easing == "ease_in_out":
        if u < 0.5:
            return 2.0 * u * u
        return 1.0 - ((-2.0 * u + 2.0) ** 2) / 2.0
    return u


def _evaluate_supported_keyframe_track(
    track: AnimationKeyframeTrack,
    normalized_time: float,
) -> float:
    current = max(0.0, min(1.0, float(normalized_time)))
    points = track.keyframes
    if len(points) == 1 or current <= points[0].time:
        return clamp_keyframe_value(track.property_name, points[0].value)

    for start, end in zip(points, points[1:], strict=False):
        if current > end.time:
            continue
        if start.interpolation == "hold":
            value = start.value if current < end.time else end.value
        else:
            span = end.time - start.time
            fraction = (current - start.time) / span
            eased = _eased_fraction(start.easing, fraction)
            if start.interpolation == "bezier":
                value = _bezier_segment_value(start, end, eased)
            else:
                value = start.value + (end.value - start.value) * eased
        return clamp_keyframe_value(track.property_name, value)

    return clamp_keyframe_value(track.property_name, points[-1].value)


def evaluate_keyframe_track(
    track: AnimationKeyframeTrack,
    normalized_time: float,
) -> float:
    if not is_supported_keyframe_track(track):
        raise ValueError(
            keyframe_track_support_reason(track) or "Track keyframe tidak didukung"
        )
    return _evaluate_supported_keyframe_track(track, normalized_time)


def evaluate_advanced_keyframe_track(
    track: AnimationKeyframeTrack,
    normalized_time: float,
) -> float:
    if not is_supported_advanced_keyframe_track(track):
        raise ValueError(
            advanced_keyframe_track_support_reason(track)
            or "Track keyframe advanced tidak didukung"
        )
    return _evaluate_supported_keyframe_track(track, normalized_time)


def evaluate_assignment_keyframe(
    assignment: AnimationAssignment | None,
    property_name: str,
    normalized_time: float,
) -> float | None:
    track = find_keyframe_track(assignment, property_name)
    if track is None or not is_supported_keyframe_track(track):
        return None
    return evaluate_keyframe_track(track, normalized_time)


def evaluate_assignment_advanced_keyframe(
    assignment: AnimationAssignment | None,
    property_name: str,
    normalized_time: float,
) -> float | None:
    track = find_keyframe_track(assignment, property_name)
    if track is None or not is_supported_advanced_keyframe_track(track):
        return None
    return evaluate_advanced_keyframe_track(track, normalized_time)



def evaluate_assignment_keyframe_with_contract(
    assignment: AnimationAssignment | None,
    property_name: str,
    normalized_time: float,
    *,
    advanced_semantics: bool,
) -> float | None:
    if advanced_semantics:
        return evaluate_assignment_advanced_keyframe(
            assignment,
            property_name,
            normalized_time,
        )
    return evaluate_assignment_keyframe(
        assignment,
        property_name,
        normalized_time,
    )
