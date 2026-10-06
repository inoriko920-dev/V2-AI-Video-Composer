from __future__ import annotations

from inspect import getsource

from aavc.presentation.dialogs.export_settings import create_export_dialog
from aavc.presentation.screens.home import create_home_screen
from aavc.presentation.screens.new_project import create_new_project_screen
from aavc.presentation.widgets.editor_shell import remove_tabs_by_label
from aavc.presentation.widgets.live_subtitle import create_live_subtitle_inspector


class _FakeWidget:
    def __init__(self) -> None:
        self.detached = False
        self.deleted = False

    def setParent(self, _parent: object | None) -> None:
        self.detached = True

    def deleteLater(self) -> None:
        self.deleted = True


class _FakeTabs:
    def __init__(self, labels: list[str]) -> None:
        self.labels = labels
        self.widgets = [_FakeWidget() for _ in labels]

    def count(self) -> int:
        return len(self.labels)

    def tabText(self, index: int) -> str:
        return self.labels[index]

    def widget(self, index: int) -> _FakeWidget:
        return self.widgets[index]

    def removeTab(self, index: int) -> None:
        self.labels.pop(index)
        self.widgets.pop(index)


def test_live_tab_cleanup_removes_reference_only_tabs() -> None:
    tabs = _FakeTabs(["Layout", "Animasi", "AI Agent"])

    removed = remove_tabs_by_label(tabs, {"Animasi", "AI Agent"})

    assert removed == ("Animasi", "AI Agent")
    assert tabs.labels == ["Layout"]


def test_export_dialog_does_not_advertise_unsupported_controls() -> None:
    source = getsource(create_export_dialog)

    assert "Gunakan akselerasi GPU jika tersedia" not in source
    assert "Pengaturan Lanjutan" not in source


def test_home_does_not_present_fake_recent_projects() -> None:
    source = getsource(create_home_screen)

    assert "Liburan ke Bromo" not in source
    assert "Konten Promosi Produk" not in source
    assert "Lihat Semua" not in source


def test_new_project_does_not_present_inactive_navigation_controls() -> None:
    source = getsource(create_new_project_screen)

    assert "Proyek Saya" not in source
    assert "Pengaturan" not in source
    assert 'QPushButton("Kembali")' not in source


def test_read_only_subtitle_tab_does_not_show_fake_edit_actions() -> None:
    source = getsource(create_live_subtitle_inspector)

    assert 'QPushButton("＋ Tambah Cue")' not in source
    assert 'QPushButton("Pisah Cue")' not in source
    assert 'QPushButton("Gabung")' not in source
