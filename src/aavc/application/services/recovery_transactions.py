"""W06-C transactions around the *single* ProjectSession and existing file ports.

UI-neutral and intentionally explicit: no QTimer, modal or automatic Open is
installed here. W06-D will call this service only after the existing unsaved
changes guard and the approved recovery dialog. No operation probes another
project as a side effect of merely hovering/previewing.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from aavc.application.services.project_session import ProjectSession
from aavc.application.services.recovery_coordinator import (
    RecoveryCoordinator,
    SnapshotRequest,
)
from aavc.domain.project.models import ProjectState
from aavc.persistence.serializer import (
    loads_project,
    temporary_sibling_path,
)
from aavc.persistence.snapshot_provenance import (
    ProvenanceStore,
    RecoveryCandidate,
    RecoveryRaceChanged,
)


class GuardRequired(RuntimeError):
    """The existing Save/Discard/Cancel guard must be answered first."""


class RecoveryCommitPartial(RuntimeError):
    """Disk/session commit or cleanup diverged; never claim unchanged disk."""

    def __init__(self, code: str, backup_path: Path | None = None) -> None:
        super().__init__(code)
        self.backup_path = backup_path


@dataclass(frozen=True, slots=True)
class RecoveryPreflight:
    path: Path
    saved_sha256: str
    candidate: RecoveryCandidate
    prior_path: Path | None
    prior_state: ProjectState | None


@dataclass(frozen=True, slots=True)
class RestoreOutcome:
    path: Path
    backup_path: Path


def _sha(path: Path) -> str:
    if path.is_symlink():
        raise ValueError("PATH_ALIAS_UNSAFE")
    return sha256(path.read_bytes()).hexdigest()


def _unsafe(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("PATH_ALIAS_UNSAFE")


def _numbered_backup(path: Path, original: bytes) -> Path:
    """Exclusive non-clobber backup; dispose an incomplete copy on failure."""
    for index in range(10000):
        suffix = ".pre-recovery.bak" if index == 0 else f".pre-recovery.{index}.bak"
        backup = path.with_suffix(path.suffix + suffix)
        try:
            with backup.open("xb") as target:
                target.write(original)
                target.flush()
                os.fsync(target.fileno())
            return backup
        except FileExistsError:
            continue
        except Exception:
            # Never remove someone else's backup on name collision.
            backup.unlink(missing_ok=True)
            raise
    raise RecoveryRaceChanged("BACKUP_NAMESPACE_EXHAUSTED")


class RecoveryTransactions:
    """One synchronous, fail-closed transaction surface for a GUI adapter.

    Shared ProvenanceStore lock serializes Save/Restore/Discard and dispatches
    made through this service. External programs have independent locks; exact
    disk and snapshot bytes are rechecked before destructive operations.
    """

    def __init__(
        self,
        session: ProjectSession,
        *,
        store: ProvenanceStore | None = None,
        coordinator: RecoveryCoordinator | None = None,
        fault_hook: Callable[[str], None] | None = None,
    ) -> None:
        self.session = session
        self.store = store or ProvenanceStore()
        self.coordinator = coordinator
        self._fault_hook = fault_hook

    def _fault(self, phase: str) -> None:
        if self._fault_hook is not None:
            self._fault_hook(phase)

    def _fence(self) -> None:
        if self.coordinator is not None:
            self.coordinator.reset_session()

    def _ensure_known_baseline(self) -> Path:
        path = self.session.path
        if path is None:
            raise ValueError("PROJECT_PATH_REQUIRED")
        _unsafe(path)
        expected = self.session.saved_disk_sha256
        if expected is None or not path.is_file() or _sha(path) != expected:
            raise RecoveryRaceChanged("BASELINE_CHANGED")
        return path

    def save(self) -> Path:
        """Manual Save is a transaction, not a candidate snapshot.

        Before writing, quarantine an *owned verified* existing candidate;
        rollback its filenames on a failed Save. Uncertain/foreign recovery
        files are preserved as forensic evidence. After successful Save, stale
        coordinator tokens are fenced and owned quarantine is retired.
        """
        with self.store.locked_transaction():
            path = self._ensure_known_baseline()
            probe = self.store.inspect(path)
            held = None
            if probe.status == "VERIFIED":
                held = self.store.quarantine_candidate(path, probe)
            try:
                # Defend an external change that arrived while staging files.
                self._fault("before_manual_save")
                if _sha(path) != self.session.saved_disk_sha256:
                    raise RecoveryRaceChanged("BASELINE_CHANGED")
                saved = self.session.save()
            except Exception:
                if held is not None:
                    try:
                        self.store.rollback_quarantine(held)
                    except Exception as exc:
                        raise RecoveryCommitPartial("SAVE_ROLLBACK_PARTIAL") from exc
                raise
            self._fence()
            if held is not None:
                try:
                    self.store.retire_quarantine(held)
                except Exception as exc:
                    raise RecoveryCommitPartial("SAVE_CLEANUP_PARTIAL") from exc
            return saved

    def save_as(self, target: str | Path) -> Path:
        """No existing project/sidecar/snapshot may be overwritten by Save As."""
        original = Path(target).absolute()
        _unsafe(original)
        destination = original.resolve(strict=False)
        if self.session.path == destination:
            return self.save()
        with self.store.locked_transaction():
            paths = (
                destination,
                self.store.snapshot_path(destination),
                self.store.metadata_path(destination),
            )
            if any(p.exists() or p.is_symlink() for p in paths):
                raise RecoveryRaceChanged("SAVE_AS_RECOVERY_COLLISION")
            self._fault("before_save_as_commit")
            if any(p.exists() or p.is_symlink() for p in paths):
                raise RecoveryRaceChanged("SAVE_AS_RECOVERY_COLLISION")
            result = self.session.save(destination)
            self._fence()
            return result

    def probe_open(
        self, target: str | Path, *, guard_approved: bool = False
    ) -> RecoveryPreflight:
        """Read-only probe AFTER old-session dirty guard, never a hidden Save."""
        if self.session.is_dirty and not guard_approved:
            raise GuardRequired("UNSAVED_SESSION_GUARD")
        raw = Path(target).absolute()
        _unsafe(raw)
        path = raw.resolve(strict=False)
        with self.store.locked_transaction():
            _unsafe(path)
            # Invalid saved content must never auto-create from lone autosave.
            content = path.read_bytes()
            loads_project(content.decode("utf-8"))
            saved_digest = sha256(content).hexdigest()
            candidate = self.store.inspect(path)
            if candidate.disk_sha256 != saved_digest:
                raise RecoveryRaceChanged("RECOVERY_RACE_CHANGED")
            return RecoveryPreflight(
                path, saved_digest, candidate, self.session.path, deepcopy(self.session.current)
            )

    def cancel(self, plan: RecoveryPreflight) -> None:
        """Explicit no-op; caller retains previous path/state/history."""
        del plan

    def _revalidate(self, plan: RecoveryPreflight) -> None:
        if self.session.path != plan.prior_path or self.session.current != plan.prior_state:
            raise RecoveryRaceChanged("RECOVERY_RACE_CHANGED")
        if _sha(plan.path) != plan.saved_sha256:
            raise RecoveryRaceChanged("RECOVERY_RACE_CHANGED")
        current = self.store.inspect(plan.path)
        if current != plan.candidate:
            raise RecoveryRaceChanged("RECOVERY_RACE_CHANGED")
        if plan.candidate.status in ("VERIFIED", "UNCERTAIN"):
            self.store.revalidate(plan.path, plan.candidate)

    def use_saved(self, plan: RecoveryPreflight) -> ProjectState:
        """User-selected disk version; quarantine only verified/uncertain candidate.

        Invalid candidate is left untouched and only the valid saved disk file
        may be opened, following user acknowledgment via the approved DLG-03.
        """
        with self.store.locked_transaction():
            self._revalidate(plan)
            held = None
            if plan.candidate.status in ("VERIFIED", "UNCERTAIN"):
                held = self.store.quarantine_candidate(plan.path, plan.candidate)
            try:
                self._fault("before_disk_adoption")
                opened = self.session.open(plan.path)
                if self.session.saved_disk_sha256 != plan.saved_sha256:
                    raise RecoveryCommitPartial("DISCARD_COMMIT_PARTIAL")
            except Exception:
                if held is not None:
                    try:
                        self.store.rollback_quarantine(held)
                    except Exception as exc:
                        raise RecoveryCommitPartial("DISCARD_ROLLBACK_PARTIAL") from exc
                raise
            self._fence()
            if held is not None:
                try:
                    self.store.retire_quarantine(held)
                except Exception as exc:
                    raise RecoveryCommitPartial("DISCARD_CLEANUP_PARTIAL") from exc
            return opened

    def restore(
        self,
        plan: RecoveryPreflight,
        *,
        confirm_conflict: bool = False,
    ) -> RestoreOutcome:
        """Confirmed Restore with byte-preserving numbered backup and CAS.

        A failed pre-commit cannot replace the original; if session adoption
        fails after durable replace, expose RESTORE_COMMIT_PARTIAL + backup.
        """
        if plan.candidate.status in ("INVALID", "ABSENT"):
            raise ValueError("RECOVERY_CANDIDATE_NOT_RESTORABLE")
        if plan.candidate.status != "VERIFIED" and not confirm_conflict:
            raise GuardRequired("CONFLICT_CONFIRMATION_REQUIRED")

        with self.store.locked_transaction():
            self._revalidate(plan)
            snapshot = self.store.snapshot_path(plan.path)
            _unsafe(snapshot)
            original = plan.path.read_bytes()
            candidate_bytes = snapshot.read_bytes()
            loads_project(candidate_bytes.decode("utf-8"))
            if (
                sha256(original).hexdigest() != plan.saved_sha256
                or sha256(candidate_bytes).hexdigest() != plan.candidate.snapshot_sha256
            ):
                raise RecoveryRaceChanged("RECOVERY_RACE_CHANGED")
            backup = _numbered_backup(plan.path, original)
            self._fault("after_backup")
            temp = temporary_sibling_path(plan.path, label="restore")
            try:
                with temp.open("xb") as output:
                    output.write(candidate_bytes)
                    output.flush()
                    os.fsync(output.fileno())
                # Re-check every user-controlled path immediately before replace.
                self._fault("before_restore_replace")
                self._revalidate(plan)
                if _sha(temp) != plan.candidate.snapshot_sha256:
                    raise RecoveryRaceChanged("RECOVERY_RACE_CHANGED")
                temp.replace(plan.path)
            finally:
                temp.unlink(missing_ok=True)
            # Disk is already replaced. Never imply a reversible, single
            # transaction with Qt session adoption.
            try:
                self.session.open(plan.path)
            except Exception as exc:
                self._fence()
                raise RecoveryCommitPartial("RESTORE_COMMIT_PARTIAL", backup) from exc
            self._fence()
            return RestoreOutcome(plan.path, backup)

    def persist_due_snapshot(self, request: SnapshotRequest) -> bool:
        """Consume W06-A eligibility under same W06-B/W06-C process lock.

        The UI executor in W06-D will invoke this on its serial writer.
        Returns False for stale requests; never writes old epoch/path after Save.
        """
        if self.coordinator is None:
            raise ValueError("RECOVERY_COORDINATOR_REQUIRED")
        with self.store.locked_transaction():
            if (
                self.coordinator.inflight is not request
                or self.coordinator.epoch != request.epoch
                or not self.session.is_dirty
                or self.session.path != request.path
                or self.session.saved_disk_sha256 is None
            ):
                self.coordinator.complete(request, success=False)
                return False
            try:
                digest = self.session.saved_disk_sha256
                assert digest is not None
                self.store.write_snapshot(
                    request.project_state,
                    request.path,
                    saved_baseline_sha256=digest,
                )
            except Exception:
                self.coordinator.complete(request, success=False)
                raise
            return self.coordinator.complete(request, success=True)
