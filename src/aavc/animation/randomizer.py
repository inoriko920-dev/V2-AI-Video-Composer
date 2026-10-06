from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import replace

from aavc.domain.project.models import AnimationAssignment, ProjectState

from .registry import effect_names, validate_effect


def _existing_by_key(project: ProjectState) -> dict[tuple[int, str], AnimationAssignment]:
    return {(item.scene_number, item.asset_id): item for item in project.animations}


def _normalize_effect_pool(effect_pool: Iterable[str] | None) -> list[str]:
    if effect_pool is None:
        return list(effect_names())

    names = list(dict.fromkeys(effect_pool))
    if len(names) < 2:
        raise ValueError("Effect pool harus memiliki minimal dua efek berbeda")
    for name in names:
        validate_effect(name)
    return names


def randomize_project_animations(
    project: ProjectState,
    *,
    seed: int,
    scene_numbers: Iterable[int] | None = None,
    cooldown: int = 2,
    effect_pool: Iterable[str] | None = None,
) -> ProjectState:
    """Assign deterministic visual effects while respecting locks and cooldown."""
    if cooldown < 0:
        raise ValueError("Cooldown animasi tidak boleh negatif")

    rng = random.Random(seed)
    allowed_scenes = set(scene_numbers) if scene_numbers is not None else None
    names = _normalize_effect_pool(effect_pool)
    existing = _existing_by_key(project)
    recent: list[str] = []
    output: list[AnimationAssignment] = []

    for scene in project.scenes:
        for asset_id in scene.asset_ids:
            key = (scene.scene_number, asset_id)
            prior = existing.get(key)
            if prior is not None and prior.locked:
                output.append(prior)
                recent.append(prior.enter_effect)
                recent[:] = recent[-cooldown:]
                continue
            if allowed_scenes is not None and scene.scene_number not in allowed_scenes:
                if prior is not None:
                    output.append(prior)
                continue

            candidates = [name for name in names if name not in recent[-cooldown:]] or names
            enter = rng.choice(candidates)
            exit_candidates = [name for name in names if name != enter]
            exit_effect = rng.choice(exit_candidates)
            output.append(
                AnimationAssignment(
                    scene_number=scene.scene_number,
                    asset_id=asset_id,
                    enter_effect=enter,
                    exit_effect=exit_effect,
                    intensity=1.0,
                    locked=False,
                )
            )
            recent.append(enter)
            recent[:] = recent[-cooldown:]

    keys = {(item.scene_number, item.asset_id) for item in output}
    for item in project.animations:
        if (item.scene_number, item.asset_id) not in keys:
            output.append(item)

    output.sort(key=lambda item: (item.scene_number, item.asset_id))
    metadata = {**project.metadata, "animation_seed": str(seed)}
    return replace(project, animations=tuple(output), metadata=metadata)
