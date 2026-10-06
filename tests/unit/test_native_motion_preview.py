import pytest

from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.motion_preview import (
    native_motion_preview_offset,
    native_visual_preview_opacity,
    native_visual_preview_scale,
    preview_continuation_scene_index,
    preview_narration_seconds,
    preview_neighbor_scene_index,
    preview_scrub_seconds,
    preview_timecode,
)


def _assignment(
    enter: str = "Rise",
    exit_effect: str = "Drift",
    *,
    intensity: float = 1.0,
) -> AnimationAssignment:
    return AnimationAssignment(
        scene_number=1,
        asset_id="A001",
        enter_effect=enter,
        exit_effect=exit_effect,
        intensity=intensity,
    )


def test_preview_neighbor_scene_index_respects_boundaries() -> None:
    assert preview_neighbor_scene_index(0, 3, -1) is None
    assert preview_neighbor_scene_index(0, 3, 1) == 1
    assert preview_neighbor_scene_index(1, 3, -1) == 0
    assert preview_neighbor_scene_index(1, 3, 1) == 2
    assert preview_neighbor_scene_index(2, 3, 1) is None
    assert preview_neighbor_scene_index(-1, 3, 1) is None
    assert preview_neighbor_scene_index(3, 3, -1) is None
    assert preview_neighbor_scene_index(0, 0, 1) is None
    assert preview_neighbor_scene_index(1, 3, 0) is None


def test_preview_continuation_scene_index_advances_until_project_end() -> None:
    assert preview_continuation_scene_index(0, 3) == 1
    assert preview_continuation_scene_index(1, 3) == 2
    assert preview_continuation_scene_index(2, 3) is None
    assert preview_continuation_scene_index(-1, 3) is None
    assert preview_continuation_scene_index(0, 0) is None


def test_preview_scrub_seconds_maps_and_clamps_scene_time() -> None:
    assert preview_scrub_seconds(-10, 1000, 8.0) == pytest.approx(0.0)
    assert preview_scrub_seconds(500, 1000, 8.0) == pytest.approx(4.0)
    assert preview_scrub_seconds(1200, 1000, 8.0) == pytest.approx(8.0)
    assert preview_scrub_seconds(0, 0, 8.0) == pytest.approx(0.0)
    assert preview_scrub_seconds(500, 1000, -2.0) == pytest.approx(0.0)


def test_preview_narration_seconds_maps_scene_local_time_to_global_timeline() -> None:
    durations = (2.0, 3.5, 1.0)

    assert preview_narration_seconds(durations, 0, 1.25) == pytest.approx(1.25)
    assert preview_narration_seconds(durations, 1, 0.0) == pytest.approx(2.0)
    assert preview_narration_seconds(durations, 1, 1.5) == pytest.approx(3.5)
    assert preview_narration_seconds(durations, 1, 99.0) == pytest.approx(5.5)
    assert preview_narration_seconds(durations, 2, -5.0) == pytest.approx(5.5)
    assert preview_narration_seconds(durations, -1, 1.0) == pytest.approx(0.0)
    assert preview_narration_seconds(durations, 3, 1.0) == pytest.approx(0.0)


def test_preview_narration_seconds_normalizes_negative_scene_durations() -> None:
    assert preview_narration_seconds((2.0, -4.0, 3.0), 2, 1.0) == pytest.approx(3.0)


def test_preview_timecode_formats_project_position_at_project_fps() -> None:
    assert preview_timecode(0.0, 30) == "00:00:00:00"
    assert preview_timecode(61.5, 30) == "00:01:01:15"
    assert preview_timecode(1.5, 60) == "00:00:01:30"
    assert preview_timecode(3661.0, 30) == "01:01:01:00"


def test_preview_timecode_clamps_negative_time_and_invalid_fps() -> None:
    assert preview_timecode(-4.0, 30) == "00:00:00:00"
    assert preview_timecode(1.0, 0) == "00:00:01:00"


