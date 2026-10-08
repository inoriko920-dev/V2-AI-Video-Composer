"""Pure, deterministic autosave eligibility coordinator (W06-A).

This module **does not write or restore files**, create Qt timers, or replace
ProjectSession. The future W06-B/W06-C adapter owns snapshot persistence,
provenance, save fences and on-disk crash consistency. A caller must explicitly
pass the current session to `tick()` after committed project changes; W06-D
will bind it to the existing GUI lifecycle.

One dispatched request owns the single global writer slot until completion.
An epoch change fences late callback *state updates*. It cannot undo an already
running filesystem write: physical IO ordering is a later mandatory gate.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Callable

from aavc.application.services.project_session import ProjectSession
from aavc.domain.project.models import ProjectState

_DEBOUNCE_SECONDS = 20.0
_MAX_ELIGIBILITY_SECONDS = 120.0
_POLL_SECONDS = 60.0
_RETRY_SECONDS = (30.0, 120.0, 300.0)


@dataclass(frozen=True, slots=True)
class SnapshotRequest:
    """Detached state capture and ownership token for a future serial writer.

    `project_state` is deep-copied before dispatch, so subsequent live-session
    metadata mutations do not change the captured state. It is not a persisted
    snapshot and must not be treated as one until W06-B validates/writes it.
    """

    epoch: int
    revision: int
    path: Path
    project_state: ProjectState
    first_dirty_at: float


class RecoveryCoordinator:
    """Manage monotonic deadlines and exactly one in-flight snapshot request.

    `tick(session)` is pure with respect to disk and ProjectSession. Each
    accepted result must be reported via `complete(request, success=...)`.
    No clock sleeps, background threads, filesystem writes or Qt imports.
    """

    def __init__(self, *, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._last_now: float | None = None
        self._owner: ProjectSession | None = None
        self._path: Path | None = None
        self._observed: ProjectState | None = None
        self._epoch = 0
        self._revision = 0
        self._dirty_since: float | None = None
        self._last_edit_at: float | None = None
        self._next_poll_at: float | None = None
        self._last_success_revision: int | None = None
        self._next_retry_at: float | None = None
        self._failure_count = 0
        self._inflight: SnapshotRequest | None = None
        self._paused = False
        self._closed = False
        self._was_eligible = False

    def _now(self) -> float:
        now = float(self._clock())
        if self._last_now is not None and now < self._last_now:
            raise ValueError("monotonic clock went backwards")
        self._last_now = now
        return now

    @property
    def epoch(self) -> int:
        return self._epoch

    @property
    def revision(self) -> int:
        return self._revision

    @property
    def inflight(self) -> SnapshotRequest | None:
        return self._inflight

    @property
    def last_success_revision(self) -> int | None:
        return self._last_success_revision

    @property
    def next_retry_at(self) -> float | None:
        return self._next_retry_at

    @property
    def next_poll_at(self) -> float | None:
        return self._next_poll_at

    @property
    def next_due_at(self) -> float | None:
        if (
            self._closed
            or self._paused
            or not self._was_eligible
            or self._dirty_since is None
            or self._last_edit_at is None
            or self._inflight is not None
            or self._revision == self._last_success_revision
        ):
            return None
        due = min(
            self._last_edit_at + _DEBOUNCE_SECONDS,
            self._dirty_since + _MAX_ELIGIBILITY_SECONDS,
        )
        return max(due, self._next_retry_at) if self._next_retry_at is not None else due

    def _clear_pending(self) -> None:
        self._dirty_since = None
        self._last_edit_at = None
        self._next_poll_at = None
        self._last_success_revision = None
        self._next_retry_at = None
        self._failure_count = 0
        self._was_eligible = False

    def reset_session(self) -> None:
        """Fence old epoch callbacks, including a reopen at the *same* path."""
        self._epoch += 1
        self._owner = None
        self._path = None
        self._observed = None
        self._revision = 0
        self._clear_pending()
        # A dispatched writer still owns its slot until it completes. Only the
        # physical IO adapter (W06-B/C) may safely abort/fence its disk writes.

    def close(self) -> None:
        """Stop future eligibility; old completion cannot claim success."""
        if not self._closed:
            self.reset_session()
            self._closed = True

    def set_paused(self, paused: bool) -> None:
        """Pause dispatch during modal decisions, switching or app teardown."""
        self._paused = bool(paused)

    def _observe(self, session: ProjectSession, now: float) -> None:
        state = session.current
        path = session.path
        eligible = state is not None and path is not None and session.is_dirty

        if session is not self._owner or path != self._path:
            self.reset_session()
            self._owner = session
            self._path = path
            self._observed = deepcopy(state) if state is not None else None
            if eligible:
                self._revision = 1
                self._dirty_since = now
                self._last_edit_at = now
                self._next_poll_at = now + _POLL_SECONDS
            self._was_eligible = eligible
            return

        state_changed = state != self._observed
        if state_changed:
            self._revision += 1
            self._observed = deepcopy(state) if state is not None else None

        if not eligible:
            if self._was_eligible:
                # A successful manual Save or Undo back to saved baseline
                # invalidates old writer tokens. Never treat autosave as Save.
                self._epoch += 1
            self._clear_pending()
            return

        if not self._was_eligible:
            self._dirty_since = now
            self._last_edit_at = now
            self._next_poll_at = now + _POLL_SECONDS
            self._last_success_revision = None
            self._next_retry_at = None
            self._failure_count = 0
        elif state_changed:
            if self._dirty_since is None:
                self._dirty_since = now
            self._last_edit_at = now

        self._was_eligible = True

    def tick(self, session: ProjectSession) -> SnapshotRequest | None:
        """Observe a completed canonical command and dispatch at most once.

        No file is written: a future adapter must accept a request, serialize
        it under a path lease, and report completion. Callers may also poll
        every 60 seconds for missed notifications; polling isn't a forced write.
        """
        now = self._now()
        if self._closed:
            return None

        self._observe(session, now)
        if self._next_poll_at is not None and now >= self._next_poll_at:
            missed = int((now - self._next_poll_at) // _POLL_SECONDS) + 1
            self._next_poll_at += missed * _POLL_SECONDS

        due = self.next_due_at
        if due is None or now < due or session.current is None or session.path is None:
            return None

        assert self._dirty_since is not None
        request = SnapshotRequest(
            epoch=self._epoch,
            revision=self._revision,
            path=session.path,
            project_state=deepcopy(session.current),
            first_dirty_at=self._dirty_since,
        )
        self._inflight = request
        # The captured revision is now in-flight; any newer actual edit owns a
        # *new* first-dirty deadline, while an old request still holds the slot.
        self._dirty_since = None
        return request

    def complete(self, request: SnapshotRequest, *, success: bool) -> bool:
        """Release only the authentic dispatched request; reject stale epochs.

        True means the completion was accepted into the current scheduler
        state; it does NOT guarantee persistent snapshot validity (W06-B).
        """
        now = self._now()
        if request is not self._inflight:
            return False
        self._inflight = None
        if (
            self._closed
            or request.epoch != self._epoch
            or request.path != self._path
            or not self._was_eligible
        ):
            return False

        if success:
            self._last_success_revision = request.revision
            self._failure_count = 0
            self._next_retry_at = None
        else:
            delay = _RETRY_SECONDS[min(self._failure_count, len(_RETRY_SECONDS) - 1)]
            self._failure_count += 1
            self._next_retry_at = now + delay
            # On failure, the original captured edit remains unprotected.
            if self._dirty_since is None:
                self._dirty_since = request.first_dirty_at

        return True
