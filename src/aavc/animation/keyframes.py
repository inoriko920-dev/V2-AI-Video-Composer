from __future__ import annotations

from aavc.domain.animation import AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment

ACTIVE_KEYFRAME_PROPERTIES = frozenset(
    {"position_x", "position_y", "scale", "rotation_degrees"}
)
K1_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES = frozenset({"opacity"})
SUPPORTED_KEYFRAME_INTERPOLATIONS = frozenset({"hold", "linear"})
KEYFRAME_PROPERTY_LIMITS: dict[str, tuple[float, float]] = {
    "position_x": (-0.10, 0.10),
    "position_y": (-0.10, 0.10),
    "scale": (0.75, 1.50),
    "rotation_degrees": (-30.0, 30.0),
    "opacity": (0.0, 1.0),
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
) -> str | None:
    if track.property_name not in active_properties:
        return f"property {track.property_name} belum aktif"
    for keyframe in track.keyframes:
        if keyframe.interpolation not in SUPPORTED_KEYFRAME_INTERPOLATIONS:
            return (
                f"interpolation {keyframe.interpolation} belum aktif untuk "
                f"{track.property_name}"
            )
        if keyframe.velocity is not None:
            return f"velocity belum aktif untuk {track.property_name}"
        if keyframe.overshoot is not None:
            return f"overshoot belum aktif untuk {track.property_name}"
    return None


def keyframe_track_support_reason(track: AnimationKeyframeTrack) -> str | None:
    reason = _track_support_reason(
        track,
        active_properties=ACTIVE_KEYFRAME_PROPERTIES,
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
            ACTIVE_KEYFRAME_PROPERTIES | K1_ACTIVE_ADVANCED_KEYFRAME_PROPERTIES
        ),
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
