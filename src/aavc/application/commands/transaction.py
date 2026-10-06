from __future__ import annotations

from dataclasses import dataclass

from aavc.application.commands.project_commands import ProjectCommand
from aavc.domain.project.models import ProjectState


@dataclass(frozen=True, slots=True)
class ProjectTransaction:
    """Apply multiple immutable commands as one undo/redo history entry."""

    commands: tuple[ProjectCommand, ...]
    description: str = "Edit batch project"

    def __post_init__(self) -> None:
        if not self.commands:
            raise ValueError("Transaksi project tidak boleh kosong")
        if not self.description.strip():
            raise ValueError("Deskripsi transaksi project tidak boleh kosong")

    def apply(self, project: ProjectState) -> ProjectState:
        candidate = project
        for command in self.commands:
            candidate = command.apply(candidate)
        return candidate

    def describe(self) -> str:
        return self.description
