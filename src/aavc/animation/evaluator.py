from __future__ import annotations

import math
from dataclasses import dataclass

from .registry import validate_effect


@dataclass(frozen=True, slots=True)
class TransformDelta:
    opacity: float = 1.0
    scale: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    rotation_degrees: float = 0.0


def evaluate_effect(name: str, progress: float, *, entering: bool = True) -> TransformDelta:
    """Evaluate conservative animation primitives without mutating base layout."""
    validate_effect(name)
    p = max(0.0, min(1.0, progress))
    if not entering:
        p = 1.0 - p

    if name == "Fade":
        return TransformDelta(opacity=p)
    if name in {"Pop", "Stomp"}:
        return TransformDelta(opacity=p, scale=0.85 + 0.15 * p)
    if name == "Rise":
        return TransformDelta(opacity=p, offset_y=(1.0 - p) * 0.08)
    if name in {"Pan", "Drift"}:
        return TransformDelta(opacity=p, offset_x=(1.0 - p) * 0.06)
    if name == "Tectonic":
        return TransformDelta(
            offset_x=math.cos(p * 6.0 * math.pi) * (1.0 - p) * 0.012
        )
    if name == "Breathe":
        return TransformDelta(opacity=1.0, scale=0.98 + 0.02 * p)
    if name == "Tumble":
        direction = -1.0 if entering else 1.0
        return TransformDelta(rotation_degrees=direction * 12.0 * (1.0 - p))

    # V2 production implementations for the registry effects that previously fell
    # back to the Scene transition.  These intentionally reuse the same bounded
    # transform primitives consumed by preview and FFmpeg so parity stays testable.
    if name == "Wipe":
        return TransformDelta(opacity=p, offset_x=(1.0 - p) * 0.10)
    if name == "Blur":
        return TransformDelta(opacity=p, scale=1.06 - 0.06 * p)
    if name == "Succession":
        return TransformDelta(opacity=p, offset_y=(1.0 - p) * 0.045)
    if name == "Baseline":
        return TransformDelta(opacity=p, offset_y=-(1.0 - p) * 0.030)
    if name == "Neon":
        return TransformDelta(opacity=p, scale=0.96 + 0.04 * p)
    if name == "Scrapbook":
        direction = -1.0 if entering else 1.0
        return TransformDelta(
            opacity=p,
            scale=0.92 + 0.08 * p,
            rotation_degrees=direction * 8.0 * (1.0 - p),
        )
    if name == "Brush":
        return TransformDelta(opacity=p, offset_x=-(1.0 - p) * 0.080)
    if name == "Ink":
        return TransformDelta(opacity=p, scale=0.90 + 0.10 * p)
    if name == "Digital":
        return TransformDelta(
            opacity=p,
            offset_x=math.cos(p * 8.0 * math.pi) * (1.0 - p) * 0.020,
        )
    if name == "Spray Paint":
        return TransformDelta(
            opacity=p,
            scale=0.94 + 0.06 * p,
            offset_y=math.cos(p * 4.0 * math.pi) * (1.0 - p) * 0.015,
        )
    if name == "Sketch":
        direction = -1.0 if entering else 1.0
        return TransformDelta(
            opacity=p,
            rotation_degrees=direction * 4.0 * (1.0 - p),
        )
    if name == "Gradient":
        return TransformDelta(opacity=p, offset_x=(1.0 - p) * 0.030)

    # validate_effect() makes this unreachable for the canonical registry, but keep
    # a neutral fail-safe if the registry is extended without updating the evaluator.
    return TransformDelta()
