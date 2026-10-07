from __future__ import annotations

import pytest

from aavc.animation import TransformDelta, effect_names, evaluate_effect
from aavc.animation.compiler import (
    NATIVE_VISUAL_ALPHA_EFFECTS,
    NATIVE_VISUAL_EFFECTS,
    NATIVE_VISUAL_MOTION_EFFECTS,
    NATIVE_VISUAL_ROTATION_EFFECTS,
    NATIVE_VISUAL_SCALE_EFFECTS,
    compile_motion_overlay_position,
    compile_native_alpha_filters,
    compile_native_rotation_filter,
    compile_native_scale_filter,
)
from aavc.domain.project.models import AnimationAssignment


@pytest.mark.parametrize("effect", effect_names())
def test_every_registry_effect_has_preview_and_ffmpeg_capability(effect: str) -> None:
    assert effect in NATIVE_VISUAL_EFFECTS

    assignment = AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        enter_effect=effect,
        exit_effect=effect,
        intensity=1.0,
    )

    compiled = False
    if effect in NATIVE_VISUAL_ALPHA_EFFECTS:
        assert compile_native_alpha_filters(
            assignment,
            duration_seconds=2.0,
        )
        compiled = True

    if effect in NATIVE_VISUAL_SCALE_EFFECTS:
        assert compile_native_scale_filter(
            assignment,
            duration_seconds=2.0,
        ) is not None
        compiled = True

    if effect in NATIVE_VISUAL_ROTATION_EFFECTS:
        assert compile_native_rotation_filter(
            assignment,
            duration_seconds=2.0,
        ) is not None
        compiled = True

    if effect in NATIVE_VISUAL_MOTION_EFFECTS:
        x_expr, y_expr = compile_motion_overlay_position(
            base_x="BASE_X",
            base_y="BASE_Y",
            assignment=assignment,
            duration_seconds=2.0,
        )
        assert (x_expr, y_expr) != ("BASE_X", "BASE_Y")
        compiled = True

    assert compiled, f"{effect} has no native FFmpeg capability"
    assert evaluate_effect(effect, 0.0, entering=True) != TransformDelta()


def test_all_21_registry_effects_are_native() -> None:
    assert len(effect_names()) == 21
    assert set(effect_names()) == NATIVE_VISUAL_EFFECTS
