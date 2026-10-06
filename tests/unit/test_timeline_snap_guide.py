from aavc.presentation.timeline_snap_guide import (
    timeline_snap_guide_label,
    timeline_snap_guide_label_left,
)


def test_timeline_snap_guide_label_maps_known_targets() -> None:
    assert timeline_snap_guide_label("marker") == "Marker"
    assert timeline_snap_guide_label("scene") == "Scene Edge"
    assert timeline_snap_guide_label("playhead") == "Playhead"
    assert timeline_snap_guide_label("split") == "Split Target"
    assert timeline_snap_guide_label("unknown") == "Snap"


def test_timeline_snap_guide_label_left_centers_when_space_is_available() -> None:
    assert timeline_snap_guide_label_left(100, 300, 80) == 60


def test_timeline_snap_guide_label_left_clamps_near_track_start() -> None:
    assert timeline_snap_guide_label_left(2, 300, 80) == 4


def test_timeline_snap_guide_label_left_clamps_near_track_end() -> None:
    assert timeline_snap_guide_label_left(298, 300, 80) == 216


def test_timeline_snap_guide_label_left_handles_label_wider_than_track() -> None:
    assert timeline_snap_guide_label_left(30, 60, 120) == 0
