from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

KeyframeInterpolation = Literal["hold", "linear", "bezier"]
KeyframeEasing = Literal["linear", "ease_in", "ease_out", "ease_in_out"]
TransformProperty = Literal[
    "position_x",
    "position_y",
    "scale",
    "rotation_degrees",
    "opacity",
    "crop_left",
    "crop_top",
    "crop_right",
    "crop_bottom",
    "blur",
    "shadow",
    "glow",
    "mask_progress",
]

KEYFRAME_INTERPOLATIONS = frozenset({"hold", "linear", "bezier"})
KEYFRAME_EASINGS = frozenset({"linear", "ease_in", "ease_out", "ease_in_out"})
TRANSFORM_PROPERTIES = frozenset(
    {
        "position_x",
        "position_y",
        "scale",
        "rotation_degrees",
        "opacity",
        "crop_left",
        "crop_top",
        "crop_right",
        "crop_bottom",
        "blur",
        "shadow",
        "glow",
        "mask_progress",
    }
)


@dataclass(frozen=True, slots=True)
class AnimationKeyframe:
    """Backend-neutral scalar keyframe using normalized scene time."""

    time: float
    value: float
    interpolation: KeyframeInterpolation = "linear"
    easing: KeyframeEasing = "linear"
    velocity: float | None = None
    overshoot: float | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.time) or not 0.0 <= self.time <= 1.0:
            raise ValueError("Waktu keyframe harus finite pada rentang 0–1")
        if not math.isfinite(self.value):
            raise ValueError("Nilai keyframe harus finite")
        if self.interpolation not in KEYFRAME_INTERPOLATIONS:
            raise ValueError(
                f"Interpolasi keyframe tidak didukung: {self.interpolation}"
            )
        if self.easing not in KEYFRAME_EASINGS:
            raise ValueError(f"Easing keyframe tidak didukung: {self.easing}")
        if self.velocity is not None and not math.isfinite(self.velocity):
            raise ValueError("Velocity keyframe harus finite")
        if self.overshoot is not None:
            if not math.isfinite(self.overshoot) or self.overshoot < 0:
                raise ValueError("Overshoot keyframe harus finite dan tidak negatif")


@dataclass(frozen=True, slots=True)
class AnimationKeyframeTrack:
    """One scalar transform property animated by ordered normalized keyframes."""

    property_name: TransformProperty
    keyframes: tuple[AnimationKeyframe, ...]

    def __post_init__(self) -> None:
        if self.property_name not in TRANSFORM_PROPERTIES:
            raise ValueError(
                f"Property keyframe tidak didukung: {self.property_name}"
            )
        if not self.keyframes:
            raise ValueError("Track keyframe harus memiliki minimal satu keyframe")
        previous = -1.0
        for keyframe in self.keyframes:
            if keyframe.time <= previous:
                raise ValueError(
                    "Waktu keyframe dalam satu track harus unik dan meningkat"
                )
            previous = keyframe.time
