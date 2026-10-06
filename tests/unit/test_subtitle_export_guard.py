from __future__ import annotations

from typing import Any

from aavc.presentation.windows.subtitle_export_guard_window import (
    SubtitleExportGuardMainWindow,
    subtitle_export_requires_working_copy_guard,
)


def _controller(
    *,
    editor_active: bool,
    working_copy_dirty: bool,
    confirm_discard: bool = True,
    rebuild_clears_dirty: bool = True,
) -> tuple[Any, list[str]]:
    target: Any = SubtitleExportGuardMainWindow.__new__(SubtitleExportGuardMainWindow)
    target._subtitle_working_copy_dirty = working_copy_dirty
    calls: list[str] = []
    target._subtitle_editor_is_active = lambda: editor_active

    def confirm(action: str) -> bool:
        calls.append(f"confirm:{action}")
        return confirm_discard

    def rebuild() -> None:
        calls.append("rebuild")
        if rebuild_clears_dirty:
            target._subtitle_working_copy_dirty = False

    target._confirm_subtitle_working_copy_discard = confirm
    target._rebuild_subtitle_editor_after_discard_authorized = rebuild
    return target, calls


def test_export_guard_is_required_only_for_dirty_active_subtitle_editor() -> None:
    assert subtitle_export_requires_working_copy_guard(
        editor_active=True,
        working_copy_dirty=True,
    )
    assert not subtitle_export_requires_working_copy_guard(
        editor_active=True,
        working_copy_dirty=False,
    )
    assert not subtitle_export_requires_working_copy_guard(
        editor_active=False,
        working_copy_dirty=True,
    )


def test_cancelled_export_guard_keeps_working_copy_and_does_not_open_export(
    monkeypatch: Any,
) -> None:
    target, calls = _controller(
        editor_active=True,
        working_copy_dirty=True,
        confirm_discard=False,
    )
    monkeypatch.setattr(
        "aavc.presentation.windows.subtitle_import_guard_window.SubtitleImportGuardMainWindow.open_export",
        lambda _self: calls.append("export"),
    )

    SubtitleExportGuardMainWindow.open_export(target)

    assert target._subtitle_working_copy_dirty
    assert calls == ["confirm:mengekspor video"]


def test_confirmed_export_rebuilds_working_copy_before_opening_dialog(
    monkeypatch: Any,
) -> None:
    target, calls = _controller(
        editor_active=True,
        working_copy_dirty=True,
        confirm_discard=True,
    )
    monkeypatch.setattr(
        "aavc.presentation.windows.subtitle_import_guard_window.SubtitleImportGuardMainWindow.open_export",
        lambda _self: calls.append("export"),
    )

    SubtitleExportGuardMainWindow.open_export(target)

    assert not target._subtitle_working_copy_dirty
    assert calls == [
        "confirm:mengekspor video",
        "rebuild",
        "export",
    ]


def test_failed_rebuild_keeps_export_closed(monkeypatch: Any) -> None:
    target, calls = _controller(
        editor_active=True,
        working_copy_dirty=True,
        confirm_discard=True,
        rebuild_clears_dirty=False,
    )
    monkeypatch.setattr(
        "aavc.presentation.windows.subtitle_import_guard_window.SubtitleImportGuardMainWindow.open_export",
        lambda _self: calls.append("export"),
    )

    SubtitleExportGuardMainWindow.open_export(target)

    assert target._subtitle_working_copy_dirty
    assert calls == ["confirm:mengekspor video", "rebuild"]


def test_clean_or_non_subtitle_export_passes_through_without_prompt(
    monkeypatch: Any,
) -> None:
    for editor_active, working_copy_dirty in ((True, False), (False, True)):
        target, calls = _controller(
            editor_active=editor_active,
            working_copy_dirty=working_copy_dirty,
        )
        monkeypatch.setattr(
            "aavc.presentation.windows.subtitle_import_guard_window.SubtitleImportGuardMainWindow.open_export",
            lambda _self, calls=calls: calls.append("export"),
        )

        SubtitleExportGuardMainWindow.open_export(target)

        assert calls == ["export"]
