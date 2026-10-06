from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from aavc.application.commands import SetSubtitleAnimation, SetSubtitleStyle
from aavc.domain.project.models import SubtitleAnimationSettings, SubtitleStyle
from aavc.presentation.windows.subtitle_edit_window import SubtitleEditMainWindow


class _Session:
    def __init__(self) -> None:
        self.commands: list[object] = []

    def execute(self, command: object) -> None:
        self.commands.append(command)


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


def _controller() -> tuple[Any, _Session, list[str]]:
    target: Any = SubtitleEditMainWindow.__new__(SubtitleEditMainWindow)
    session = _Session()
    calls: list[str] = []
    target.services = SimpleNamespace(project_session=session)
    target.window = _WindowShell()
    target._refresh_window_title = lambda: calls.append("title")
    target.refresh_editor_overview = lambda: calls.append("overview")
    target.open_subtitle_editor = lambda: calls.append("subtitle-rebuild")
    target._show_project_error = lambda *_args: calls.append("error")
    return target, session, calls


def test_apply_subtitle_style_keeps_current_subtitle_screen_alive() -> None:
    target, session, calls = _controller()
    style = SubtitleStyle(preset_name="Dokumenter")

    SubtitleEditMainWindow.set_subtitle_style(target, style)

    assert len(session.commands) == 1
    assert isinstance(session.commands[0], SetSubtitleStyle)
    assert calls == ["title", "overview"]
    assert "Working copy Edit Cue tetap dipertahankan" in target.window.bar.messages[-1]


def test_apply_subtitle_animation_keeps_current_subtitle_screen_alive() -> None:
    target, session, calls = _controller()
    animation = SubtitleAnimationSettings(preset="Pop")

    SubtitleEditMainWindow.set_subtitle_animation(target, animation)

    assert len(session.commands) == 1
    assert isinstance(session.commands[0], SetSubtitleAnimation)
    assert calls == ["title", "overview"]
    assert "Working copy Edit Cue tetap dipertahankan" in target.window.bar.messages[-1]
