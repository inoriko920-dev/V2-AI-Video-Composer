from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from aavc.application.commands import SetNarrationAudio, SetSubtitleSource
from aavc.presentation.windows.subtitle_import_guard_window import (
    SubtitleImportGuardMainWindow,
    subtitle_import_requires_working_copy_guard,
)


class _Session:
    def __init__(self) -> None:
        self.commands: list[object] = []

    def execute(self, command: object) -> None:
        self.commands.append(command)


def _controller(
    *,
    editor_active: bool,
    working_copy_dirty: bool,
    confirm_discard: bool = True,
) -> tuple[Any, _Session, list[str]]:
    target: Any = SubtitleImportGuardMainWindow.__new__(SubtitleImportGuardMainWindow)
    session = _Session()
    calls: list[str] = []
    target.services = SimpleNamespace(project_session=session)
    target._subtitle_working_copy_dirty = working_copy_dirty
    target._subtitle_editor_is_active = lambda: editor_active

    def confirm(action: str) -> bool:
        calls.append(f"confirm:{action}")
        return confirm_discard

    def rebuild() -> None:
        calls.append("rebuild")
        target._subtitle_working_copy_dirty = False

    def set_dirty(value: bool) -> None:
        calls.append(f"dirty:{value}")
        target._subtitle_working_copy_dirty = value

    target._confirm_subtitle_working_copy_discard = confirm
    target._rebuild_subtitle_editor_after_discard_authorized = rebuild
    target._set_subtitle_working_copy_dirty = set_dirty
    target._refresh_window_title = lambda: calls.append("title")
    target.refresh_editor_overview = lambda: calls.append("overview")
    return target, session, calls


def test_guard_is_required_only_for_dirty_active_subtitle_import() -> None:
    assert subtitle_import_requires_working_copy_guard(
        "subtitle", editor_active=True, working_copy_dirty=True
    )
    assert not subtitle_import_requires_working_copy_guard(
        "subtitle", editor_active=True, working_copy_dirty=False
    )
    assert not subtitle_import_requires_working_copy_guard(
        "subtitle", editor_active=False, working_copy_dirty=True
    )
    assert not subtitle_import_requires_working_copy_guard(
        "narration", editor_active=True, working_copy_dirty=True
    )


def test_cancelled_srt_guard_does_not_mutate_project_or_working_copy() -> None:
    target, session, calls = _controller(
        editor_active=True,
        working_copy_dirty=True,
        confirm_discard=False,
    )

    result = SubtitleImportGuardMainWindow._apply_imported_media(
        target, "replacement.srt", "subtitle"
    )

    assert result is None
    assert session.commands == []
    assert target._subtitle_working_copy_dirty
    assert calls == ["confirm:mengimpor SRT baru"]


def test_confirmed_srt_reimport_rebuilds_editor_from_new_source() -> None:
    target, session, calls = _controller(
        editor_active=True,
        working_copy_dirty=True,
        confirm_discard=True,
    )

    result = SubtitleImportGuardMainWindow._apply_imported_media(
        target, "replacement.srt", "subtitle"
    )

    assert result == "Subtitle SRT"
    assert len(session.commands) == 1
    assert isinstance(session.commands[0], SetSubtitleSource)
    assert not target._subtitle_working_copy_dirty
    assert calls == [
        "confirm:mengimpor SRT baru",
        "rebuild",
        "title",
        "overview",
    ]


def test_clean_srt_reimport_skips_confirmation_but_rebuilds_editor() -> None:
    target, session, calls = _controller(
        editor_active=True,
        working_copy_dirty=False,
    )

    result = SubtitleImportGuardMainWindow._apply_imported_media(
        target, "replacement.srt", "subtitle"
    )

    assert result == "Subtitle SRT"
    assert len(session.commands) == 1
    assert isinstance(session.commands[0], SetSubtitleSource)
    assert calls == ["rebuild", "title", "overview"]


def test_audio_import_does_not_discard_dirty_subtitle_working_copy() -> None:
    target, session, calls = _controller(
        editor_active=True,
        working_copy_dirty=True,
    )

    result = SubtitleImportGuardMainWindow._apply_imported_media(
        target, "narration.wav", "narration"
    )

    assert result == "Narasi audio"
    assert len(session.commands) == 1
    assert isinstance(session.commands[0], SetNarrationAudio)
    assert target._subtitle_working_copy_dirty
    assert calls == ["title", "overview"]
