import pytest

from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.motion_preview import (
    native_visual_preview_opacity,
    native_visual_preview_scale,
)


def _assignment(*, intensity: float = 1.0) -> AnimationAssignment:
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        enter_effect="Stomp",
        exit_effect="Stomp",
        intensity=intensity,
    )


def test_native_stomp_preview_matches_scale_and_alpha_window() -> None:
    assignment = _assignment()

    assert native_visual_preview_scale(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(0.85)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=0.125,
        duration_seconds=2.0,
    ) == pytest.approx(0.925)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=0.25,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)
    assert native_visual_preview_opacity(
        assignment,
        time_seconds=0.125,
        duration_seconds=2.0,
    ) == pytest.approx(0.5)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=2.0,
        duration_seconds=2.0,
    ) == pytest.approx(0.85)
    assert native_visual_preview_opacity(
        assignment,
        time_seconds=2.0,
        duration_seconds=2.0,
    ) == pytest.approx(0.0)


def test_zero_intensity_stomp_is_identity_and_opaque() -> None:
    assignment = _assignment(intensity=0.0)

    assert native_visual_preview_scale(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)
    assert native_visual_preview_opacity(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)
