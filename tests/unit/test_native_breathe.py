from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation.compiler import (
    compile_native_alpha_filters,
    compile_native_scale_filter,
    is_native_visual_effect,
)
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.motion_preview import native_visual_preview_scale
from aavc.rendering import build_ffmpeg_command, build_render_plan, validate_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="native-breathe",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _assignment(*, intensity: float = 1.0) -> AnimationAssignment:
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        enter_effect="Breathe",
        exit_effect="Breathe",
        intensity=intensity,
    )


def test_native_breathe_compiles_scale_without_alpha() -> None:
    assignment = _assignment()

    assert is_native_visual_effect("Breathe")
    assert compile_native_alpha_filters(
        assignment,
        duration_seconds=3.0,
    ) == ()
    scale_filter = compile_native_scale_filter(
        assignment,
        duration_seconds=3.0,
    )
    assert scale_filter is not None
    assert "0.98+0.02*t/0.250000" in scale_filter
    assert "1-0.02*(t-2.750000)/0.250000" in scale_filter
    assert ":h=-2:eval=frame" in scale_filter


def test_native_breathe_preview_matches_scale_window() -> None:
    assignment = _assignment()

    assert native_visual_preview_scale(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(0.98)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=0.125,
        duration_seconds=2.0,
    ) == pytest.approx(0.99)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=0.25,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=1.875,
        duration_seconds=2.0,
    ) == pytest.approx(0.99)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=2.0,
        duration_seconds=2.0,
    ) == pytest.approx(0.98)


def test_breathe_reaches_ffmpeg_and_has_no_fallback(tmp_path: Path) -> None:
    project = _project()
    scene = project.scenes[0]
    assignment = replace(
        _assignment(),
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
    )
    updated = replace(project, animations=(assignment,))
    plan = build_render_plan(updated, tmp_path / "breathe.mp4")
    command = " ".join(build_ffmpeg_command(plan))

    assert "0.98+0.02*t/0.250000" in command
    assert "eval=frame" in command
    assert "format=rgba,fade=t=" not in command
    fallback_messages = [
        issue.message
        for issue in validate_render_plan(plan).issues
        if issue.code == "VISUAL_EFFECT_FALLBACK"
    ]
    assert not any("Breathe" in message for message in fallback_messages)


def test_breathe_and_pop_can_use_different_scale_excursions() -> None:
    assignment = AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        enter_effect="Pop",
        exit_effect="Breathe",
        intensity=1.0,
    )

    scale_filter = compile_native_scale_filter(
        assignment,
        duration_seconds=3.0,
    )
    assert scale_filter is not None
    assert "0.85+0.15*t/0.250000" in scale_filter
    assert "1-0.02*(t-2.750000)/0.250000" in scale_filter


def test_zero_intensity_breathe_keeps_baseline_filter_graph(tmp_path: Path) -> None:
    project = _project()
    scene = project.scenes[0]
    baseline = " ".join(
        build_ffmpeg_command(build_render_plan(project, tmp_path / "baseline.mp4"))
    )
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        enter_effect="Breathe",
        exit_effect="Breathe",
        intensity=0.0,
    )
    updated = replace(project, animations=(assignment,))
    command = " ".join(
        build_ffmpeg_command(build_render_plan(updated, tmp_path / "baseline.mp4"))
    )

    assert command == baseline
