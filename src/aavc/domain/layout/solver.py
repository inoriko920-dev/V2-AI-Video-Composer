from __future__ import annotations

from dataclasses import dataclass

from aavc.domain.project.models import Scene


@dataclass(frozen=True, slots=True)
class Placement:
    asset_id: str
    anchor_x: float
    anchor_y: float
    max_width: float
    max_height: float


def solve_layout(scene: Scene) -> tuple[Placement, ...]:
    if scene.mode == "SINGLE":
        return (Placement(scene.asset_ids[0], 0.50, 0.47, 0.72, 0.84),)
    return (
        Placement(scene.asset_ids[0], 0.255, 0.50, 0.47, 0.66),
        Placement(scene.asset_ids[1], 0.745, 0.50, 0.47, 0.66),
    )
