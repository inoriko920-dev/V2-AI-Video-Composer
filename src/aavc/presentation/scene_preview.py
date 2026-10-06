from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aavc.domain.layout import solve_layout
from aavc.domain.project.models import ProjectState, Scene


@dataclass(frozen=True, slots=True)
class PreviewAsset:
    asset_id: str
    status: str
    path: str | None
    anchor_x: float
    anchor_y: float
    max_width: float
    max_height: float


@dataclass(frozen=True, slots=True)
class ScenePreviewPlan:
    scene_number: int
    mode: str
    duration_seconds: float
    width: int
    height: int
    assets: tuple[PreviewAsset, ...]


def build_scene_preview_plan(project: ProjectState, scene: Scene) -> ScenePreviewPlan:
    bindings = {binding.asset_id: binding for binding in project.bindings}
    assets: list[PreviewAsset] = []
    for placement in solve_layout(scene):
        binding = bindings.get(placement.asset_id)
        status = binding.status if binding is not None else "MISSING"
        path = binding.path if binding is not None else None
        if path is not None and not Path(path).is_file():
            status = "MISSING"
        assets.append(
            PreviewAsset(
                asset_id=placement.asset_id,
                status=status,
                path=path,
                anchor_x=placement.anchor_x,
                anchor_y=placement.anchor_y,
                max_width=placement.max_width,
                max_height=placement.max_height,
            )
        )
    return ScenePreviewPlan(
        scene_number=scene.scene_number,
        mode=scene.mode,
        duration_seconds=scene.duration_seconds,
        width=project.width,
        height=project.height,
        assets=tuple(assets),
    )
