from __future__ import annotations

from pathlib import Path

from aavc.application.commands.project_commands import ProjectCommand
from aavc.application.commands.transaction import ProjectTransaction
from aavc.application.services.history import ProjectHistory
from aavc.domain.project.models import ProjectState
from aavc.persistence.project_repository import ProjectRepository


class ProjectSession:
    """Own the active project, its file path, persistence baseline, and edit history."""

    def __init__(self, repository: ProjectRepository | None = None) -> None:
        self._repository = repository or ProjectRepository()
        self._history: ProjectHistory | None = None
        self._path: Path | None = None
        self._saved_state: ProjectState | None = None

    @property
    def current(self) -> ProjectState | None:
        return self._history.current if self._history is not None else None

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def has_project(self) -> bool:
        return self._history is not None

    @property
    def is_dirty(self) -> bool:
        current = self.current
        if current is None:
            return False
        if self._saved_state is None:
            return True
        return current != self._saved_state

    @property
    def can_undo(self) -> bool:
        return self._history.can_undo if self._history is not None else False

    @property
    def can_redo(self) -> bool:
        return self._history.can_redo if self._history is not None else False

    def start(self, project: ProjectState, path: str | Path | None = None) -> ProjectState:
        self._history = ProjectHistory(project)
        self._path = Path(path).resolve() if path is not None else None
        # ``start`` is primarily an in-memory/test entrypoint. With an explicit
        # path, callers are declaring the supplied state to be the persisted
        # baseline. Without a path there is no persisted baseline yet.
        self._saved_state = project if path is not None else None
        return project

    def create(self, project: ProjectState, path: str | Path) -> ProjectState:
        """Persist a new project first, then make it the active session."""

        destination = Path(path).resolve()
        saved = self._repository.save(project, destination)
        # Do not replace the active session until persistence succeeds.
        self._history = ProjectHistory(project)
        self._path = saved.resolve()
        self._saved_state = project
        return project

    def open(self, path: str | Path) -> ProjectState:
        source = Path(path).resolve()
        project = self._repository.load(source)
        # Mutate the live session only after load succeeds so a bad file cannot
        # destroy the previously active project.
        self._history = ProjectHistory(project)
        self._path = source
        self._saved_state = project
        return project

    def save(self, path: str | Path | None = None) -> Path:
        project = self._require_project()
        destination = Path(path).resolve() if path is not None else self._path
        if destination is None:
            raise ValueError("Lokasi proyek belum ditentukan")
        saved = self._repository.save(project, destination)
        self._path = saved.resolve()
        self._saved_state = project
        return self._path

    def execute(self, command: ProjectCommand) -> ProjectState:
        return self._require_history().execute(command)

    def execute_many(
        self,
        commands: tuple[ProjectCommand, ...],
        *,
        description: str = "Edit batch project",
    ) -> ProjectState:
        return self.execute(ProjectTransaction(commands, description))

    def undo(self) -> ProjectState:
        return self._require_history().undo()

    def redo(self) -> ProjectState:
        return self._require_history().redo()

    def _require_project(self) -> ProjectState:
        project = self.current
        if project is None:
            raise ValueError("Tidak ada proyek aktif")
        return project

    def _require_history(self) -> ProjectHistory:
        if self._history is None:
            raise ValueError("Tidak ada proyek aktif")
        return self._history
