from aavc.animation.compiler import (
    NATIVE_VISUAL_ALPHA_EFFECTS,
    NATIVE_VISUAL_EFFECTS,
    NATIVE_VISUAL_MOTION_EFFECTS,
    NATIVE_VISUAL_ROTATION_EFFECTS,
    NATIVE_VISUAL_SCALE_EFFECTS,
    native_visual_effect_names,
)
from aavc.animation.registry import effect_names
from aavc.presentation.dialogs.asset_motion import NATIVE_MOTION_CHOICES


def test_native_effect_choices_share_one_ordered_source() -> None:
    assert native_visual_effect_names() == effect_names()
    assert len(native_visual_effect_names()) == 21
    assert native_visual_effect_names() == NATIVE_MOTION_CHOICES
    assert frozenset(NATIVE_MOTION_CHOICES) == NATIVE_VISUAL_EFFECTS


def test_native_capability_sets_cover_exact_native_effect_set() -> None:
    capability_union = (
        NATIVE_VISUAL_ALPHA_EFFECTS
        | NATIVE_VISUAL_MOTION_EFFECTS
        | NATIVE_VISUAL_ROTATION_EFFECTS
        | NATIVE_VISUAL_SCALE_EFFECTS
    )
    assert capability_union == NATIVE_VISUAL_EFFECTS
    assert frozenset(effect_names()) >= NATIVE_VISUAL_EFFECTS
