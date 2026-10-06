from __future__ import annotations

from dataclasses import dataclass

from aavc.domain.project.models import ProjectState


@dataclass(frozen=True, slots=True)
class SceneInspectorView:
    scene_number: int
    mode: str
    asset_ids: tuple[str, ...]
    duration_seconds: float


def build_scene_inspector_view(
    project: ProjectState,
    scene_number: int,
) -> SceneInspectorView:
    for scene in project.scenes:
        if scene.scene_number == scene_number:
            return SceneInspectorView(
                scene_number=scene.scene_number,
                mode=scene.mode,
                asset_ids=scene.asset_ids,
                duration_seconds=scene.duration_seconds,
            )
    raise ValueError(f"Scene {scene_number} tidak ditemukan")


def scene_index_for_number(project: ProjectState, scene_number: int | None) -> int:
    if not project.scenes:
        return -1
    if scene_number is None:
        return 0
    for index, scene in enumerate(project.scenes):
        if scene.scene_number == scene_number:
            return index
    return 0
