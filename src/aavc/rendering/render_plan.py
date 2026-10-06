from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aavc.domain.layout import Placement, solve_layout
from aavc.domain.project.models import (
    AnimationAssignment,
    ProjectState,
    RenderQualitySettings,
)


@dataclass(frozen=True, slots=True)
class SceneRenderPlan:
    scene_number: int
    duration_seconds: float
    asset_paths: tuple[str, ...]
    placements: tuple[Placement, ...]
    animations: tuple[AnimationAssignment | None, ...] = ()


@dataclass(frozen=True, slots=True)
class RenderPlan:
    width: int
    height: int
    fps: int
    scenes: tuple[SceneRenderPlan, ...]
    narration_audio: str | None
    subtitle_ass: str | None
    output_path: str
    quality: RenderQualitySettings

    @property
    def duration_seconds(self) -> float:
        return sum(scene.duration_seconds for scene in self.scenes)


def build_render_plan(
    project: ProjectState,
    output_path: str | Path,
    subtitle_ass: str | None = None,
) -> RenderPlan:
    by_id = {binding.asset_id: binding for binding in project.bindings}
    animations_by_key = {
        (assignment.scene_number, assignment.asset_id): assignment
        for assignment in project.animations
    }
    scenes: list[SceneRenderPlan] = []
    for scene in project.scenes:
        paths: list[str] = []
        animations: list[AnimationAssignment | None] = []
        for asset_id in scene.asset_ids:
            binding = by_id[asset_id]
            if binding.status != "READY" or binding.path is None:
                raise ValueError(f"Asset {asset_id} tidak READY")
            paths.append(binding.path)
            animations.append(
                animations_by_key.get((scene.scene_number, asset_id))
            )
        scenes.append(
            SceneRenderPlan(
                scene_number=scene.scene_number,
                duration_seconds=scene.duration_seconds,
                asset_paths=tuple(paths),
                placements=solve_layout(scene),
                animations=tuple(animations),
            )
        )
    return RenderPlan(
        width=project.width,
        height=project.height,
        fps=project.fps,
        scenes=tuple(scenes),
        narration_audio=project.narration_audio,
        subtitle_ass=subtitle_ass,
        output_path=str(Path(output_path)),
        quality=project.render_quality,
    )
