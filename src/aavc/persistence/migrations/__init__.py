from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

Migration = Callable[[dict[str, Any]], dict[str, Any]]


def _v1_to_v2(payload: dict[str, Any]) -> dict[str, Any]:
    migrated = deepcopy(payload)
    migrated.setdefault("animations", [])
    migrated.setdefault("subtitle_style", {})
    migrated.setdefault("subtitle_animation", {})
    migrated.setdefault("render_quality", {})
    migrated.setdefault("metadata", {})
    migrated["schema_version"] = 2
    return migrated


def _v2_to_v3(payload: dict[str, Any]) -> dict[str, Any]:
    migrated = deepcopy(payload)
    animations = migrated.get("animations")
    if isinstance(animations, list):
        for raw in animations:
            if isinstance(raw, dict):
                raw.setdefault("keyframe_tracks", [])
    migrated["schema_version"] = 3
    return migrated


_MIGRATIONS: dict[int, Migration] = {
    1: _v1_to_v2,
    2: _v2_to_v3,
}


def migrate_project_payload(
    payload: dict[str, Any],
    *,
    source_version: int,
    target_version: int,
) -> dict[str, Any]:
    """Migrate a parsed project document without mutating the caller payload."""

    if source_version < 1:
        raise ValueError("Versi schema project harus >= 1")
    if source_version > target_version:
        raise ValueError(
            f"Tidak dapat menurunkan schema {source_version} ke {target_version}"
        )

    migrated = deepcopy(payload)
    version = source_version
    while version < target_version:
        migration = _MIGRATIONS.get(version)
        if migration is None:
            raise ValueError(
                f"Migrasi schema {version} ke {version + 1} tidak tersedia"
            )
        migrated = migration(migrated)
        version += 1

    migrated["schema_version"] = target_version
    return migrated
