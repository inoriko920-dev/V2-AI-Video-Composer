from __future__ import annotations

from dataclasses import dataclass, replace

from aavc.animation.registry import validate_effect
from aavc.domain.project.models import AnimationAssignment, ProjectState


@dataclass(frozen=True, slots=True)
class RemoveAnimationAssignment:
    """Remove one asset animation assignment through project history."""

    scene_number: int
    asset_id: str

    def apply(self, project: ProjectState) -> ProjectState:
        valid_targets = {
            (scene.scene_number, asset_id)
            for scene in project.scenes
            for asset_id in scene.asset_ids
        }
        key = (self.scene_number, self.asset_id)
        if key not in valid_targets:
            raise ValueError("Target animasi tidak ada di scene")
        if not any(
            (item.scene_number, item.asset_id) == key
            for item in project.animations
        ):
            raise ValueError("Assignment animasi belum ada pada aset ini")

        animations = tuple(
            item
            for item in project.animations
            if (item.scene_number, item.asset_id) != key
        )
        return replace(project, animations=animations)

    def describe(self) -> str:
        return f"Hapus animasi {self.asset_id} pada Scene {self.scene_number}"


@dataclass(frozen=True, slots=True)
class SetAnimationAssignmentsBatch:
    """Apply a validated animation set atomically as one project-history entry."""

    assignments: tuple[AnimationAssignment, ...]

    def apply(self, project: ProjectState) -> ProjectState:
        if not self.assignments:
            raise ValueError("Batch animasi tidak boleh kosong")

        valid_targets = {
            (scene.scene_number, asset_id)
            for scene in project.scenes
            for asset_id in scene.asset_ids
        }
        existing_by_key = {
            (item.scene_number, item.asset_id): item for item in project.animations
        }
        proposed_by_key: dict[tuple[int, str], AnimationAssignment] = {}

        for assignment in self.assignments:
            key = (assignment.scene_number, assignment.asset_id)
            if key not in valid_targets:
                raise ValueError(
                    f"Target animasi AI tidak ada: Scene {assignment.scene_number} / {assignment.asset_id}"
                )
            if key in proposed_by_key:
                raise ValueError(
                    f"Assignment animasi AI duplikat: Scene {assignment.scene_number} / {assignment.asset_id}"
                )
            validate_effect(assignment.enter_effect)
            validate_effect(assignment.exit_effect)
            if not 0.0 <= assignment.intensity <= 2.0:
                raise ValueError("Intensitas animasi harus 0–2")

            existing = existing_by_key.get(key)
            if existing is not None and existing.locked and assignment != existing:
                raise ValueError(
                    f"Assignment terkunci tidak boleh diganti: Scene {assignment.scene_number} / {assignment.asset_id}"
                )
            proposed_by_key[key] = assignment

        merged = [
            item
            for item in project.animations
            if (item.scene_number, item.asset_id) not in proposed_by_key
        ]
        merged.extend(proposed_by_key.values())
        merged.sort(key=lambda item: (item.scene_number, item.asset_id))
        return replace(project, animations=tuple(merged))

    def describe(self) -> str:
        return f"Terapkan {len(self.assignments)} assignment animasi Auto (AI)"
