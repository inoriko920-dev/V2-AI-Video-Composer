from aavc.presentation.windows.guarded_main_window import (
    background_work_blocks_close,
    resolve_unsaved_choice,
)
from aavc.presentation.windows.subtitle_edit_window import (
    resolve_subtitle_working_copy_leave,
)


def test_clean_project_never_blocks_destructive_action() -> None:
    assert resolve_unsaved_choice(False, "cancel")
    assert resolve_unsaved_choice(False, "save", save_succeeded=False)


def test_dirty_project_allows_discard_and_blocks_cancel() -> None:
    assert resolve_unsaved_choice(True, "discard")
    assert not resolve_unsaved_choice(True, "cancel")


def test_dirty_project_only_allows_save_when_persistence_succeeds() -> None:
    assert resolve_unsaved_choice(True, "save", save_succeeded=True)
    assert not resolve_unsaved_choice(True, "save", save_succeeded=False)


def test_clean_subtitle_working_copy_never_blocks_leave() -> None:
    assert resolve_subtitle_working_copy_leave(False, discard_confirmed=False)
    assert resolve_subtitle_working_copy_leave(False, discard_confirmed=True)


def test_dirty_subtitle_working_copy_requires_explicit_discard() -> None:
    assert not resolve_subtitle_working_copy_leave(True, discard_confirmed=False)
    assert resolve_subtitle_working_copy_leave(True, discard_confirmed=True)



def test_background_work_blocks_application_close_until_consumed() -> None:
    assert background_work_blocks_close(background_busy=True)
    assert not background_work_blocks_close(background_busy=False)
