from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

from .cancellation import CancellationRequested, CancellationToken
from .job import JobSnapshot, JobStatus


@dataclass(slots=True)
class _JobRecord:
    job_id: str
    name: str
    token: CancellationToken
    status: JobStatus = JobStatus.QUEUED
    error: str | None = None
    future: Future[None] | None = None


class JobManager:
    """Small cooperative background-job manager for UI-safe long-running work."""

    def __init__(self, max_workers: int = 2) -> None:
        if max_workers < 1:
            raise ValueError("max_workers harus >= 1")
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="aavc")
        self._lock = Lock()
        self._jobs: dict[str, _JobRecord] = {}

    def submit(self, name: str, work: Callable[[CancellationToken], None]) -> str:
        if not name.strip():
            raise ValueError("Nama job tidak boleh kosong")
        job_id = uuid4().hex
        record = _JobRecord(job_id=job_id, name=name, token=CancellationToken())
        with self._lock:
            self._jobs[job_id] = record

        def runner() -> None:
            self._set_status(job_id, JobStatus.RUNNING)
            try:
                record.token.raise_if_cancelled()
                work(record.token)
                if record.token.is_cancelled:
                    self._set_status(job_id, JobStatus.CANCELLED)
                else:
                    self._set_status(job_id, JobStatus.COMPLETED)
            except CancellationRequested:
                self._set_status(job_id, JobStatus.CANCELLED)
            except Exception as exc:  # boundary: convert worker failures into job state
                self._set_status(job_id, JobStatus.FAILED, str(exc))

        future = self._executor.submit(runner)
        with self._lock:
            record.future = future
        return job_id

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return False
            if record.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
                return False
            record.token.cancel()
            future = record.future
        if future is not None and future.cancel():
            self._set_status(job_id, JobStatus.CANCELLED)
        return True

    def snapshot(self, job_id: str) -> JobSnapshot:
        with self._lock:
            record = self._jobs[job_id]
            return JobSnapshot(record.job_id, record.name, record.status, record.error)

    def snapshots(self) -> tuple[JobSnapshot, ...]:
        with self._lock:
            return tuple(
                JobSnapshot(record.job_id, record.name, record.status, record.error)
                for record in self._jobs.values()
            )

    def shutdown(self, *, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def _set_status(self, job_id: str, status: JobStatus, error: str | None = None) -> None:
        with self._lock:
            record = self._jobs[job_id]
            record.status = status
            record.error = error
