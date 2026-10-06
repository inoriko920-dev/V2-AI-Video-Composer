from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from aavc.domain.project.models import AnimationAssignment, ProjectState
from aavc.platform.credentials import CredentialStore
from aavc.providers.adapters.gemini import GeminiProvider
from aavc.providers.base import ProviderRequest
from aavc.providers.key_pool import ApiKeyPool
from aavc.providers.manager import ProviderManager, ProviderRunDiagnostics

DEFAULT_GEMINI_ANIMATION_MODEL = "gemini-3.5-flash-lite"


@dataclass(frozen=True, slots=True)
class AiAnimationPlanResult:
    assignments: tuple[AnimationAssignment, ...]
    diagnostics: ProviderRunDiagnostics


def ai_run_status_text(diagnostics: ProviderRunDiagnostics) -> str:
    health = diagnostics.pool_health
    return (
        f"{diagnostics.attempt_count} attempt; "
        f"{health.available} available / {health.cooldown} cooldown / "
        f"{health.disabled} disabled"
    )


def _unlocked_animation_targets(
    project: ProjectState,
) -> tuple[tuple[int, str, str], ...]:
    locked = {
        (item.scene_number, item.asset_id)
        for item in project.animations
        if item.locked
    }
    targets: list[tuple[int, str, str]] = []
    for scene in project.scenes:
        for index, asset_id in enumerate(scene.asset_ids):
            key = (scene.scene_number, asset_id)
            if key in locked:
                continue
            quote = scene.source_quotes[index] if index < len(scene.source_quotes) else ""
            targets.append((scene.scene_number, asset_id, quote))
    return tuple(targets)


def build_ai_animation_request(
    project: ProjectState,
    *,
    model: str,
    allowed_effects: Sequence[str],
) -> ProviderRequest:
    """Build a bounded prompt that may only propose known project animation targets."""

    normalized_model = model.strip()
    if not normalized_model:
        raise ValueError("Model Gemini tidak boleh kosong")
    effects = tuple(
        dict.fromkeys(effect.strip() for effect in allowed_effects if effect.strip())
    )
    if not effects:
        raise ValueError("Daftar efek Auto (AI) tidak boleh kosong")

    targets = _unlocked_animation_targets(project)
    if not targets:
        raise ValueError(
            "Semua assignment animasi project terkunci; tidak ada target Auto (AI)"
        )

    target_lines = "\n".join(
        (
            f'- scene_number={scene_number}; asset_id="{asset_id}"; '
            f"context={json.dumps(quote, ensure_ascii=False)}"
        )
        for scene_number, asset_id, quote in targets
    )
    schema_example = {
        "assignments": [
            {
                "scene_number": 1,
                "asset_id": "A001",
                "enter_effect": effects[0],
                "exit_effect": effects[0],
                "intensity": 1.0,
            }
        ]
    }
    prompt = (
        "Choose tasteful asset motion for an infographic/documentary video.\n"
        "Return exactly one animation assignment for EVERY target below.\n"
        "Use only the exact allowed effect names. Do not invent scene numbers or asset IDs.\n"
        "Intensity must be a number from 0.0 through 2.0. Prefer restrained motion and avoid repetitive adjacent patterns.\n\n"
        f"ALLOWED_EFFECTS: {json.dumps(effects, ensure_ascii=False)}\n\n"
        f"TARGETS:\n{target_lines}\n\n"
        "Return JSON only, with no Markdown fence or prose, in this shape:\n"
        f"{json.dumps(schema_example, ensure_ascii=False)}"
    )
    return ProviderRequest(
        prompt=prompt,
        model=normalized_model,
        system_instruction=(
            "You are the animation planner inside AI Automatic Video Composer. "
            "Obey the provided target list and JSON schema exactly."
        ),
        temperature=0.35,
        metadata={"feature": "native-animation-auto"},
    )