def test_native_fade_enter_preview_opacity_matches_render_window() -> None:
    assignment = _assignment("Fade", "Drift")

    assert native_visual_preview_opacity(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(0.0)
    assert native_visual_preview_opacity(
        assignment,
        time_seconds=0.125,
        duration_seconds=2.0,
    ) == pytest.approx(0.5)
    assert native_visual_preview_opacity(
        assignment,
        time_seconds=0.25,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)


def test_native_fade_exit_preview_opacity_matches_render_window() -> None:
    assignment = _assignment("Rise", "Fade")

    assert native_visual_preview_opacity(
        assignment,
        time_seconds=1.75,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)
    assert native_visual_preview_opacity(
        assignment,
        time_seconds=1.875,
        duration_seconds=2.0,
    ) == pytest.approx(0.5)
    assert native_visual_preview_opacity(
        assignment,
        time_seconds=2.0,
        duration_seconds=2.0,
    ) == pytest.approx(0.0)


def test_native_pop_preview_matches_scale_and_alpha_window() -> None:
    assignment = _assignment("Pop", "Pop")

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
    assert native_visual_preview_scale(
        assignment,
        time_seconds=1.875,
        duration_seconds=2.0,
    ) == pytest.approx(0.925)
    assert native_visual_preview_scale(
        assignment,
        time_seconds=2.0,
        duration_seconds=2.0,
    ) == pytest.approx(0.85)
    assert native_visual_preview_opacity(
        assignment,
        time_seconds=0.125,
        duration_seconds=2.0,
    ) == pytest.approx(0.5)


def test_preview_scale_is_identity_without_active_native_pop() -> None:
    assert native_visual_preview_scale(
        None,
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)
    assert native_visual_preview_scale(
        _assignment("Rise", "Drift"),
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)
    assert native_visual_preview_scale(
        _assignment("Pop", "Pop", intensity=0.0),
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)


def test_preview_opacity_is_opaque_without_active_native_alpha() -> None:
    assert native_visual_preview_opacity(
        None,
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)
    assert native_visual_preview_opacity(
        _assignment("Rise", "Drift"),
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)
    assert native_visual_preview_opacity(
        _assignment("Fade", "Fade", intensity=0.0),
        time_seconds=0.0,
        duration_seconds=2.0,
    ) == pytest.approx(1.0)


def test_preview_offset_is_zero_without_assignment() -> None:
    assert native_motion_preview_offset(
        None,
        time_seconds=0.0,
        duration_seconds=2.0,
    ).x == 0.0
    assert native_motion_preview_offset(
        None,
        time_seconds=0.0,
        duration_seconds=2.0,
    ).y == 0.0


def test_rise_enter_matches_phase_one_window() -> None:
    assignment = _assignment("Rise", "Fade")

    start = native_motion_preview_offset(
        assignment,
        time_seconds=0.0,
        duration_seconds=2.0,
    )
    halfway = native_motion_preview_offset(
        assignment,
        time_seconds=0.125,
        duration_seconds=2.0,
    )
    settled = native_motion_preview_offset(
        assignment,
        time_seconds=0.25,
        duration_seconds=2.0,
    )

    assert start.y == pytest.approx(0.08)
    assert halfway.y == pytest.approx(0.04)
    assert settled.y == pytest.approx(0.0)
    assert start.x == pytest.approx(0.0)


def test_drift_exit_matches_phase_one_window() -> None:
    assignment = _assignment("Fade", "Drift")

    before_exit = native_motion_preview_offset(
        assignment,
        time_seconds=1.75,
        duration_seconds=2.0,
    )
    halfway = native_motion_preview_offset(
        assignment,
        time_seconds=1.875,
        duration_seconds=2.0,
    )
    end = native_motion_preview_offset(
        assignment,
        time_seconds=2.0,
        duration_seconds=2.0,
    )

    assert before_exit.x == pytest.approx(0.0)
    assert halfway.x == pytest.approx(0.03)
    assert end.x == pytest.approx(0.06)
    assert end.y == pytest.approx(0.0)


def test_preview_offset_respects_intensity_and_ignores_non_native_effects() -> None:
    doubled = native_motion_preview_offset(
        _assignment("Rise", "Blur", intensity=2.0),
        time_seconds=0.0,
        duration_seconds=2.0,
    )
    non_native = native_motion_preview_offset(
        _assignment("Fade", "Blur"),
        time_seconds=0.0,
        duration_seconds=2.0,
    )

    assert doubled.y == pytest.approx(0.16)
    assert non_native.x == pytest.approx(0.0)
    assert non_native.y == pytest.approx(0.0)


def test_short_scene_uses_half_duration_window() -> None:
    assignment = _assignment("Pan", "Drift")

    midpoint = native_motion_preview_offset(
        assignment,
        time_seconds=0.05,
        duration_seconds=0.1,
    )

    assert midpoint.x == pytest.approx(0.0)
    assert midpoint.y == pytest.approx(0.0)
