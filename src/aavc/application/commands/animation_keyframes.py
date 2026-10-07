from __future__ import annotations

from dataclasses import dataclass, replace

from aavc.animation.contract import (
    ADVANCED_KEYFRAME_CONTRACT,
    ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY,
    ADVANCED_SCHEMA_VERSION,
    dormant_advanced_track_locations,
    track_requires_advanced,
    validate_project_animation_contract,
)
from aavc.animation.keyframes import advanced_keyframe_track_support_reason
from aavc.application.commands.project_commands import SetAnimationAssignment
from aavc.domain.animation import AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment, ProjectState


class AdvancedAnimationActivationRequired(ValueError):
    """Signal that a legacy-v3 edit needs explicit advanced-v1 activation."""

    def __init__(
        self,
        *,
        scene_number: int,
        asset_id: str,
        changed_properties: tuple[str, ...],
        dormant_locations: tuple[tuple[int, str, str], ...],
        requires_dormant_acknowledgement: bool,
    ) -> None:
        self.scene_number = scene_number
        self.asset_id = asset_id
        self.changed_properties = changed_properties
        self.dormant_locations = dormant_locations
        self.requires_dormant_acknowledgement = (
            requires_dormant_acknowledgement
        )
        super().__init__(
            "Advanced Animation harus diaktifkan sebelum edit advanced dapat diterapkan"
        )


def _track_map(
    assignment: AnimationAssignment | None,
) -> dict[str, AnimationKeyframeTrack]:
    if assignment is None:
        return {}
    return {track.property_name: track for track in assignment.keyframe_tracks}


def _changed_advanced_properties(
    existing: AnimationAssignment | None,
    proposed: AnimationAssignment,
) -> tuple[str, ...]:
    existing_tracks = _track_map(existing)
    changed: list[str] = []
    for track in proposed.keyframe_tracks:
        if existing_tracks.get(track.property_name) == track:
            continue
        reason = advanced_keyframe_track_support_reason(track)
        if reason is not None:
            raise ValueError(reason)
        if track_requires_advanced(track):
            changed.append(track.property_name)
    return tuple(changed)


def _target_exists(project: ProjectState, assignment: AnimationAssignment) -> bool:
    return any(
        scene.scene_number == assignment.scene_number
        and assignment.asset_id in scene.asset_ids
        for scene in project.scenes
    )


@dataclass(frozen=True, slots=True)
class ApplyAnimationKeyframeEdit:
    """Apply one asset preset/keyframe working copy as one history mutation."""

    assignment: AnimationAssignment
    activate_advanced: bool = False
    acknowledge_dormant: bool = False

    def apply(self, project: ProjectState) -> ProjectState:
        if not _target_exists(project, self.assignment):
            raise ValueError("Target animasi tidak ada di scene")
        if not 0.0 <= self.assignment.intensity <= 2.0:
            raise ValueError("Intensitas animasi harus 0–2")

        contract = validate_project_animation_contract(project)
        existing = next(
            (
                item
                for item in project.animations
                if item.scene_number == self.assignment.scene_number
                and item.asset_id == self.assignment.asset_id
            ),
            None,
        )

        for track in self.assignment.keyframe_tracks:
            reason = advanced_keyframe_track_support_reason(track)
            if reason is not None:
                raise ValueError(reason)

        changed_advanced = _changed_advanced_properties(existing, self.assignment)
        candidate = project
        if contract == "legacy-v3" and changed_advanced:
            dormant = dormant_advanced_track_locations(project)
            changed_locations = {
                (
                    self.assignment.scene_number,
                    self.assignment.asset_id,
                    property_name,
                )
                for property_name in changed_advanced
            }
            unrelated = tuple(
                location for location in dormant if location not in changed_locations
            )
            needs_ack = bool(unrelated)
            if not self.activate_advanced or (
                needs_ack and not self.acknowledge_dormant
            ):
                raise AdvancedAnimationActivationRequired(
                    scene_number=self.assignment.scene_number,
                    asset_id=self.assignment.asset_id,
                    changed_properties=changed_advanced,
                    dormant_locations=dormant,
                    requires_dormant_acknowledgement=needs_ack,
                )

            metadata = dict(project.metadata)
            metadata[ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY] = (
                ADVANCED_KEYFRAME_CONTRACT
            )
            candidate = replace(
                project,
                schema_version=ADVANCED_SCHEMA_VERSION,
                metadata=metadata,
            )

        return SetAnimationAssignment(self.assignment).apply(candidate)

    def describe(self) -> str:
        return (
            "Terapkan editor animasi "
            f"{self.assignment.asset_id} pada Scene {self.assignment.scene_number}"
        )


@dataclass(frozen=True, slots=True)
class RemoveAnimationKeyframeTrack:
    """Remove one property track without implicit schema promotion/demotion."""

    scene_number: int
    asset_id: str
    property_name: str

    def apply(self, project: ProjectState) -> ProjectState:
        validate_project_animation_contract(project)
        existing = next(
            (
                item
                for item in project.animations
                if item.scene_number == self.scene_number
                and item.asset_id == self.asset_id
            ),
            None,
        )
        if existing is None:
            raise ValueError("Assignment animasi belum ada pada aset ini")
        if not any(
            track.property_name == self.property_name
            for track in existing.keyframe_tracks
        ):
            raise ValueError("Track keyframe belum ada pada aset ini")

        tracks = tuple(
            track
            for track in existing.keyframe_tracks
            if track.property_name != self.property_name
        )
        updated = replace(existing, keyframe_tracks=tracks)
        return SetAnimationAssignment(updated).apply(project)

    def describe(self) -> str:
        return (
            f"Hapus track {self.property_name} dari {self.asset_id} "
            f"pada Scene {self.scene_number}"
        )
