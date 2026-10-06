from __future__ import annotations

from aavc.presentation.timeline_follow_override import (
    normalize_timeline_follow_manual_override,
    timeline_follow_button_text,
    timeline_follow_may_scroll,
)


def test_manual_follow_override_defaults_off_and_normalizes_values() -> None:
    assert normalize_timeline_follow_manual_override(None) is False
    assert normalize_timeline_follow_manual_override(False) is False
    assert normalize_timeline_follow_manual_override("off") is False
    assert normalize_timeline_follow_manual_override(True) is True
    assert normalize_timeline_follow_manual_override("on") is True


def test_manual_override_blocks_follow_without_disabling_master_setting() -> None:
    assert timeline_follow_may_scroll(
        requested_follow=True,
        follow_enabled=True,
        manual_override=False,
    )
    assert not timeline_follow_may_scroll(
        requested_follow=True,
        follow_enabled=True,
        manual_override=True,
    )
    assert not timeline_follow_may_scroll(
        requested_follow=False,
        follow_enabled=True,
        manual_override=False,
    )
    assert not timeline_follow_may_scroll(
        requested_follow=True,
        follow_enabled=False,
        manual_override=False,
    )


def test_follow_button_text_distinguishes_pause_from_master_off() -> None:
    assert timeline_follow_button_text(
        follow_enabled=True,
        manual_override=False,
    ) == "Follow ON"
    assert timeline_follow_button_text(
        follow_enabled=True,
        manual_override=True,
    ) == "Follow PAUSE"
    assert timeline_follow_button_text(
        follow_enabled=False,
        manual_override=True,
    ) == "Follow OFF"
