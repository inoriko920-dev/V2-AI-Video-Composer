import pytest

from aavc.domain.project.models import SubtitleAnimationSettings
from aavc.presentation.subtitle_preview import (
    active_subtitle_cue,
    subtitle_animation_transform,
)
from aavc.subtitles.srt import SubtitleCue


def _cues() -> tuple[SubtitleCue, ...]:
    return (
        SubtitleCue(index=1, start_seconds=0.5, end_seconds=1.5, text="Pertama"),
        SubtitleCue(index=2, start_seconds=2.0, end_seconds=3.0, text="Kedua\\NBaris"),
    )


def _cue() -> SubtitleCue:
    return SubtitleCue(index=1, start_seconds=1.0, end_seconds=3.0, text="Animasi")


def test_active_subtitle_cue_uses_start_inclusive_end_exclusive_boundaries() -> None:
    cues = _cues()

    assert active_subtitle_cue(cues, 0.49) is None
    assert active_subtitle_cue(cues, 0.5) == cues[0]
    assert active_subtitle_cue(cues, 1.499) == cues[0]
    assert active_subtitle_cue(cues, 1.5) is None
    assert active_subtitle_cue(cues, 2.0) == cues[1]
    assert active_subtitle_cue(cues, 3.0) is None


def test_active_subtitle_cue_clamps_negative_time_to_zero() -> None:
    cue = SubtitleCue(index=1, start_seconds=0.0, end_seconds=1.0, text="Mulai")

    assert active_subtitle_cue((cue,), -2.0) == cue


def test_active_subtitle_cue_returns_none_for_empty_input() -> None:
    assert active_subtitle_cue((), 1.0) is None


def test_fade_transform_fades_in_and_out_using_project_durations() -> None:
    animation = SubtitleAnimationSettings(
        preset="Fade",
        enter_duration_ms=500,
        exit_duration_ms=500,
    )

    start = subtitle_animation_transform(_cue(), 1.0, animation)
    enter_half = subtitle_animation_transform(_cue(), 1.25, animation)
    settled = subtitle_animation_transform(_cue(), 2.0, animation)
    exit_half = subtitle_animation_transform(_cue(), 2.75, animation)

    assert start.opacity == pytest.approx(0.0)
    assert enter_half.opacity == pytest.approx(0.5)
    assert settled.opacity == pytest.approx(1.0)
    assert exit_half.opacity == pytest.approx(0.5)
    assert settled.scale == pytest.approx(1.0)
    assert settled.vertical_offset == pytest.approx(0.0)


def test_clean_documentary_uses_same_fade_semantics() -> None:
    animation = SubtitleAnimationSettings(
        preset="Clean Documentary",
        enter_duration_ms=250,
        exit_duration_ms=250,
    )

    transform = subtitle_animation_transform(_cue(), 1.125, animation)

    assert transform.opacity == pytest.approx(0.5)
    assert transform.scale == pytest.approx(1.0)


def test_pop_uses_fixed_ass_scale_and_fade() -> None:
    animation = SubtitleAnimationSettings(
        preset="Pop",
        enter_duration_ms=250,
        exit_duration_ms=250,
        intensity=2.0,
    )

    transform = subtitle_animation_transform(_cue(), 2.0, animation)

    assert transform.opacity == pytest.approx(1.0)
    assert transform.scale == pytest.approx(1.05)
    assert transform.vertical_offset == pytest.approx(0.0)


def test_slide_up_moves_80_project_pixels_during_enter_only() -> None:
    animation = SubtitleAnimationSettings(
        preset="Slide Up",
        enter_duration_ms=400,
        exit_duration_ms=250,
    )

    start = subtitle_animation_transform(_cue(), 1.0, animation)
    halfway = subtitle_animation_transform(_cue(), 1.2, animation)
    settled = subtitle_animation_transform(_cue(), 1.4, animation)

    assert start.vertical_offset == pytest.approx(80.0)
    assert halfway.vertical_offset == pytest.approx(40.0)
    assert settled.vertical_offset == pytest.approx(0.0)


def test_zero_animation_durations_show_full_opacity_immediately() -> None:
    animation = SubtitleAnimationSettings(
        preset="Fade",
        enter_duration_ms=0,
        exit_duration_ms=0,
    )

    transform = subtitle_animation_transform(_cue(), 1.0, animation)

    assert transform.opacity == pytest.approx(1.0)


def test_unknown_preset_falls_back_to_fade_without_extra_transform() -> None:
    animation = SubtitleAnimationSettings(
        preset="Unknown",
        enter_duration_ms=500,
        exit_duration_ms=500,
    )

    transform = subtitle_animation_transform(_cue(), 1.25, animation)

    assert transform.opacity == pytest.approx(0.5)
    assert transform.scale == pytest.approx(1.0)
    assert transform.vertical_offset == pytest.approx(0.0)


def test_transform_outside_cue_is_invisible() -> None:
    animation = SubtitleAnimationSettings()

    assert subtitle_animation_transform(_cue(), 0.5, animation).opacity == pytest.approx(0.0)
    assert subtitle_animation_transform(_cue(), 3.0, animation).opacity == pytest.approx(0.0)
