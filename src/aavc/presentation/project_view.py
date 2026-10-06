from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aavc.domain.project.models import ProjectState


@dataclass(frozen=True, slots=True)
class ProjectSummaryView:
    title: str
    resolution: str
    fps: int
    duration_label: str
    scene_count: int
    asset_count: int
    ready_count: int
    not_ready_count: int
    narration_label: str
    subtitle_label: str


@dataclass(frozen=True, slots=True)
class SceneView:
    scene_number: int
    mode: str
    duration_label: str
    asset_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AssetView:
    asset_id: str
    status: str
    file_label: str
    source_quote: str


def format_duration(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    minutes, remainder = divmod(total_ms, 60_000)
    secs, millis = divmod(remainder, 1000)
    if millis:
        return f"{minutes:02d}:{secs:02d}.{millis:03d}"
    return f"{minutes:02d}:{secs:02d}"


def build_project_summary(project: ProjectState) -> ProjectSummaryView:
    ready_count = sum(binding.status == "READY" for binding in project.bindings)
    return ProjectSummaryView(
        title=project.title,
        resolution=f"{project.width} × {project.height}",
        fps=project.fps,
        duration_label=format_duration(project.duration_seconds),
        scene_count=len(project.scenes),
        asset_count=len(project.bindings),
        ready_count=ready_count,
        not_ready_count=len(project.bindings) - ready_count,
        narration_label=(
            Path(project.narration_audio).name if project.narration_audio else "Belum ada"
        ),
        subtitle_label=(
            Path(project.subtitle_source).name if project.subtitle_source else "Belum ada"
        ),
    )


def build_scene_views(project: ProjectState) -> tuple[SceneView, ...]:
    return tuple(
        SceneView(
            scene_number=scene.scene_number,
            mode=scene.mode,
            duration_label=format_duration(scene.duration_seconds),
            asset_ids=scene.asset_ids,
        )
        for scene in project.scenes
    )


def build_asset_views(project: ProjectState) -> tuple[AssetView, ...]:
    return tuple(
        AssetView(
            asset_id=binding.asset_id,
            status=binding.status,
            file_label=Path(binding.path).name if binding.path else "File belum ditemukan",
            source_quote=binding.source_quote,
        )
        for binding in project.bindings
    )
