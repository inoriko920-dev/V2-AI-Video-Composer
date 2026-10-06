from __future__ import annotations

from dataclasses import dataclass

from aavc.application.commands.project_commands import ProjectCommand
from aavc.domain.project.models import ProjectState


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    description: str
    before: ProjectState
    after: ProjectState


class ProjectHistory:
    def __init__(self, initial: ProjectState) -> None:
        self._current = initial
        self._undo: list[HistoryEntry] = []
        self._redo: list[HistoryEntry] = []

    @property
    def current(self) -> ProjectState:
        return self._current

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def execute(self, command: ProjectCommand) -> ProjectState:
        before = self._current
        after = command.apply(before)
        self._undo.append(HistoryEntry(command.describe(), before, after))
        self._redo.clear()
        self._current = after
        return after

    def undo(self) -> ProjectState:
        if not self._undo:
            raise ValueError("Tidak ada aksi untuk di-undo")
        entry = self._undo.pop()
        self._redo.append(entry)
        self._current = entry.before
        return self._current

    def redo(self) -> ProjectState:
        if not self._redo:
            raise ValueError("Tidak ada aksi untuk di-redo")
        entry = self._redo.pop()
        self._undo.append(entry)
        self._current = entry.after
        return self._current
