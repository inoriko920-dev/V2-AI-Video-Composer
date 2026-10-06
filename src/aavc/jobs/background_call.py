from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

from aavc.jobs.cancellation import CancellationRequested, CancellationToken
from aavc.jobs.job import JobStatus
from aavc.jobs.manager import JobManager


@dataclass(frozen=True, slots=True)
class BackgroundCallSnapshot[T]:
    done: bool
    result: T | None = None
    error: Exception | None = None
    progress: float | None = None
    cancelled: bool = False


class BackgroundCall[T]:
    """Run one blocking callable through the canonical JobManager."""

    def __init__(
        self,
        jobs: JobManager,
        work: Callable[[], T] | None = None,
        *,
        cancellable_work: Callable[[CancellationToken, Callable[[float], None]], T] | None = None,
        name: str = "background-work",
    ) -> None:
        if (work is None) == (cancellable_work is None):
            raise ValueError("Berikan tepat satu work atau cancellable_work")
        self._jobs = jobs
        self._work = work
        self._cancellable_work = cancellable_work
        self._name = name
        self._lock = Lock()
        self._started = False
        self._done = False
        self._result: T | None = None
        self._error: Exception | None = None
        self._progress: float | None = None
        self._cancelled = False
        self._job_id: str | None = None

    @property
    def started(self) -> bool:
        with self._lock:
            return self._started

    @property
    def job_id(self) -> str | None:
        with self._lock:
            return self._job_id

    def _report_progress(self, value: float) -> None:
        normalized = max(0.0, min(1.0, float(value)))
        with self._lock:
            self._progress = normalized

    def start(self) -> None:
        with self._lock:
            if self._started:
                raise RuntimeError("BackgroundCall hanya boleh dimulai sekali")
            self._started = True

        def runner(token: CancellationToken) -> None:
            try:
                token.raise_if_cancelled()
                if self._cancellable_work is not None:
                    result = self._cancellable_work(token, self._report_progress)
                else:
                    assert self._work is not None
                    result = self._work()
                token.raise_if_cancelled()
            except CancellationRequested:
                with self._lock:
                    self._cancelled = True
                    self._done = True
                raise
            except Exception as error:
                if token.is_cancelled:
                    with self._lock:
                        self._cancelled = True
                        self._done = True
                    raise CancellationRequested("Pekerjaan dibatalkan") from error
                with self._lock:
                    self._error = error
                    self._done = True
                raise
            else:
                with self._lock:
                    self._result = result
                    self._progress = 1.0 if self._progress is not None else None
                    self._done = True

        job_id = self._jobs.submit(self._name, runner)
        with self._lock:
            self._job_id = job_id

    def cancel(self) -> bool:
        with self._lock:
            job_id = self._job_id
        if job_id is None:
            return False
        return self._jobs.cancel(job_id)

    def snapshot(self) -> BackgroundCallSnapshot[T]:
        with self._lock:
            done = self._done
            result = self._result
            error = self._error
            progress = self._progress
            cancelled = self._cancelled
            job_id = self._job_id

        if not done and job_id is not None:
            job_snapshot = self._jobs.snapshot(job_id)
            if job_snapshot.status == JobStatus.CANCELLED:
                done = True
                cancelled = True

        return BackgroundCallSnapshot(
            done=done,
            result=result,
            error=error,
            progress=progress,
            cancelled=cancelled,
        )
