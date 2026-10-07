from dataclasses import replace
from pathlib import Path

from aavc.application.services.validation import validate_project
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="zero-intensity-fallback",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _unsupported_assignment(project, *, intensity: float) -> AnimationAssignment:
    scene = project.scenes[0]
    return AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        enter_effect="Legacy Wipe",
        exit_effect="Legacy Blur",
        intensity=intensity,
    )


def test_zero_intensity_unsupported_assignment_has_no_fallback_warning(
    tmp_path: Path,
) -> None:
    project = _project()
    baseline_plan = build_render_plan(project, tmp_path / "out.mp4")
    updated = replace(
        project,
        animations=(_unsupported_assignment(project, intensity=0.0),),
    )
    updated_plan = build_render_plan(updated, tmp_path / "out.mp4")

    assert build_ffmpeg_command(updated_plan) == build_ffmpeg_command(baseline_plan)
    assert not any(
        issue.code == "VISUAL_EFFECT_FALLBACK" for issue in validate_project(updated)
    )
    assert not any(
        issue.code == "VISUAL_EFFECT_FALLBACK"
        for issue in validate_render_plan(updated_plan).issues
    )


def test_active_unsupported_assignment_still_warns_in_both_validation_paths(
    tmp_path: Path,
) -> None:
    project = _project()
    updated = replace(
        project,
        animations=(_unsupported_assignment(project, intensity=1.0),),
    )
    plan = build_render_plan(updated, tmp_path / "out.mp4")

    project_fallback = [
        issue
        for issue in validate_project(updated)
        if issue.code == "VISUAL_EFFECT_FALLBACK"
    ]
    render_fallback = [
        issue
        for issue in validate_render_plan(plan).issues
        if issue.code == "VISUAL_EFFECT_FALLBACK"
    ]

    assert len(project_fallback) == 1
    assert any("Legacy Wipe" in issue.message for issue in render_fallback)
    assert any("Legacy Blur" in issue.message for issue in render_fallback)
