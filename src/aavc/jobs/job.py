from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class JobSnapshot:
    job_id: str
    name: str
    status: JobStatus
    error: str | None = None