def _decode_json_object(text: str) -> Mapping[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            lines = lines[1:-1]
            if lines and lines[0].strip().lower() == "json":
                lines = lines[1:]
            stripped = "\n".join(lines).strip()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ValueError("Respons Auto (AI) bukan JSON yang valid") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Respons Auto (AI) harus berupa object JSON")
    return payload


def parse_ai_animation_response(
    text: str,
    project: ProjectState,
    *,
    allowed_effects: Sequence[str],
) -> tuple[AnimationAssignment, ...]:
    """Validate AI JSON completely before any ProjectState mutation is allowed."""

    effects = frozenset(effect.strip() for effect in allowed_effects if effect.strip())
    if not effects:
        raise ValueError("Daftar efek Auto (AI) tidak boleh kosong")
    payload = _decode_json_object(text)
    if set(payload) != {"assignments"}:
        raise ValueError("Respons Auto (AI) memiliki field root yang tidak didukung")
    raw_assignments = payload.get("assignments")
    if not isinstance(raw_assignments, list):
        raise ValueError("Field assignments Auto (AI) harus berupa array")

    target_rows = _unlocked_animation_targets(project)
    required_targets = {
        (scene_number, asset_id) for scene_number, asset_id, _ in target_rows
    }
    if not required_targets:
        raise ValueError("Tidak ada target Auto (AI) yang dapat diubah")
    locked_targets = {
        (item.scene_number, item.asset_id)
        for item in project.animations
        if item.locked
    }

    parsed: list[AnimationAssignment] = []
    seen: set[tuple[int, str]] = set()
    required_fields = {
        "scene_number",
        "asset_id",
        "enter_effect",
        "exit_effect",
        "intensity",
    }
    for raw in raw_assignments:
        if not isinstance(raw, Mapping) or set(raw) != required_fields:
            raise ValueError(
                "Setiap assignment Auto (AI) harus memakai schema yang tepat"
            )

        scene_value = raw.get("scene_number")
        if isinstance(scene_value, bool) or not isinstance(scene_value, int):
            raise ValueError("scene_number Auto (AI) harus integer")
        asset_value = raw.get("asset_id")
        enter_value = raw.get("enter_effect")
        exit_value = raw.get("exit_effect")
        intensity_value = raw.get("intensity")
        if not isinstance(asset_value, str) or not asset_value.strip():
            raise ValueError("asset_id Auto (AI) harus string non-kosong")
        if not isinstance(enter_value, str) or enter_value not in effects:
            raise ValueError(f"Efek masuk Auto (AI) tidak didukung: {enter_value}")
        if not isinstance(exit_value, str) or exit_value not in effects:
            raise ValueError(f"Efek keluar Auto (AI) tidak didukung: {exit_value}")
        if isinstance(intensity_value, bool) or not isinstance(
            intensity_value, (int, float)
        ):
            raise ValueError("intensity Auto (AI) harus angka")
        intensity = float(intensity_value)
        if not 0.0 <= intensity <= 2.0:
            raise ValueError("intensity Auto (AI) harus 0–2")

        key = (scene_value, asset_value)
        if key in locked_targets:
            raise ValueError(
                "Respons Auto (AI) mencoba mengubah assignment terkunci: "
                f"Scene {scene_value} / {asset_value}"
            )
        if key not in required_targets:
            raise ValueError(
                f"Target Auto (AI) tidak ada di project: Scene {scene_value} / {asset_value}"
            )
        if key in seen:
            raise ValueError(
                f"Target Auto (AI) duplikat: Scene {scene_value} / {asset_value}"
            )
        seen.add(key)
        parsed.append(
            AnimationAssignment(
                scene_number=scene_value,
                asset_id=asset_value,
                enter_effect=enter_value,
                exit_effect=exit_value,
                intensity=intensity,
                locked=False,
            )
        )

    missing = required_targets - seen
    if missing:
        missing_text = ", ".join(
            f"Scene {scene_number}/{asset_id}"
            for scene_number, asset_id in sorted(missing)
        )
        raise ValueError(
            f"Respons Auto (AI) tidak lengkap; target hilang: {missing_text}"
        )

    parsed.sort(key=lambda item: (item.scene_number, item.asset_id))
    return tuple(parsed)


def plan_gemini_native_motion_detailed(
    project: ProjectState,
    *,
    credentials: CredentialStore,
    credential_slots: Sequence[int],
    model: str,
    allowed_effects: Sequence[str],
    cancel_requested: Callable[[], bool] | None = None,
    progress_callback: Callable[[float], None] | None = None,
) -> AiAnimationPlanResult:
    """Run one bounded Gemini plan with runtime diagnostics and cancellation."""

    slots = tuple(dict.fromkeys(int(slot) for slot in credential_slots))
    if not slots:
        raise ValueError("Belum ada slot credential Gemini yang terkonfigurasi")

    pool = ApiKeyPool(max_keys=100)
    for slot in slots:
        if slot < 1 or slot > 100:
            raise ValueError("Slot credential Gemini harus 1–100")
        reference = f"gemini-slot-{slot:03d}"
        pool.register(key_id=f"slot-{slot:03d}", credential_ref=reference)

    if progress_callback is not None:
        progress_callback(0.05)
    request = build_ai_animation_request(
        project,
        model=model,
        allowed_effects=allowed_effects,
    )
    manager = ProviderManager(
        provider=GeminiProvider(),
        key_pool=pool,
        credentials=credentials,
        max_attempts=len(slots),
    )
    response, diagnostics = manager.generate_with_diagnostics(
        request,
        cancel_requested=cancel_requested,
        progress_callback=(
            (lambda value: progress_callback(0.10 + value * 0.75))
            if progress_callback is not None
            else None
        ),
    )
    if progress_callback is not None:
        progress_callback(0.90)
    assignments = parse_ai_animation_response(
        response.text,
        project,
        allowed_effects=allowed_effects,
    )
    if progress_callback is not None:
        progress_callback(1.0)
    return AiAnimationPlanResult(assignments, diagnostics)


def plan_gemini_native_motion(
    project: ProjectState,
    *,
    credentials: CredentialStore,
    credential_slots: Sequence[int],
    model: str,
    allowed_effects: Sequence[str],
) -> tuple[AnimationAssignment, ...]:
    """Compatibility wrapper returning only validated animation assignments."""

    return plan_gemini_native_motion_detailed(
        project,
        credentials=credentials,
        credential_slots=credential_slots,
        model=model,
        allowed_effects=allowed_effects,
    ).assignments
