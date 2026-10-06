from __future__ import annotations

from pathlib import Path

from aavc.domain.project.models import ProjectState
from aavc.persistence.serializer import load_project, save_project


class ProjectRepository:
    def save(self, project: ProjectState, path: str | Path) -> Path:
        return save_project(project, path)

    def load(self, path: str | Path) -> ProjectState:
        return load_project(path)
