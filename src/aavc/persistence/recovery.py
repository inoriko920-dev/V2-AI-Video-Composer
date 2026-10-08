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


def _preserve_pre_recovery_project(project: Path) -> Path:
    """Save the previous disk state without ever replacing an older backup.

    Exclusive creation also protects against concurrent restore attempts choosing
    the same numbered backup filename.
    """
    index = 0
    while True:
        suffix = ".pre-recovery.bak" if index == 0 else f".pre-recovery.{index}.bak"
        backup = project.with_suffix(project.suffix + suffix)
        try:
            output = backup.open("xb")
        except FileExistsError:
            index += 1
            continue

        try:
            with output:
                with project.open("rb") as source:
                    shutil.copyfileobj(source, output)
            shutil.copystat(project, backup)
            return backup
        except Exception:
            # Failed copies must not reserve a partially written backup slot.
            backup.unlink(missing_ok=True)
            raise


class RecoveryManager:
    def recovery_path_for(self, project_path: str | Path) -> Path:
        path = Path(project_path)
        return path.with_suffix(path.suffix + ".autosave")

    def write_snapshot(self, project: ProjectState, project_path: str | Path) -> RecoverySnapshot:
        target = self.recovery_path_for(project_path)
        save_project(
            project,
            target,
            create_schema_backup=False,
            allow_schema_downgrade=True,
        )
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

        if project.exists():
            _preserve_pre_recovery_project(project)
        temp = temporary_sibling_path(project, label="restore")
        try:
            shutil.copy2(recovery, temp)
            temp.replace(project)
            return project
        finally:
            temp.unlink(missing_ok=True)

    def clear_snapshot(self, project_path: str | Path) -> None:
        self.recovery_path_for(project_path).unlink(missing_ok=True)
