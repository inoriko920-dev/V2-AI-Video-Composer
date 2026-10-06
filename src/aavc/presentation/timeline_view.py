from __future__ import annotations

from dataclasses import dataclass

from aavc.domain.project.models import ProjectState


@dataclass(frozen=True, slots=True)
class TimelineSegment:
    scene_index: int
    scene_number: int
    mode: str
    duration_seconds: float
    start_seconds: float
    end_seconds: float
    fraction: float


@dataclass(frozen=True, slots=True)
class TimelinePlan:
    total_duration_seconds: float
    segments: tuple[TimelineSegment, ...]


def build_timeline_plan(project: ProjectState) -> TimelinePlan:
    total = sum(scene.duration_seconds for scene in project.scenes)
    cursor = 0.0
    segments: list[TimelineSegment] = []

    for index, scene in enumerate(project.scenes):
        start = cursor
        end = start + scene.duration_seconds
        fraction = scene.duration_seconds / total if total > 0 else 0.0
        segments.append(
            TimelineSegment(
                scene_index=index,
                scene_number=scene.scene_number,
                mode=scene.mode,
                duration_seconds=scene.duration_seconds,
                start_seconds=start,
                end_seconds=end,
                fraction=fraction,
            )
        )
        cursor = end

    return TimelinePlan(total_duration_seconds=total, segments=tuple(segments))
