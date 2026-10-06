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
    if name in {"Rise", "Slide Up"}:
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
    return TransformDelta(opacity=p)
