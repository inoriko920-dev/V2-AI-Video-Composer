"""Pure geometry contract used by the Qt shell and non-GUI acceptance tests."""
from __future__ import annotations

from dataclasses import dataclass

from aavc.presentation.design_tokens import METRICS


@dataclass(frozen=True, slots=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    def intersects(self, other: Rect) -> bool:
        return not (
            self.x + self.w <= other.x
            or other.x + other.w <= self.x
            or self.y + self.h <= other.y
            or other.y + other.h <= self.y
        )


@dataclass(frozen=True, slots=True)
class ShellGeometry:
    content: Rect
    left: Rect
    preview: Rect
    right: Rect
    timeline: Rect

    @classmethod
    def calculate(cls, width: int, height: int) -> ShellGeometry:
        if width < 1280 or height < 720:
            raise ValueError("STEP 09 minimum supported editor viewport is 1280x720")
        top = METRICS.menu_h + METRICS.toolbar_h
        bottom = METRICS.status_h
        content_h = height - top - bottom
        timeline_h = max(
            METRICS.timeline_min_h,
            min(METRICS.timeline_ref_h, int(content_h * 0.34)),
        )
        upper_h = content_h - timeline_h
        left_w = METRICS.left_ref_w if width >= 1600 else METRICS.left_min_w
        right_w = METRICS.right_ref_w if width >= 1600 else 300
        center_w = width - left_w - right_w
        if center_w < 640:
            right_w = max(0, width - left_w - 640)
            center_w = width - left_w - right_w
        return cls(
            content=Rect(0, top, width, content_h),
            left=Rect(0, top, left_w, upper_h),
            preview=Rect(left_w, top, center_w, upper_h),
            right=Rect(left_w + center_w, top, right_w, upper_h),
            timeline=Rect(0, top + upper_h, width, timeline_h),
        )
