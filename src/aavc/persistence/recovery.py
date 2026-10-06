from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from aavc.domain.project.models import ProjectState
from aavc.persistence.serializer import load_project, save_project, temporary_sibling_path


@dataclass(frozen=True, slots=True)
class RecoverySnapshot:
    project_path: Path
    recovery_path: Path


class RecoveryManager:
    def recovery_path_for(self, project_path: str | Path) -> Path:
        path = Path(project_path)
        return path.with_suffix(path.suffix + ".autosave")

    def write_snapshot(self, project: ProjectState, project_path: str | Path) -> RecoverySnapshot:
        target = self.recovery_path_for(project_path)
        save_project(project, target)
        return RecoverySnapshot(Path(project_path), target)

    def has_snapshot(self, project_path: str | Path) -> bool:
        return self.recovery_path_for(project_path).is_file()

    def load_snapshot(self, project_path: str | Path) -> ProjectState:
        target = self.recovery_path_for(project_path)
        if not target.is_file():
            raise FileNotFoundError(target)
        return load_project(target)

    def restore_snapshot(self, project_path: str | Path) -> Path:
        project = Path(project_path)
        recovery = self.recovery_path_for(project)
        if not recovery.is_file():
            raise FileNotFoundError(recovery)

        # Validate the snapshot before touching the current project or backup.
        # A truncated/corrupt/future-schema autosave must fail closed.
        load_project(recovery)

        backup = project.with_suffix(project.suffix + ".pre-recovery.bak")
        if project.exists():
            shutil.copy2(project, backup)
        temp = temporary_sibling_path(project, label="restore")
        try:
            shutil.copy2(recovery, temp)
            temp.replace(project)
            return project
        finally:
            temp.unlink(missing_ok=True)

    def clear_snapshot(self, project_path: str | Path) -> None:
        self.recovery_path_for(project_path).unlink(missing_ok=True)
