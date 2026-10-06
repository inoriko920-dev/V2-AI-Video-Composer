from __future__ import annotations

from dataclasses import dataclass, field

from aavc.application.services.project_session import ProjectSession
from aavc.jobs import JobManager
from aavc.platform.paths import PathService


@dataclass(frozen=True, slots=True)
class FoundationServices:
    app_name: str
    paths: PathService
    project_session: ProjectSession
    jobs: JobManager = field(default_factory=JobManager)


def build_foundation_services() -> FoundationServices:
    return FoundationServices(
        app_name="AI Automatic Video Composer",
        paths=PathService.discover(),
        project_session=ProjectSession(),
        jobs=JobManager(),
    )
