from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from aavc.domain.animation import AnimationKeyframeTrack

if TYPE_CHECKING:
    from aavc.domain.project.models import ProjectState

LEGACY_SCHEMA_VERSION = 3
ADVANCED_SCHEMA_VERSION = 4
MAX_SUPPORTED_SCHEMA_VERSION = ADVANCED_SCHEMA_VERSION
AUTOMATIC_MIGRATION_SCHEMA_VERSION = LEGACY_SCHEMA_VERSION

ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY = "animation_keyframe_contract"
ADVANCED_KEYFRAME_CONTRACT = "advanced-v1"

FOUNDATIONAL_KEYFRAME_PROPERTIES = frozenset(
    {"position_x", "position_y", "scale", "rotation_degrees"}
)
ADVANCED_KEYFRAME_PROPERTIES = frozenset(
    {
        "opacity",
        "crop_left",
        "crop_top",
        "crop_right",
        "crop_bottom",
        "blur",
        "shadow",
        "glow",
        "mask_progress",
    }
)

ResolvedAnimationKeyframeContract = Literal["legacy-v3", "advanced-v1"]


def track_requires_advanced(track: AnimationKeyframeTrack) -> bool:
    if track.property_name in ADVANCED_KEYFRAME_PROPERTIES:
        return True
    return any(
        keyframe.interpolation == "bezier"
        or keyframe.velocity is not None
        or keyframe.overshoot is not None
        for keyframe in track.keyframes
    )


def resolve_animation_keyframe_contract(
    schema_version: int,
    metadata: dict[str, str],
) -> ResolvedAnimationKeyframeContract:
    marker = metadata.get(ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY)

    if schema_version == LEGACY_SCHEMA_VERSION:
        if marker is not None:
            raise ValueError(
                "ADVANCED_CONTRACT_SCHEMA_MISMATCH: schema v3 tidak boleh memiliki "
                f"{ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY}"
            )
        return "legacy-v3"

    if schema_version == ADVANCED_SCHEMA_VERSION:
        if marker != ADVANCED_KEYFRAME_CONTRACT:
            raise ValueError(
                "ADVANCED_CONTRACT_INVALID: schema v4 wajib memiliki "
                f'{ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY}="{ADVANCED_KEYFRAME_CONTRACT}"'
            )
        return "advanced-v1"

    if schema_version > MAX_SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            "Versi project tidak didukung: "
            f"schema {schema_version} lebih baru dari schema "
            f"{MAX_SUPPORTED_SCHEMA_VERSION} yang didukung aplikasi ini"
        )

    raise ValueError(
        "Versi project harus dimigrasikan ke schema v3 sebelum contract animation "
        f"di-resolve; diterima schema {schema_version}"
    )


def validate_project_animation_contract(
    project: ProjectState,
) -> ResolvedAnimationKeyframeContract:
    return resolve_animation_keyframe_contract(project.schema_version, project.metadata)


def advanced_track_locations(
    project: ProjectState,
) -> tuple[tuple[int, str, str], ...]:
    locations: list[tuple[int, str, str]] = []
    for assignment in project.animations:
        for track in assignment.keyframe_tracks:
            if track_requires_advanced(track):
                locations.append(
                    (
                        assignment.scene_number,
                        assignment.asset_id,
                        track.property_name,
                    )
                )
    return tuple(locations)


def dormant_advanced_track_locations(
    project: ProjectState,
) -> tuple[tuple[int, str, str], ...]:
    if validate_project_animation_contract(project) != "legacy-v3":
        return ()
    return advanced_track_locations(project)
