from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from aavc.animation import keyframe_track_support_reason
from aavc.animation.compiler import is_native_visual_effect
from aavc.animation.contract import (
    track_requires_advanced,
    validate_project_animation_contract,
)
from aavc.domain.project.models import ProjectState

Severity = Literal["ERROR", "WARNING"]


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    severity: Severity
    message: str
    scene_number: int | None = None
    asset_id: str | None = None


def _path_is_file(value: str | None) -> bool:
    if value is None or not value:
        return False
    return Path(value).expanduser().is_file()


def validate_project(project: ProjectState) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    contract = validate_project_animation_contract(project)
    by_asset = {binding.asset_id: binding for binding in project.bindings}

    if project.narration_audio and not _path_is_file(project.narration_audio):
        issues.append(
            ValidationIssue(
                code="NARRATION_NOT_FOUND",
                severity="ERROR",
                message="File narasi project tidak ditemukan; impor ulang audio narasi",
            )
        )
    if project.subtitle_source and not _path_is_file(project.subtitle_source):
        issues.append(
            ValidationIssue(
                code="SUBTITLE_NOT_FOUND",
                severity="ERROR",
                message="File subtitle project tidak ditemukan; impor ulang subtitle SRT",
            )
        )

    for scene in project.scenes:
        if scene.duration_seconds < 1.0:
            issues.append(
                ValidationIssue(
                    code="SCENE_DURATION_SHORT",
                    severity="WARNING",
                    message=f"Durasi Scene {scene.scene_number} terlalu pendek",
                    scene_number=scene.scene_number,
                )
            )
        for asset_id in scene.asset_ids:
            binding = by_asset.get(asset_id)
            ready = (
                binding is not None
                and binding.status == "READY"
                and _path_is_file(binding.path)
            )
            if not ready:
                issues.append(
                    ValidationIssue(
                        code="ASSET_NOT_READY",
                        severity="ERROR",
                        message=f"{asset_id} belum READY atau file tidak ditemukan",
                        scene_number=scene.scene_number,
                        asset_id=asset_id,
                    )
                )

    for assignment in project.animations:
        if assignment.intensity > 0:
            unsupported = sorted(
                {
                    effect
                    for effect in (assignment.enter_effect, assignment.exit_effect)
                    if not is_native_visual_effect(effect)
                }
            )
            if unsupported:
                effect_names = ", ".join(unsupported)
                issues.append(
                    ValidationIssue(
                        code="VISUAL_EFFECT_FALLBACK",
                        severity="WARNING",
                        message=(
                            f"Efek visual {effect_names} pada {assignment.asset_id} "
                            "belum memiliki compiler native; render akan memakai "
                            "fallback/default transition"
                        ),
                        scene_number=assignment.scene_number,
                        asset_id=assignment.asset_id,
                    )
                )

        for track in assignment.keyframe_tracks:
            if track_requires_advanced(track):
                if contract == "legacy-v3":
                    issues.append(
                        ValidationIssue(
                            code="ADVANCED_TRACK_DORMANT",
                            severity="WARNING",
                            message=(
                                f"Track advanced {track.property_name} pada "
                                f"{assignment.asset_id} tersimpan tetapi belum aktif "
                                "pada schema v3"
                            ),
                            scene_number=assignment.scene_number,
                            asset_id=assignment.asset_id,
                        )
                    )
                else:
                    issues.append(
                        ValidationIssue(
                            code="ADVANCED_BACKEND_UNAVAILABLE",
                            severity="ERROR",
                            message=(
                                f"Track advanced {track.property_name} pada "
                                f"{assignment.asset_id} belum memiliki backend yang "
                                "dipromosikan pada K0"
                            ),
                            scene_number=assignment.scene_number,
                            asset_id=assignment.asset_id,
                        )
                    )
                continue

            reason = keyframe_track_support_reason(track)
            if reason is None:
                continue
            issues.append(
                ValidationIssue(
                    code="KEYFRAME_TRACK_FALLBACK",
                    severity="WARNING",
                    message=(
                        f"Track keyframe {track.property_name} pada "
                        f"{assignment.asset_id} belum aktif penuh: {reason}"
                    ),
                    scene_number=assignment.scene_number,
                    asset_id=assignment.asset_id,
                )
            )

    return tuple(issues)
