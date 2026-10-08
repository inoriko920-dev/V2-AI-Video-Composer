"""W06-B safe snapshot provenance and read-only candidate inspection.

No Qt, no ProjectSession mutation, no Save/Restore transaction, no automatic
timer binding. All on-disk snapshot JSON writes reuse the existing RecoveryManager
and serializer. A snapshot followed by a metadata descriptor is *not* a single
atomic transaction: missing/stale metadata always produces UNCERTAIN.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Callable, Literal
from uuid import uuid4

from aavc.domain.project.models import ProjectState
from aavc.persistence.recovery import RecoveryManager
from aavc.persistence.serializer import dumps_project, load_project, temporary_sibling_path

CandidateStatus = Literal["ABSENT", "VERIFIED", "UNCERTAIN", "INVALID"]
_MAX_METADATA_BYTES = 16 * 1024
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SECRET = re.compile(r"AIza[A-Za-z0-9_-]{35}|sk-[A-Za-z0-9_-]{20,}")
_GLOBAL_IO_LEASE = RLock()


class RecoveryRaceChanged(RuntimeError):
    """A baseline/candidate changed; never use the previous decision token."""


@dataclass(frozen=True, slots=True)
class RecoveryCandidate:
    status: CandidateStatus
    reason: str
    disk_sha256: str | None
    snapshot_sha256: str | None


@dataclass(frozen=True, slots=True)
class QuarantinedCandidate:
    project_path: Path
    snapshot_path: Path
    metadata_path: Path
    snapshot_copy: Path
    metadata_copy: Path | None
    snapshot_sha256: str
    metadata_sha256: str | None


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _unsafe(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("PATH_ALIAS_UNSAFE")


def _file_sha(path: Path) -> str:
    _unsafe(path)
    return _digest(path.read_bytes())


def _path_identity(path: Path) -> str:
    _unsafe(path)
    # Normalise case on Windows only; never include original path in descriptor.
    normalized = os.path.normcase(str(path.resolve(strict=True)))
    return _digest(normalized.encode("utf-8"))


def _validate_descriptor(data: bytes) -> dict[str, str | int]:
    if len(data) > _MAX_METADATA_BYTES:
        raise ValueError("AUTOSAVE_META_OVERSIZE")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("AUTOSAVE_META_INVALID") from exc
    required = {
        "format_version", "project_path_identity", "saved_baseline_sha256",
        "snapshot_sha256", "schema_version", "write_generation",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("AUTOSAVE_META_INVALID")
    if type(value["format_version"]) is not int or value["format_version"] != 1:
        raise ValueError("AUTOSAVE_META_UNKNOWN_VERSION")
    if type(value["schema_version"]) is not int or value["schema_version"] not in (3, 4):
        raise ValueError("AUTOSAVE_META_INVALID_SCHEMA")
    for key in ("project_path_identity", "saved_baseline_sha256", "snapshot_sha256"):
        if type(value[key]) is not str or _DIGEST.fullmatch(value[key]) is None:
            raise ValueError("AUTOSAVE_META_INVALID")
    if type(value["write_generation"]) is not str or re.fullmatch(
        r"[a-f0-9]{32}", value["write_generation"]
    ) is None:
        raise ValueError("AUTOSAVE_META_INVALID")
    return value


class ProvenanceStore:
    """Thin, fail-closed IO adapter for future W06-C transactional orchestration.

    The process-wide lock serializes *this adapter's* operations. W06-C must
    fence ProjectSession Save/Restore against this lock, because locking this
    adapter alone cannot serialize unrelated external editors/processes.
    """

    def __init__(
        self,
        *,
        manager: RecoveryManager | None = None,
        fault_hook: Callable[[str], None] | None = None,
    ) -> None:
        self._manager = manager or RecoveryManager()
        self._fault_hook = fault_hook

    def _fault(self, phase: str) -> None:
        if self._fault_hook is not None:
            self._fault_hook(phase)

    def snapshot_path(self, project_path: str | Path) -> Path:
        return self._manager.recovery_path_for(project_path)

    def metadata_path(self, project_path: str | Path) -> Path:
        snapshot = self.snapshot_path(project_path)
        return snapshot.with_name(snapshot.name + ".meta.json")

    def _check_paths(self, project_path: Path) -> None:
        for path in (project_path, self.snapshot_path(project_path), self.metadata_path(project_path)):
            _unsafe(path)
        if not project_path.is_file():
            raise ValueError("PROJECT_DESTINATION_UNREADABLE")

    def _publish_snapshot(self, project: ProjectState, path: Path) -> None:
        self._manager.write_snapshot(project, path)

    def _publish_metadata(self, metadata: Path, value: dict[str, str | int]) -> None:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(raw) > _MAX_METADATA_BYTES:
            raise ValueError("AUTOSAVE_META_OVERSIZE")
        temporary = temporary_sibling_path(metadata, label="meta")
        try:
            _unsafe(temporary)
            with temporary.open("xb") as file:
                file.write(raw)
                file.flush()
                os.fsync(file.fileno())
            self._fault("before_meta_replace")
            temporary.replace(metadata)
        finally:
            temporary.unlink(missing_ok=True)

    def write_snapshot(
        self,
        project: ProjectState,
        project_path: str | Path,
        *,
        saved_baseline_sha256: str,
    ) -> RecoveryCandidate:
        """Publish snapshot first, then descriptor; never touch the real project.

        Raises on stale baseline, symlink, invalid model, forbidden credentials
        or IO errors. An interrupted second phase is inspected as UNCERTAIN.
        """
        with _GLOBAL_IO_LEASE:
            path = Path(project_path)
            self._check_paths(path)
            if _DIGEST.fullmatch(saved_baseline_sha256) is None:
                raise ValueError("INVALID_BASELINE_DIGEST")
            state_json = dumps_project(project)
            # Reject known credential-like values; don't put their bytes in an
            # autosave. This is not a general-purpose secret-scanner guarantee.
            if _SECRET.search(state_json) or any(
                any(word in name.lower() for word in ("api_key", "token", "secret", "password"))
                for name in project.metadata
            ):
                raise ValueError("SENSITIVE_PROJECT_FIELD")
            # Parser verifies data invariants and v3/v4 advanced contract.
            from aavc.persistence.serializer import loads_project

            loads_project(state_json)
            disk_sha = _file_sha(path)
            if disk_sha != saved_baseline_sha256:
                raise RecoveryRaceChanged("BASELINE_CHANGED")
            # A syntactically corrupt saved file is not a usable baseline.
            load_project(path)
            identity = _path_identity(path)
            self._fault("before_snapshot")
            self._publish_snapshot(project, path)
            snapshot = self.snapshot_path(path)
            snap_sha = _file_sha(snapshot)
            self._fault("after_snapshot")
            if _file_sha(path) != disk_sha:
                raise RecoveryRaceChanged("BASELINE_CHANGED")
            descriptor: dict[str, str | int] = {
                "format_version": 1,
                "project_path_identity": identity,
                "saved_baseline_sha256": disk_sha,
                "snapshot_sha256": snap_sha,
                "schema_version": project.schema_version,
                "write_generation": uuid4().hex,
            }
            self._publish_metadata(self.metadata_path(path), descriptor)
            return RecoveryCandidate("VERIFIED", "MATCHING_BASELINE", disk_sha, snap_sha)

    def inspect(self, project_path: str | Path) -> RecoveryCandidate:
        """Read-only classification; never delete or auto-restore a candidate."""
        with _GLOBAL_IO_LEASE:
            path = Path(project_path)
            snapshot = self.snapshot_path(path)
            metadata = self.metadata_path(path)
            try:
                self._check_paths(path)
                disk_sha = _file_sha(path)
                # Both project and snapshot must decode, with valid schemas.
                load_project(path)
            except (ValueError, OSError) as exc:
                return RecoveryCandidate("INVALID", "PROJECT_UNREADABLE", None, None)
            if not snapshot.exists():
                return RecoveryCandidate("ABSENT", "NO_SNAPSHOT", disk_sha, None)
            try:
                snap_sha = _file_sha(snapshot)
                snap_project = load_project(snapshot)
            except (ValueError, OSError, UnicodeDecodeError):
                return RecoveryCandidate("INVALID", "AUTOSAVE_INVALID_SCHEMA", disk_sha, None)
            if not metadata.is_file():
                return RecoveryCandidate("UNCERTAIN", "AUTOSAVE_META_UNCERTAIN", disk_sha, snap_sha)
            try:
                desc = _validate_descriptor(metadata.read_bytes())
                identity = _path_identity(path)
            except (ValueError, OSError):
                return RecoveryCandidate("UNCERTAIN", "AUTOSAVE_META_UNCERTAIN", disk_sha, snap_sha)
            if desc["snapshot_sha256"] != snap_sha:
                return RecoveryCandidate("UNCERTAIN", "SNAPSHOT_CHANGED", disk_sha, snap_sha)
            if desc["project_path_identity"] != identity:
                return RecoveryCandidate("UNCERTAIN", "PROJECT_IDENTITY_CHANGED", disk_sha, snap_sha)
            if desc["schema_version"] != snap_project.schema_version:
                return RecoveryCandidate("UNCERTAIN", "SCHEMA_MISMATCH", disk_sha, snap_sha)
            if desc["saved_baseline_sha256"] != disk_sha:
                return RecoveryCandidate("UNCERTAIN", "BASELINE_CHANGED", disk_sha, snap_sha)
            return RecoveryCandidate("VERIFIED", "MATCHING_BASELINE", disk_sha, snap_sha)

    def revalidate(self, project_path: str | Path, candidate: RecoveryCandidate) -> None:
        """Reject stale preflight tokens before W06-C destructive operations."""
        current = self.inspect(project_path)
        if (
            current.status != candidate.status
            or current.disk_sha256 != candidate.disk_sha256
            or current.snapshot_sha256 != candidate.snapshot_sha256
            or current.reason != candidate.reason
            or candidate.status not in ("VERIFIED", "UNCERTAIN")
        ):
            raise RecoveryRaceChanged("RECOVERY_RACE_CHANGED")

    def quarantine_candidate(
        self, project_path: str | Path, candidate: RecoveryCandidate
    ) -> QuarantinedCandidate:
        """Stage *only* the checked candidate, never silently delete it."""
        with _GLOBAL_IO_LEASE:
            path = Path(project_path)
            self.revalidate(path, candidate)
            snapshot = self.snapshot_path(path)
            metadata = self.metadata_path(path)
            assert candidate.snapshot_sha256 is not None
            snapshot_copy = snapshot.with_name("." + snapshot.name + ".quarantine-" + uuid4().hex)
            metadata_copy = (
                metadata.with_name("." + metadata.name + ".quarantine-" + uuid4().hex)
                if metadata.is_file()
                else None
            )
            meta_sha = _file_sha(metadata) if metadata_copy is not None else None
            snapshot.rename(snapshot_copy)
            try:
                self._fault("after_quarantine_snapshot")
                if metadata_copy is not None:
                    metadata.rename(metadata_copy)
            except Exception:
                if snapshot.exists():
                    raise RecoveryRaceChanged("QUARANTINE_COLLISION") from None
                snapshot_copy.rename(snapshot)
                raise
            return QuarantinedCandidate(
                path, snapshot, metadata, snapshot_copy, metadata_copy,
                candidate.snapshot_sha256, meta_sha,
            )

    def rollback_quarantine(self, held: QuarantinedCandidate) -> None:
        """Do not overwrite a new candidate arriving during rollback."""
        with _GLOBAL_IO_LEASE:
            if held.snapshot_path.exists() or held.metadata_path.exists():
                raise RecoveryRaceChanged("QUARANTINE_COLLISION")
            if _file_sha(held.snapshot_copy) != held.snapshot_sha256:
                raise RecoveryRaceChanged("QUARANTINE_CHANGED")
            if held.metadata_copy is not None and (
                held.metadata_sha256 is None
                or _file_sha(held.metadata_copy) != held.metadata_sha256
            ):
                raise RecoveryRaceChanged("QUARANTINE_CHANGED")
            held.snapshot_copy.rename(held.snapshot_path)
            if held.metadata_copy is not None:
                held.metadata_copy.rename(held.metadata_path)

    def retire_quarantine(self, held: QuarantinedCandidate) -> None:
        """Later W06-C only: retire proven owned quarantine after session commit."""
        with _GLOBAL_IO_LEASE:
            if _file_sha(held.snapshot_copy) != held.snapshot_sha256:
                raise RecoveryRaceChanged("QUARANTINE_CHANGED")
            if held.metadata_copy is not None and (
                held.metadata_sha256 is None
                or _file_sha(held.metadata_copy) != held.metadata_sha256
            ):
                raise RecoveryRaceChanged("QUARANTINE_CHANGED")
            if held.metadata_copy is not None:
                held.metadata_copy.unlink()
            held.snapshot_copy.unlink()
