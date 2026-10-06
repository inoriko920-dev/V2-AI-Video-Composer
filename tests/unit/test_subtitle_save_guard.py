from __future__ import annotations

from typing import Any

from aavc.presentation.windows.subtitle_save_guard_window import (
    SubtitleSaveGuardMainWindow,
    subtitle_project_save_requires_working_copy_guard,
)


def _controller(
    *,
    editor_active: bool,
    working_copy_dirty: bool,
) -> tuple[Any, list[tuple[str, ...]]]:
    target: Any = SubtitleSaveGuardMainWindow.__new__(SubtitleSaveGuardMainWindow)
    target._subtitle_working_copy_dirty = working_copy_dirty
    calls: list[tuple[str, ...]] = []
    target._subtitle_editor_is_active = lambda: editor_active
    target._show_project_notice = lambda title, message: calls.append(
        ("notice", title, message)
    )
    return target, calls


def test_project_save_guard_is_required_only_for_dirty_active_subtitle_editor() -> None:
    assert subtitle_project_save_requires_working_copy_guard(
        editor_active=True,
        working_copy_dirty=True,
    )
    assert not subtitle_project_save_requires_working_copy_guard(
        editor_active=True,
        working_copy_dirty=False,
    )
    assert not subtitle_project_save_requires_working_copy_guard(
        editor_active=False,
        working_copy_dirty=True,
    )


def test_dirty_subtitle_working_copy_blocks_project_save(monkeypatch: Any) -> None:
    target, calls = _controller(editor_active=True, working_copy_dirty=True)
    monkeypatch.setattr(
        "aavc.presentation.windows.subtitle_export_guard_window.SubtitleExportGuardMainWindow.save_project",
        lambda _self: calls.append(("save",)),
    )

    SubtitleSaveGuardMainWindow.save_project(target)

    assert len(calls) == 1
    assert calls[0][0] == "notice"
    assert calls[0][1] == "Subtitle belum disimpan"
    assert "Simpan Salinan" in calls[0][2]


def test_dirty_subtitle_working_copy_blocks_project_save_as(monkeypatch: Any) -> None:
    target, calls = _controller(editor_active=True, working_copy_dirty=True)
    monkeypatch.setattr(
        "aavc.presentation.windows.guarded_main_window.GuardedMainWindow.save_project_as",
        lambda _self: calls.append(("save-as",)),
    )

    SubtitleSaveGuardMainWindow.save_project_as(target)

    assert len(calls) == 1
    assert calls[0][0] == "notice"
    assert "Simpan Salinan" in calls[0][2]


def test_clean_or_non_subtitle_project_persistence_passes_through(
    monkeypatch: Any,
) -> None:
    for editor_active, working_copy_dirty in ((True, False), (False, True)):
        target, calls = _controller(
            editor_active=editor_active,
            working_copy_dirty=working_copy_dirty,
        )
        monkeypatch.setattr(
            "aavc.presentation.windows.subtitle_export_guard_window.SubtitleExportGuardMainWindow.save_project",
            lambda _self, calls=calls: calls.append(("save",)),
        )
        monkeypatch.setattr(
            "aavc.presentation.windows.guarded_main_window.GuardedMainWindow.save_project_as",
            lambda _self, calls=calls: calls.append(("save-as",)),
        )

        SubtitleSaveGuardMainWindow.save_project(target)
        SubtitleSaveGuardMainWindow.save_project_as(target)

        assert calls == [("save",), ("save-as",)]
