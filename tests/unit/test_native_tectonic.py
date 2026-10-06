from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation.compiler import compile_motion_overlay_position, is_native_visual_effect
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.motion_preview import native_motion_preview_offset
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _assignment(*, intensity: float = 1.0) -> AnimationAssignment:
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        enter_effect="Tectonic",
        exit_effect="Tectonic",
        intensity=intensity,
    )


def _project():
    return create_project_state(
        title="native-tectonic",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_native_tectonic_compiler_and_preview_share_damped_shake_contract() -> None:
    assignment = _assignment()

    assert is_native_visual_effect("Tectonic")
    x_expr, y_expr = compile_motion_overlay_position(
        base_x="(W-w)/2",
        base_y="(H-h)/2",
        assignment=assignment,
        duration_seconds=2.0,
    )
    assert "cos((t/0.250000)*18.849556)" in x_expr
    assert "W*0.012000" in x_expr
    assert "1.750000" in x_expr
    assert y_expr == "(H-h)/2"

    start = native_motion_preview_offset(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    )
    midpoint = native_motion_preview_offset(
        assignment,
        time_seconds=0.125,
        duration_seconds=2.0,
    )
    settled = native_motion_preview_offset(
        assignment,
        time_seconds=0.25,
        duration_seconds=2.0,
    )
    ending = native_motion_preview_offset(
        assignment,
        time_seconds=2.0,
        duration_seconds=2.0,
    )

    assert start.x == pytest.approx(0.012)
    assert midpoint.x == pytest.approx(-0.006)
    assert settled.x == pytest.approx(0.0, abs=1e-9)
    assert ending.x == pytest.approx(0.012)
    assert start.y == midpoint.y == settled.y == ending.y == 0.0


def test_zero_intensity_tectonic_keeps_base_overlay_position() -> None:
    assignment = _assignment(intensity=0.0)

    x_expr, y_expr = compile_motion_overlay_position(
        base_x="(W-w)/2",
        base_y="(H-h)/2",
        assignment=assignment,
        duration_seconds=2.0,
    )
    assert x_expr == "(W-w)/2"
    assert y_expr == "(H-h)/2"
    offset = native_motion_preview_offset(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    )
    assert offset.x == 0.0
    assert offset.y == 0.0


def test_native_tectonic_reaches_ffmpeg_and_has_no_fallback(tmp_path: Path) -> None:
    project = _project()
    scene = project.scenes[0]
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        enter_effect="Tectonic",
        exit_effect="Tectonic",
        intensity=1.0,
    )
    project = replace(project, animations=(assignment,))
    plan = build_render_plan(project, tmp_path / "tectonic.mp4")
    command = " ".join(build_ffmpeg_command(plan))

    assert "18.849556" in command
    assert "W*0.012000" in command
    fallback_messages = [
        issue.message
        for issue in validate_render_plan(plan).issues
        if issue.code == "VISUAL_EFFECT_FALLBACK"
    ]
    assert not any("Tectonic" in message for message in fallback_messages)
