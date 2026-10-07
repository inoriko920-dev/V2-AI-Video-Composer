from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from aavc.animation import keyframe_track_support_reason
from aavc.animation.contract import track_requires_advanced
from aavc.animation.compiler import is_native_visual_effect

from .render_plan import RenderPlan


class PreflightSeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True, slots=True)
class PreflightIssue:
    code: str
    severity: PreflightSeverity
    message: str


@dataclass(frozen=True, slots=True)
class PreflightReport:
    issues: tuple[PreflightIssue, ...]

    @property
    def ok(self) -> bool:
        return not any(
            issue.severity is PreflightSeverity.ERROR for issue in self.issues
        )


def validate_render_plan(plan: RenderPlan) -> PreflightReport:
    issues: list[PreflightIssue] = []
    fallback_effects: set[str] = set()

    if plan.width <= 0 or plan.height <= 0:
        issues.append(
            PreflightIssue(
                "INVALID_FRAME_SIZE",
                PreflightSeverity.ERROR,
                "Resolusi render tidak valid",
            )
        )
    if plan.fps <= 0:
        issues.append(
            PreflightIssue(
                "INVALID_FPS",
                PreflightSeverity.ERROR,
                "FPS harus lebih dari 0",
            )
        )
    if not plan.scenes:
        issues.append(
            PreflightIssue(
                "NO_SCENES",
                PreflightSeverity.ERROR,
                "Render plan tidak memiliki scene",
            )
        )

    seen_scene_numbers: set[int] = set()
    for scene in plan.scenes:
        if scene.scene_number in seen_scene_numbers:
            issues.append(
                PreflightIssue(
                    "DUPLICATE_SCENE_NUMBER",
                    PreflightSeverity.ERROR,
                    f"Scene {scene.scene_number} muncul lebih dari sekali",
                )
            )
        seen_scene_numbers.add(scene.scene_number)
        if scene.duration_seconds <= 0:
            issues.append(
                PreflightIssue(
                    "INVALID_SCENE_DURATION",
                    PreflightSeverity.ERROR,
                    f"Scene {scene.scene_number} memiliki durasi tidak valid",
                )
            )
        if not scene.asset_paths:
            issues.append(
                PreflightIssue(
                    "SCENE_WITHOUT_ASSET",
                    PreflightSeverity.ERROR,
                    f"Scene {scene.scene_number} tidak memiliki aset",
                )
            )
        if scene.animations and len(scene.animations) != len(scene.asset_paths):
            issues.append(
                PreflightIssue(
                    "ANIMATION_SLOT_MISMATCH",
                    PreflightSeverity.ERROR,
                    f"Slot animasi Scene {scene.scene_number} tidak sejajar dengan aset",
                )
            )
        for assignment in scene.animations:
            if assignment is None:
                continue
            if assignment.intensity > 0:
                for effect in {assignment.enter_effect, assignment.exit_effect}:
                    if not is_native_visual_effect(effect):
                        fallback_effects.add(effect)
            for track in assignment.keyframe_tracks:
                if track_requires_advanced(track):
                    if plan.animation_keyframe_contract == "legacy-v3":
                        issues.append(
                            PreflightIssue(
                                "ADVANCED_TRACK_DORMANT",
                                PreflightSeverity.WARNING,
                                "Track keyframe "
                                f"{track.property_name} pada Scene {scene.scene_number}/"
                                f"{assignment.asset_id} tersimpan tetapi dormant pada schema v3",
                            )
                        )
                    else:
                        issues.append(
                            PreflightIssue(
                                "ADVANCED_BACKEND_UNAVAILABLE",
                                PreflightSeverity.ERROR,
                                "Track advanced "
                                f"{track.property_name} pada Scene {scene.scene_number}/"
                                f"{assignment.asset_id} belum memiliki backend yang "
                                "dipromosikan pada K0",
                            )
                        )
                    continue

                reason = keyframe_track_support_reason(track)
                if reason is not None:
                    issues.append(
                        PreflightIssue(
                            "KEYFRAME_TRACK_FALLBACK",
                            PreflightSeverity.WARNING,
                            "Track keyframe "
                            f"{track.property_name} pada Scene {scene.scene_number}/"
                            f"{assignment.asset_id} diabaikan: {reason}",
                        )
                    )
        for asset_path in scene.asset_paths:
            path = Path(asset_path)
            if not path.is_file():
                issues.append(
                    PreflightIssue(
                        "MISSING_ASSET",
                        PreflightSeverity.ERROR,
                        f"Aset render tidak ditemukan: {path.name}",
                    )
                )

    for effect in sorted(fallback_effects):
        issues.append(
            PreflightIssue(
                "VISUAL_EFFECT_FALLBACK",
                PreflightSeverity.WARNING,
                f"Efek visual {effect} belum memiliki compiler native; "
                "efek khusus diabaikan dan transisi Scene default tetap digunakan",
            )
        )

    if plan.narration_audio is not None and not Path(plan.narration_audio).is_file():
        issues.append(
            PreflightIssue(
                "MISSING_NARRATION",
                PreflightSeverity.ERROR,
                "File narasi tidak ditemukan",
            )
        )
    if plan.subtitle_ass is not None and not Path(plan.subtitle_ass).is_file():
        issues.append(
            PreflightIssue(
                "MISSING_SUBTITLE",
                PreflightSeverity.ERROR,
                "File subtitle ASS tidak ditemukan",
            )
        )

    output = Path(plan.output_path)
    if output.suffix.lower() != ".mp4":
        issues.append(
            PreflightIssue(
                "UNEXPECTED_OUTPUT_EXTENSION",
                PreflightSeverity.WARNING,
                "Output final sebaiknya menggunakan ekstensi .mp4",
            )
        )
    if not output.parent.exists():
        issues.append(
            PreflightIssue(
                "OUTPUT_PARENT_MISSING",
                PreflightSeverity.WARNING,
                "Folder output belum ada dan perlu dibuat sebelum render",
            )
        )

    return PreflightReport(tuple(issues))
