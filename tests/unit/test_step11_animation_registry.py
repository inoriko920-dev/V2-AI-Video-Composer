from dataclasses import replace
from pathlib import Path

from aavc.animation import effect_names, randomize_project_animations
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="demo",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_registry_has_exact_21_effects() -> None:
    names = effect_names()
    assert len(names) == 21
    assert len(set(names)) == 21
    assert {"Fade", "Pop", "Brush", "Ink", "Spray Paint", "Stomp"}.issubset(names)


def test_randomizer_is_deterministic() -> None:
    project = _project()
    first = randomize_project_animations(project, seed=20261003)
    second = randomize_project_animations(project, seed=20261003)
    assert first.animations == second.animations
    assert len(first.animations) == 3


def test_randomizer_respects_locked_assignment() -> None:
    project = _project()
    locked = AnimationAssignment(1, "A001", enter_effect="Fade", exit_effect="Pop", locked=True)
    project = replace(project, animations=(locked,))
    randomized = randomize_project_animations(project, seed=1)
    result = {(item.scene_number, item.asset_id): item for item in randomized.animations}
    assert result[(1, "A001")] == locked
