from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from aavc.presentation.navigation import UiRoute
from aavc.presentation.windows.subtitle_edit_window import (
    SubtitleEditMainWindow,
    subtitle_editor_should_leave_for_missing_source,
)


class _StatusBar:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, message: str, _timeout: int) -> None:
        self.messages.append(message)


class _WindowShell:
    def __init__(self) -> None:
        self.bar = _StatusBar()

    def statusBar(self) -> _StatusBar:
        return self.bar


def _controller(
    *,
    editor_active: bool,
    subtitle_source: str | None,
) -> tuple[Any, list[object]]:
    target: Any = SubtitleEditMainWindow.__new__(SubtitleEditMainWindow)
    target.services = SimpleNamespace(
        project_session=SimpleNamespace(
            current=SimpleNamespace(subtitle_source=subtitle_source)
        )
    )
    target.window = _WindowShell()
    target._subtitle_working_copy_dirty = True
    calls: list[object] = []
    target._subtitle_editor_is_active = lambda: editor_active

    def set_dirty(value: bool) -> None:
        calls.append(("dirty", value))
        target._subtitle_working_copy_dirty = value

    target._set_subtitle_working_copy_dirty = set_dirty
    target.show_route = lambda route: calls.append(("route", route))
    return target, calls


def test_history_reconcile_decision_requires_active_editor_without_source() -> None:
    assert subtitle_editor_should_leave_for_missing_source(
        editor_active=True,
        subtitle_source=None,
    )
    assert subtitle_editor_should_leave_for_missing_source(
        editor_active=True,
        subtitle_source="",
    )
    assert not subtitle_editor_should_leave_for_missing_source(
        editor_active=False,
        subtitle_source=None,
    )
    assert not subtitle_editor_should_leave_for_missing_source(
        editor_active=True,
        subtitle_source="subtitle.srt",
    )


def test_reconcile_closes_stale_subtitle_editor_and_clears_local_dirty() -> None:
    target, calls = _controller(editor_active=True, subtitle_source=None)

    SubtitleEditMainWindow._reconcile_subtitle_editor_after_project_history(target)

    assert calls == [
        ("dirty", False),
        ("route", UiRoute.EDITOR),
    ]
    assert not target._subtitle_working_copy_dirty
    assert "tidak memiliki source subtitle" in target.window.bar.messages[-1]


def test_reconcile_keeps_active_editor_when_source_still_exists() -> None:
    target, calls = _controller(
        editor_active=True,
        subtitle_source="subtitle.srt",
    )

    SubtitleEditMainWindow._reconcile_subtitle_editor_after_project_history(target)

    assert calls == []
    assert target._subtitle_working_copy_dirty
    assert target.window.bar.messages == []


def test_reconcile_does_nothing_outside_subtitle_editor() -> None:
    target, calls = _controller(editor_active=False, subtitle_source=None)

    SubtitleEditMainWindow._reconcile_subtitle_editor_after_project_history(target)

    assert calls == []
    assert target._subtitle_working_copy_dirty
    assert target.window.bar.messages == []
