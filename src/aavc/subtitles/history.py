from __future__ import annotations

from dataclasses import dataclass, field

from .srt import SubtitleCue


@dataclass(frozen=True, slots=True)
class SubtitleWorkingCopySnapshot:
    cues: tuple[SubtitleCue, ...]
    selected_row: int


@dataclass(slots=True)
class SubtitleWorkingCopyHistory:
    """Local undo/redo history for an unsaved copied-SRT editing session."""

    _undo: list[SubtitleWorkingCopySnapshot] = field(default_factory=list)
    _redo: list[SubtitleWorkingCopySnapshot] = field(default_factory=list)

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def record(
        self,
        previous: SubtitleWorkingCopySnapshot,
        current: SubtitleWorkingCopySnapshot,
    ) -> None:
        """Record one user action when cue contents changed.

        Selection-only changes are intentionally not history entries. Recording a new
        edit after Undo clears the redo branch.
        """

        if previous.cues == current.cues:
            return
        self._undo.append(previous)
        self._redo.clear()

    def undo(
        self,
        current: SubtitleWorkingCopySnapshot,
    ) -> SubtitleWorkingCopySnapshot:
        if not self._undo:
            return current
        previous = self._undo.pop()
        self._redo.append(current)
        return previous

    def redo(
        self,
        current: SubtitleWorkingCopySnapshot,
    ) -> SubtitleWorkingCopySnapshot:
        if not self._redo:
            return current
        following = self._redo.pop()
        self._undo.append(current)
        return following
