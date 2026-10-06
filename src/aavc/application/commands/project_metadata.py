from __future__ import annotations

from dataclasses import dataclass, replace

from aavc.domain.project.models import ProjectState


@dataclass(frozen=True, slots=True)
class SetProjectTitle:
    """Rename the canonical project title without moving its project file."""

    title: str

    def apply(self, project: ProjectState) -> ProjectState:
        title = self.title.strip()
        if not title:
            raise ValueError("Nama proyek tidak boleh kosong")
        if len(title) > 200:
            raise ValueError("Nama proyek maksimal 200 karakter")
        return replace(project, title=title)

    def describe(self) -> str:
        return f"Ubah nama proyek menjadi {self.title.strip()}"
