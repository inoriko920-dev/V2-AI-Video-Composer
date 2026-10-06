from aavc.presentation.timeline_zoom_scroll import (
    normalize_timeline_follow_playhead,
    timeline_should_follow_playhead,
)


def test_follow_playhead_defaults_on() -> None:
    assert normalize_timeline_follow_playhead(None) is True
    assert normalize_timeline_follow_playhead(object()) is True


def test_follow_playhead_normalizes_explicit_off_values() -> None:
    for value in (False, 0, 0.0, "0", "false", "OFF", " no "):
        assert normalize_timeline_follow_playhead(value) is False


def test_follow_playhead_normalizes_explicit_on_values() -> None:
    for value in (True, 1, 1.0, "1", "true", "ON", " yes "):
        assert normalize_timeline_follow_playhead(value) is True


def test_auto_follow_requires_request_and_enabled_setting() -> None:
    assert timeline_should_follow_playhead(True, True) is True
    assert timeline_should_follow_playhead(True, False) is False
    assert timeline_should_follow_playhead(False, True) is False
    assert timeline_should_follow_playhead(False, False) is False
