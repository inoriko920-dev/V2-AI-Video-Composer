from aavc.presentation.timeline_zoom_actions import timeline_fit_zoom_percent


def test_fit_zoom_returns_largest_zoom_that_fits_viewport() -> None:
    assert timeline_fit_zoom_percent((10.0,), 600) == 125
    assert timeline_fit_zoom_percent((10.0,), 480) == 100


def test_fit_zoom_can_expand_to_maximum_when_track_is_short() -> None:
    assert timeline_fit_zoom_percent((1.0,), 500) == 400


def test_fit_zoom_falls_back_to_minimum_when_visual_min_width_cannot_fit() -> None:
    # Two very short scenes are each clamped to 56 px plus the 3 px scene gap.
    assert timeline_fit_zoom_percent((0.1, 0.1), 100) == 50


def test_fit_zoom_empty_timeline_returns_standard_zoom() -> None:
    assert timeline_fit_zoom_percent((), 800) == 100
