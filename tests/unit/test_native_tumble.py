from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation.compiler import (
    compile_native_rotation_filter,
    is_native_visual_effect,
)
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.motion_preview import native_visual_preview_rotation
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _assignment(*, intensity: float = 1.0) -> AnimationAssignment:
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        enter_effect="Tumble",
        exit_effect="Tumble",
        intensity=intensity,
    )


def _project():
    return create_project_state(
        title="native-tumble",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_native_tumble_rotation_contract_matches_preview_window() -> None:
    assignment = _assignment()

    assert is_native_visual_effect("Tumble")
    rotation_filter = compile_native_rotation_filter(
        assignment,
        duration_seconds=2.0,
    )
    assert rotation_filter is not None
    assert "rotate=a='" in rotation_filter
    assert "0.209440" in rotation_filter
    assert "ow=iw:oh=ih:c=none" in rotation_filter

    assert native_visual_preview_rotation(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(-12.0)
    assert native_visual_preview_rotation(
        assignment,
        time_seconds=0.125,
        duration_seconds=2.0,
    ) == pytest.approx(-6.0)
    assert native_visual_preview_rotation(
        assignment,
        time_seconds=0.25,
        duration_seconds=2.0,
    ) == pytest.approx(0.0)
    assert native_visual_preview_rotation(
        assignment,
        time_seconds=2.0,
        duration_seconds=2.0,
    ) == pytest.approx(12.0)


def test_zero_intensity_tumble_is_identity() -> None:
    assignment = _assignment(intensity=0.0)

    assert compile_native_rotation_filter(
        assignment,
        duration_seconds=2.0,
    ) is None
    assert native_visual_preview_rotation(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(0.0)


def test_native_tumble_reaches_ffmpeg_and_has_no_fallback(tmp_path: Path) -> None:
    project = _project()
    scene = project.scenes[0]
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        enter_effect="Tumble",
        exit_effect="Tumble",
        intensity=1.0,
    )
    project = replace(project, animations=(assignment,))
    plan = build_render_plan(project, tmp_path / "tumble.mp4")
    command = " ".join(build_ffmpeg_command(plan))

    assert "rotate=a='" in command
    assert "0.209440" in command
    fallback_messages = [
        issue.message
        for issue in validate_render_plan(plan).issues
        if issue.code == "VISUAL_EFFECT_FALLBACK"
    ]
    assert not any("Tumble" in message for message in fallback_messages)
