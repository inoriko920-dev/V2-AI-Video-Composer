from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

from aavc.jobs.cancellation import CancellationToken
from aavc.jobs.manager import JobManager


@dataclass(frozen=True, slots=True)
class BackgroundCallSnapshot[T]:
    done: bool
    result: T | None = None
    error: Exception | None = None


class BackgroundCall[T]:
    """Run one blocking callable through the canonical JobManager."""

    def __init__(
        self,
        jobs: JobManager,
        work: Callable[[], T],
        *,
        name: str = "background-work",
    ) -> None:
        self._jobs = jobs
        self._work = work
        self._name = name
        self._lock = Lock()
        self._started = False
        self._done = False
        self._result: T | None = None
        self._error: Exception | None = None
        self._job_id: str | None = None

    @property
    def started(self) -> bool:
        with self._lock:
            return self._started

    @property
    def job_id(self) -> str | None:
        with self._lock:
            return self._job_id

    def start(self) -> None:
        with self._lock:
            if self._started:
                raise RuntimeError("BackgroundCall hanya boleh dimulai sekali")
            self._started = True

        def runner(token: CancellationToken) -> None:
            try:
                token.raise_if_cancelled()
                result = self._work()
            except Exception as error:  # worker boundary: surface failure to GUI poller
                with self._lock:
                    self._error = error
                    self._done = True
                raise
            else:
                with self._lock:
                    self._result = result
                    self._done = True

        job_id = self._jobs.submit(self._name, runner)
        with self._lock:
            self._job_id = job_id

    def snapshot(self) -> BackgroundCallSnapshot[T]:
        with self._lock:
            return BackgroundCallSnapshot(
                done=self._done,
                result=self._result,
                error=self._error,
            )
