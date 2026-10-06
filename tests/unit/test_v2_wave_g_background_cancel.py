from __future__ import annotations

from aavc.presentation.windows.background_work_window import BackgroundWorkMainWindow


def test_background_runtime_exposes_cancel_entrypoint_for_ai_and_render() -> None:
    assert callable(BackgroundWorkMainWindow.cancel_background_work)
    assert callable(BackgroundWorkMainWindow._cancel_background_from_menu)
