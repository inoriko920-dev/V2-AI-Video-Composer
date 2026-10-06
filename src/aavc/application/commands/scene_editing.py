from __future__ import annotations

import math
from dataclasses import dataclass, replace

from aavc.domain.project.models import AnimationAssignment, ProjectState, Scene


def _scene_by_number(project: ProjectState, scene_number: int) -> Scene:
    scene = next(
        (item for item in project.scenes if item.scene_number == scene_number),
        None,
    )
    if scene is None:
        raise ValueError(f"Scene {scene_number} tidak ditemukan")
    return scene


@dataclass(frozen=True, slots=True)
class SetSceneDurationsBatch:
    """Update multiple Scene durations atomically as one history entry."""

    updates: tuple[tuple[int, float], ...]

    def apply(self, project: ProjectState) -> ProjectState:
        if not self.updates:
            raise ValueError("Batch durasi Scene tidak boleh kosong")

        update_map: dict[int, float] = {}
        existing_numbers = {scene.scene_number for scene in project.scenes}
        for scene_number, raw_duration in self.updates:
            if scene_number in update_map:
                raise ValueError(f"Scene {scene_number} muncul dua kali pada batch durasi")
            duration = float(raw_duration)
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError(
                    f"Durasi Scene {scene_number} harus finite dan lebih dari 0"
                )
            if scene_number not in existing_numbers:
                raise ValueError(f"Scene {scene_number} tidak ditemukan")
            update_map[scene_number] = round(duration, 3)

        scenes = tuple(
            replace(
                scene,
                duration_seconds=update_map.get(
                    scene.scene_number,
                    scene.duration_seconds,
                ),
            )
            for scene in project.scenes
        )
        return replace(project, scenes=scenes)

    def describe(self) -> str:
        return f"Ubah durasi {len(self.updates)} Scene"


@dataclass(frozen=True, slots=True)
class CopySceneAnimations:
    """Copy source Scene animation assignments to matching target asset slots."""

    source_scene_number: int
    target_scene_numbers: tuple[int, ...]

    def apply(self, project: ProjectState) -> ProjectState:
        if not self.target_scene_numbers:
            raise ValueError("Target paste animasi tidak boleh kosong")
        if len(self.target_scene_numbers) != len(set(self.target_scene_numbers)):
            raise ValueError("Target paste animasi tidak boleh duplikat")
        if self.source_scene_number in self.target_scene_numbers:
            raise ValueError("Scene sumber tidak boleh menjadi target paste animasi")

        source = _scene_by_number(project, self.source_scene_number)
        source_assignments = {
            item.asset_id: item
            for item in project.animations
            if item.scene_number == source.scene_number
        }
        source_by_slot = tuple(
            source_assignments.get(asset_id) for asset_id in source.asset_ids
        )
        if not any(item is not None for item in source_by_slot):
            raise ValueError(
                f"Scene {source.scene_number} belum memiliki assignment animasi"
            )

        targets = tuple(
            _scene_by_number(project, scene_number)
            for scene_number in self.target_scene_numbers
        )
        for target in targets:
            if len(target.asset_ids) != len(source.asset_ids):
                raise ValueError(
                    "Jumlah slot aset target harus sama dengan Scene sumber: "
                    f"Scene {target.scene_number}"
                )

        existing_by_key = {
            (item.scene_number, item.asset_id): item for item in project.animations
        }
        proposed: dict[tuple[int, str], AnimationAssignment] = {}

        for target in targets:
            for slot_index, source_assignment in enumerate(source_by_slot):
                if source_assignment is None:
                    continue
                target_asset_id = target.asset_ids[slot_index]
                copied = replace(
                    source_assignment,
                    scene_number=target.scene_number,
                    asset_id=target_asset_id,
                )
                key = (target.scene_number, target_asset_id)
                current = existing_by_key.get(key)
                if current is not None and current.locked and current != copied:
                    raise ValueError(
                        "Assignment animasi terkunci tidak boleh ditimpa: "
                        f"Scene {target.scene_number} / {target_asset_id}"
                    )
                proposed[key] = copied

        merged = [
            item
            for item in project.animations
            if (item.scene_number, item.asset_id) not in proposed
        ]
        merged.extend(proposed.values())
        merged.sort(key=lambda item: (item.scene_number, item.asset_id))
        return replace(project, animations=tuple(merged))

    def describe(self) -> str:
        return (
            f"Salin animasi Scene {self.source_scene_number} "
            f"ke {len(self.target_scene_numbers)} Scene"
        )
