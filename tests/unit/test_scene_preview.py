from dataclasses import replace
from pathlib import Path

from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.layout import solve_layout
from aavc.presentation.scene_preview import build_scene_preview_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="preview-live",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_preview_plan_uses_exact_canonical_layout_placements() -> None:
    project = _project()

    for scene in project.scenes:
        plan = build_scene_preview_plan(project, scene)
        placements = solve_layout(scene)

        assert plan.scene_number == scene.scene_number
        assert plan.mode == scene.mode
        assert len(plan.assets) == len(placements)
        for asset, placement in zip(plan.assets, placements, strict=True):
            assert asset.asset_id == placement.asset_id
            assert asset.anchor_x == placement.anchor_x
            assert asset.anchor_y == placement.anchor_y
            assert asset.max_width == placement.max_width
            assert asset.max_height == placement.max_height


def test_preview_plan_exposes_ready_binding_paths() -> None:
    project = _project()
    scene = project.scenes[0]

    plan = build_scene_preview_plan(project, scene)

    assert all(asset.status == "READY" for asset in plan.assets)
    assert all(asset.path is not None for asset in plan.assets)


def test_preview_plan_marks_binding_missing_when_file_is_gone(tmp_path: Path) -> None:
    project = _project()
    scene = project.scenes[0]
    target_id = scene.asset_ids[0]
    bindings = []
    for binding in project.bindings:
        if binding.asset_id == target_id:
            bindings.append(
                replace(
                    binding,
                    path=str(tmp_path / "gone.png"),
                    status="READY",
                )
            )
        else:
            bindings.append(binding)
    project = replace(project, bindings=tuple(bindings))

    plan = build_scene_preview_plan(project, scene)
    target = next(asset for asset in plan.assets if asset.asset_id == target_id)

    assert target.status == "MISSING"
    assert target.path == str(tmp_path / "gone.png")
