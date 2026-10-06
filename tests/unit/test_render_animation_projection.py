from dataclasses import replace
from pathlib import Path

from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment
from aavc.rendering import build_ffmpeg_command, build_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="animation-plan",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_render_plan_uses_none_for_assets_without_assignment(tmp_path: Path) -> None:
    project = _project()
    plan = build_render_plan(project, tmp_path / "out.mp4")

    assert all(
        animation is None
        for scene in plan.scenes
        for animation in scene.animations
    )
    assert all(
        len(scene.animations) == len(scene.asset_paths) == len(scene.placements)
        for scene in plan.scenes
    )


def test_render_plan_projects_partial_assignment_in_asset_order(tmp_path: Path) -> None:
    project = _project()
    scene = next(item for item in project.scenes if len(item.asset_ids) == 2)
    target_asset = scene.asset_ids[1]
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=target_asset,
        enter_effect="Rise",
        exit_effect="Drift",
        intensity=0.75,
        locked=True,
    )
    project = replace(project, animations=(assignment,))

    plan = build_render_plan(project, tmp_path / "out.mp4")
    planned_scene = next(
        item for item in plan.scenes if item.scene_number == scene.scene_number
    )

    assert planned_scene.animations == (None, assignment)
    assert planned_scene.animations[1] is assignment


def test_animation_projection_reaches_ffmpeg_motion_compiler(tmp_path: Path) -> None:
    project = _project()
    scene = project.scenes[0]
    baseline = build_ffmpeg_command(build_render_plan(project, tmp_path / "baseline.mp4"))

    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        enter_effect="Pan",
        exit_effect="Fade",
        intensity=1.25,
        locked=False,
    )
    animated_project = replace(project, animations=(assignment,))
    animated = build_ffmpeg_command(
        build_render_plan(animated_project, tmp_path / "baseline.mp4")
    )

    assert animated != baseline
    baseline_filter = baseline[baseline.index("-filter_complex") + 1]
    animated_filter = animated[animated.index("-filter_complex") + 1]
    assert "overlay=x=(W-w)/2:y=(H-h)/2:shortest=1" in baseline_filter
    assert "overlay=x='((W-w)/2)+" in animated_filter
    assert "W*0.075000" in animated_filter
