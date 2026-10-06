from __future__ import annotations

from dataclasses import dataclass

from aavc.animation.randomizer import randomize_project_animations
from aavc.domain.project.models import ProjectState


@dataclass(frozen=True, slots=True)
class RandomizeAnimationAssignments:
    seed: int
    scene_numbers: tuple[int, ...] | None = None
    cooldown: int = 2
    effect_pool: tuple[str, ...] | None = None

    def apply(self, project: ProjectState) -> ProjectState:
        if self.scene_numbers is not None:
            existing_scene_numbers = {scene.scene_number for scene in project.scenes}
            missing = sorted(set(self.scene_numbers) - existing_scene_numbers)
            if missing:
                joined = ", ".join(str(number) for number in missing)
                raise ValueError(f"Scene tidak ditemukan: {joined}")

        return randomize_project_animations(
            project,
            seed=self.seed,
            scene_numbers=self.scene_numbers,
            cooldown=self.cooldown,
            effect_pool=self.effect_pool,
        )

    def describe(self) -> str:
        if self.scene_numbers is None:
            scope = "semua Scene"
        else:
            scope = "Scene " + ", ".join(str(number) for number in self.scene_numbers)
        return f"Auto motion {scope} (seed {self.seed})"
