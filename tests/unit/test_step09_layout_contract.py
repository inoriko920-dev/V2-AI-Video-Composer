from aavc.presentation.layout_contract import ShellGeometry


def test_1920_shell_zones_do_not_overlap() -> None:
    g = ShellGeometry.calculate(1920, 1080)
    assert g.left.w == 300
    assert g.right.w == 360
    assert g.preview.w >= 640
    assert g.timeline.h >= 180
    assert not g.left.intersects(g.preview)
    assert not g.preview.intersects(g.right)
    assert not g.timeline.intersects(g.left)


def test_compact_editor_preserves_minimum_preview() -> None:
    g = ShellGeometry.calculate(1366, 768)
    assert g.preview.w >= 640
    assert g.timeline.h >= 180
