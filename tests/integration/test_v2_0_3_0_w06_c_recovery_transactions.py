"""W06-C RED-first integration contracts for session/file transactions.

Only synthetic projects in isolated tmp_path. No Qt, user files or real secrets.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from aavc.application.commands import SetSceneDuration
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.recovery_coordinator import RecoveryCoordinator
from aavc.application.services.recovery_transactions import (
    GuardRequired,
    RecoveryCommitPartial,
    RecoveryTransactions,
)
from aavc.domain.project.models import AssetBinding, ProjectState, Scene
from aavc.persistence.project_repository import ProjectRepository
from aavc.persistence.serializer import load_project, save_project
from aavc.persistence.snapshot_provenance import ProvenanceStore, RecoveryRaceChanged


def project(name: str = "fixture") -> ProjectState:
    return ProjectState(
        schema_version=3,
        title=name,
        source_docx="test.docx",
        asset_directory="synthetic",
        scenes=(Scene(1, ("asset",), ("test",), 3.0),),
        bindings=(AssetBinding("asset", "test", None, "MISSING"),),
        metadata={"test": "W06-C"},
    )


def session(tmp_path: Path, name: str = "A") -> ProjectSession:
    s = ProjectSession()
    s.create(project(name), tmp_path / (name + ".aavcproj"))
    return s


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def snapshot(s: ProjectSession, store: ProvenanceStore, name: str = "recovery") -> None:
    assert s.path is not None
    store.write_snapshot(replace(project(name), scenes=(
        Scene(1, ("asset",), ("test",), 4.0),
    )), s.path, saved_baseline_sha256=digest(s.path))


def test_rcv_04_manual_save_retires_only_verified_candidate(tmp_path: Path) -> None:
    s = session(tmp_path)
    assert s.path is not None
    original = s.path.read_bytes()
    store = ProvenanceStore()
    snapshot(s, store)
    s.execute(SetSceneDuration(1, 4.5))
    tx = RecoveryTransactions(s, store=store)
    saved = tx.save()
    assert saved == s.path
    assert s.path.read_bytes() != original
    assert not s.is_dirty and s.can_undo
    assert not store.snapshot_path(s.path).exists()
    assert not store.metadata_path(s.path).exists()


def test_rcv_04_save_with_uncertain_candidate_preserves_unowned_files(tmp_path: Path) -> None:
    s = session(tmp_path)
    assert s.path is not None
    store = ProvenanceStore()
    snapshot(s, store)
    store.metadata_path(s.path).write_bytes(b"untrusted descriptor")
    before = store.snapshot_path(s.path).read_bytes()
    s.execute(SetSceneDuration(1, 6))
    RecoveryTransactions(s, store=store).save()
    assert not s.is_dirty
    assert store.snapshot_path(s.path).read_bytes() == before
    assert store.metadata_path(s.path).read_bytes() == b"untrusted descriptor"
    assert store.inspect(s.path).status != "VERIFIED"


def test_rcv_05_external_save_conflict_is_fail_closed(tmp_path: Path) -> None:
    s = session(tmp_path)
    assert s.path is not None
    tx = RecoveryTransactions(s)
    s.execute(SetSceneDuration(1, 5))
    other = tmp_path / "other.aavcproj"
    save_project(project("from another process"), other)
    s.path.write_bytes(other.read_bytes())
    before = s.path.read_bytes()
    with pytest.raises(RecoveryRaceChanged, match="BASELINE_CHANGED"):
        tx.save()
    assert s.path.read_bytes() == before
    assert s.is_dirty and s.can_undo
    assert load_project(s.path).title == "from another process"


def test_rcv_05_failed_save_does_not_rebind_or_mutate_history(tmp_path: Path) -> None:
    class FailingRepository(ProjectRepository):
        def save(self, p: ProjectState, path: str | Path) -> Path:
            raise PermissionError("injected denied")

    s = session(tmp_path)
    assert s.path is not None
    original = s.path.read_bytes()
    s.execute(SetSceneDuration(1, 5))
    before = (s.path, s.current, s.is_dirty, s.can_undo, s.can_redo)
    s._repository = FailingRepository()  # isolated injected failure
    with pytest.raises(PermissionError, match="injected"):
        RecoveryTransactions(s).save()
    assert (s.path, s.current, s.is_dirty, s.can_undo, s.can_redo) == before
    assert s.path.read_bytes() == original


@pytest.mark.parametrize("collision", ["project", "snapshot", "metadata"])
def test_rcv_06_24_save_as_collision_no_rebind(tmp_path: Path, collision: str) -> None:
    s = session(tmp_path)
    old = s.path
    assert old is not None
    s.execute(SetSceneDuration(1, 5))
    target = tmp_path / "occupied.aavcproj"
    store = ProvenanceStore()
    destination = {
        "project": target,
        "snapshot": store.snapshot_path(target),
        "metadata": store.metadata_path(target),
    }[collision]
    destination.write_bytes(b"foreign-owned")
    with pytest.raises(RecoveryRaceChanged, match="SAVE_AS_RECOVERY_COLLISION"):
        RecoveryTransactions(s, store=store).save_as(target)
    assert s.path == old and s.is_dirty
    assert destination.read_bytes() == b"foreign-owned"


def test_rcv_06_save_as_success_preserves_old_snapshot(tmp_path: Path) -> None:
    s = session(tmp_path)
    assert s.path is not None
    old = s.path
    store = ProvenanceStore()
    snapshot(s, store)
    old_bytes = store.snapshot_path(old).read_bytes()
    s.execute(SetSceneDuration(1, 4))
    target = tmp_path / "new.aavcproj"
    RecoveryTransactions(s, store=store).save_as(target)
    assert s.path == target.resolve() and not s.is_dirty
    assert store.snapshot_path(old).read_bytes() == old_bytes
    assert target.is_file()
    assert not store.snapshot_path(target).exists()


def test_rcv_07_10_23_probe_guard_before_io_and_cancel_zero_mutation(tmp_path: Path) -> None:
    s = session(tmp_path, "old")
    candidate = tmp_path / "target.aavcproj"
    save_project(project("target"), candidate)
    s.execute(SetSceneDuration(1, 5))
    tx = RecoveryTransactions(s)
    before = (s.path, s.current, s.can_undo, s.is_dirty, digest(candidate))
    with pytest.raises(GuardRequired, match="UNSAVED_SESSION_GUARD"):
        tx.probe_open(candidate)
    plan = tx.probe_open(candidate, guard_approved=True)
    assert plan.candidate.status == "ABSENT"
    tx.cancel(plan)
    assert (s.path, s.current, s.can_undo, s.is_dirty, digest(candidate)) == before


def test_rcv_07_verified_restore_creates_backup_and_fresh_history(tmp_path: Path) -> None:
    target = session(tmp_path, "target")
    assert target.path is not None
    target_path = target.path
    old_bytes = target_path.read_bytes()
    store = ProvenanceStore()
    snapshot(target, store)
    active = session(tmp_path, "active")
    tx = RecoveryTransactions(active, store=store)
    plan = tx.probe_open(target_path)
    assert plan.candidate.status == "VERIFIED"
    outcome = tx.restore(plan)
    assert outcome.backup_path is not None
    assert outcome.backup_path.read_bytes() == old_bytes
    assert load_project(target_path).title == "recovery"
    assert active.path == target_path.resolve()
    assert active.current is not None and active.current.title == "recovery"
    assert not active.can_undo and not active.can_redo and not active.is_dirty
    assert store.snapshot_path(target_path).is_file()


def test_rcv_08_conflict_restore_requires_second_explicit_approval(tmp_path: Path) -> None:
    target = session(tmp_path, "target")
    assert target.path is not None
    store = ProvenanceStore()
    snapshot(target, store)
    store.metadata_path(target.path).unlink()
    active = session(tmp_path, "active")
    tx = RecoveryTransactions(active, store=store)
    plan = tx.probe_open(target.path)
    assert plan.candidate.status == "UNCERTAIN"
    before = (active.path, active.current, target.path.read_bytes())
    with pytest.raises(GuardRequired, match="CONFLICT_CONFIRMATION_REQUIRED"):
        tx.restore(plan)
    assert (active.path, active.current, target.path.read_bytes()) == before
    result = tx.restore(plan, confirm_conflict=True)
    assert result.backup_path is not None and result.backup_path.is_file()


def test_rcv_09_discard_quarantine_commit_and_preserve_other_files(tmp_path: Path) -> None:
    target = session(tmp_path, "target")
    assert target.path is not None
    store = ProvenanceStore()
    snapshot(target, store)
    different = tmp_path / "different.autosave"
    different.write_bytes(b"keep-me")
    active = session(tmp_path, "active")
    tx = RecoveryTransactions(active, store=store)
    plan = tx.probe_open(target.path)
    tx.use_saved(plan)
    assert active.path == target.path
    assert active.current is not None and active.current.title == "target"
    assert not store.snapshot_path(target.path).exists()
    assert different.read_bytes() == b"keep-me"


def test_rcv_09_discard_rollback_if_adoption_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = session(tmp_path, "target")
    assert target.path is not None
    store = ProvenanceStore()
    snapshot(target, store)
    active = session(tmp_path, "active")
    tx = RecoveryTransactions(active, store=store)
    plan = tx.probe_open(target.path)
    before = (active.path, active.current, store.snapshot_path(target.path).read_bytes())
    def fail_open(_path: str | Path) -> ProjectState:
        raise ValueError("injected adoption failure")
    monkeypatch.setattr(active, "open", fail_open)
    with pytest.raises(ValueError, match="injected adoption"):
        tx.use_saved(plan)
    assert (active.path, active.current, store.snapshot_path(target.path).read_bytes()) == before
    assert store.inspect(target.path).status == "VERIFIED"


@pytest.mark.parametrize("source", ["disk", "snapshot", "descriptor"])
def test_rcv_17_20_restore_token_race_no_mutation(tmp_path: Path, source: str) -> None:
    target = session(tmp_path, "target")
    assert target.path is not None
    store = ProvenanceStore()
    snapshot(target, store)
    active = session(tmp_path, "active")
    tx = RecoveryTransactions(active, store=store)
    plan = tx.probe_open(target.path)
    if source == "disk":
        target.path.write_bytes(target.path.read_bytes() + b" ")
    elif source == "snapshot":
        store.snapshot_path(target.path).write_bytes(store.snapshot_path(target.path).read_bytes() + b" ")
    else:
        store.metadata_path(target.path).write_bytes(store.metadata_path(target.path).read_bytes() + b" ")
    changed = (active.path, active.current, target.path.read_bytes())
    with pytest.raises(RecoveryRaceChanged, match="RECOVERY_RACE_CHANGED"):
        tx.restore(plan)
    assert (active.path, active.current, target.path.read_bytes()) == changed
    assert not list(tmp_path.glob("*.pre-recovery*"))


def test_at_13_existing_backup_never_overwritten(tmp_path: Path) -> None:
    s = session(tmp_path)
    assert s.path is not None
    store = ProvenanceStore()
    snapshot(s, store)
    backup = s.path.with_suffix(s.path.suffix + ".pre-recovery.bak")
    backup.write_bytes(b"old-backup")
    tx = RecoveryTransactions(s, store=store)
    result = tx.restore(tx.probe_open(s.path))
    assert backup.read_bytes() == b"old-backup"
    assert result.backup_path is not None and ".1." in result.backup_path.name


def test_at_15_failed_replace_keeps_disk_and_candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    s = session(tmp_path)
    assert s.path is not None
    store = ProvenanceStore()
    snapshot(s, store)
    before = s.path.read_bytes()
    snap = store.snapshot_path(s.path).read_bytes()
    original = Path.replace
    def fail_recovery_replace(self: Path, target: Path) -> Path:
        if target == s.path and ".aavc-restore-" in self.name:
            raise PermissionError("injected replace refused")
        return original(self, target)
    monkeypatch.setattr(Path, "replace", fail_recovery_replace)
    with pytest.raises(PermissionError, match="injected replace"):
        RecoveryTransactions(s, store=store).restore(RecoveryTransactions(s, store=store).probe_open(s.path))
    assert s.path.read_bytes() == before
    assert store.snapshot_path(s.path).read_bytes() == snap


def test_at_16_after_disk_commit_failed_session_adoption_reports_partial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = session(tmp_path)
    assert s.path is not None
    store = ProvenanceStore()
    snapshot(s, store)
    before = s.path.read_bytes()
    def fail_open(_path: str | Path) -> ProjectState:
        raise RuntimeError("synthetic UI state exception")
    monkeypatch.setattr(s, "open", fail_open)
    tx = RecoveryTransactions(s, store=store)
    with pytest.raises(RecoveryCommitPartial, match="RESTORE_COMMIT_PARTIAL") as ex:
        tx.restore(tx.probe_open(s.path))
    assert ex.value.backup_path is not None
    assert ex.value.backup_path.read_bytes() == before
    assert s.path.read_bytes() != before


def test_at_19_saved_project_blocks_stale_snapshot_completion(tmp_path: Path) -> None:
    s = session(tmp_path)
    clock = [0.0]
    c = RecoveryCoordinator(clock=lambda: clock[0])
    store = ProvenanceStore()
    tx = RecoveryTransactions(s, store=store, coordinator=c)
    s.execute(SetSceneDuration(1, 4))
    c.tick(s)
    clock[0] = 20
    req = c.tick(s)
    assert req is not None
    tx.save()
    assert tx.persist_due_snapshot(req) is False
    assert s.path is not None and not store.snapshot_path(s.path).exists()


def test_rcv_01_scheduler_persists_snapshot_without_cleaning_session(tmp_path: Path) -> None:
    s = session(tmp_path)
    clock = [0.0]
    c = RecoveryCoordinator(clock=lambda: clock[0])
    store = ProvenanceStore()
    tx = RecoveryTransactions(s, store=store, coordinator=c)
    s.execute(SetSceneDuration(1, 4))
    c.tick(s)
    clock[0] = 20
    req = c.tick(s)
    assert req is not None
    before_disk = s.path.read_bytes() if s.path else None
    assert tx.persist_due_snapshot(req) is True
    assert s.path is not None
    assert store.inspect(s.path).status == "VERIFIED"
    assert s.path.read_bytes() == before_disk and s.is_dirty and s.can_undo
    assert c.last_success_revision == req.revision


def test_rcv_05_external_edit_before_manual_save_rolls_back_quarantine(tmp_path: Path) -> None:
    s = session(tmp_path)
    assert s.path is not None
    store = ProvenanceStore()
    snapshot(s, store)
    old_candidate = store.snapshot_path(s.path).read_bytes()
    s.execute(SetSceneDuration(1, 7))
    external = save_project(project("external"), tmp_path / "external.aavcproj").read_bytes()

    def fault(phase: str) -> None:
        if phase == "before_manual_save":
            assert s.path is not None
            s.path.write_bytes(external)

    with pytest.raises(RecoveryRaceChanged, match="BASELINE_CHANGED"):
        RecoveryTransactions(s, store=store, fault_hook=fault).save()
    assert s.path.read_bytes() == external
    assert store.snapshot_path(s.path).read_bytes() == old_candidate
    assert store.inspect(s.path).status == "UNCERTAIN"
    assert s.is_dirty


def test_rcv_24_race_creates_sidecar_before_save_as_commit(tmp_path: Path) -> None:
    s = session(tmp_path)
    store = ProvenanceStore()
    new_path = tmp_path / "new.aavcproj"
    foreign = store.metadata_path(new_path)

    def fault(phase: str) -> None:
        if phase == "before_save_as_commit":
            foreign.write_bytes(b"owned by another writer")

    with pytest.raises(RecoveryRaceChanged, match="SAVE_AS_RECOVERY_COLLISION"):
        RecoveryTransactions(s, store=store, fault_hook=fault).save_as(new_path)
    assert s.path is not None and s.path.name == "A.aavcproj"
    assert not new_path.exists()
    assert foreign.read_bytes() == b"owned by another writer"


def test_rcv_09_discard_fault_after_quarantine_rolls_back(tmp_path: Path) -> None:
    target = session(tmp_path, "target")
    assert target.path is not None
    store = ProvenanceStore()
    snapshot(target, store)
    before = store.snapshot_path(target.path).read_bytes()
    active = session(tmp_path, "active")
    old_path = active.path

    def fault(phase: str) -> None:
        if phase == "before_disk_adoption":
            raise OSError("synthetic open failure")

    tx = RecoveryTransactions(active, store=store, fault_hook=fault)
    with pytest.raises(OSError, match="synthetic open failure"):
        tx.use_saved(tx.probe_open(target.path))
    assert active.path == old_path
    assert store.snapshot_path(target.path).read_bytes() == before
    assert store.inspect(target.path).status == "VERIFIED"


def test_at_10_external_disk_changes_just_before_restore_replace(tmp_path: Path) -> None:
    s = session(tmp_path)
    assert s.path is not None
    path = s.path
    store = ProvenanceStore()
    snapshot(s, store)
    original = path.read_bytes()
    external = original + b" - external writer"

    def fault(phase: str) -> None:
        if phase == "before_restore_replace":
            path.write_bytes(external)

    tx = RecoveryTransactions(s, store=store, fault_hook=fault)
    with pytest.raises(RecoveryRaceChanged, match="RECOVERY_RACE_CHANGED"):
        tx.restore(tx.probe_open(path))
    assert path.read_bytes() == external
    assert store.snapshot_path(path).is_file()
    assert not list(tmp_path.glob(".*aavc-restore-*.tmp"))
    backups = list(tmp_path.glob("*.pre-recovery.bak"))
    assert len(backups) == 1 and backups[0].read_bytes() == original


def test_at_11_snapshot_changes_just_before_restore_replace(tmp_path: Path) -> None:
    s = session(tmp_path)
    assert s.path is not None
    path = s.path
    store = ProvenanceStore()
    snapshot(s, store)
    before = path.read_bytes()

    def fault(phase: str) -> None:
        if phase == "before_restore_replace":
            store.snapshot_path(path).write_bytes(b"new snapshot from process B")

    tx = RecoveryTransactions(s, store=store, fault_hook=fault)
    with pytest.raises(RecoveryRaceChanged, match="RECOVERY_RACE_CHANGED"):
        tx.restore(tx.probe_open(path))
    assert path.read_bytes() == before
    assert not list(tmp_path.glob(".*aavc-restore-*.tmp"))


def test_at_14_backup_creation_failure_does_not_touch_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    s = session(tmp_path)
    assert s.path is not None
    store = ProvenanceStore()
    snapshot(s, store)
    old = s.path.read_bytes()
    original_open = Path.open

    def fault_open(self: Path, mode: str = "r", *args: object, **kwargs: object):
        if ".pre-recovery" in self.name and mode == "xb":
            raise PermissionError("backup blocked")
        return original_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fault_open)
    tx = RecoveryTransactions(s, store=store)
    with pytest.raises(PermissionError, match="backup blocked"):
        tx.restore(tx.probe_open(s.path))
    assert s.path.read_bytes() == old
    assert store.snapshot_path(s.path).exists()


def test_rcv_11_invalid_candidate_preserved_when_explicit_saved_version_opened(tmp_path: Path) -> None:
    s = session(tmp_path, "target")
    assert s.path is not None
    store = ProvenanceStore()
    store.snapshot_path(s.path).write_bytes(b"corrupt autosave preserve")
    old = store.snapshot_path(s.path).read_bytes()
    active = session(tmp_path, "active")
    tx = RecoveryTransactions(active, store=store)
    plan = tx.probe_open(s.path)
    assert plan.candidate.status == "INVALID"
    loaded = tx.use_saved(plan)
    assert loaded.title == "target"
    assert store.snapshot_path(s.path).read_bytes() == old
    assert active.path == s.path


def test_restore_fault_after_backup_preserves_disk_and_backup(tmp_path: Path) -> None:
    s = session(tmp_path)
    assert s.path is not None
    store = ProvenanceStore()
    snapshot(s, store)
    before = s.path.read_bytes()

    def fault(phase: str) -> None:
        if phase == "after_backup":
            raise OSError("synthetic interrupted after backup")

    tx = RecoveryTransactions(s, store=store, fault_hook=fault)
    with pytest.raises(OSError, match="synthetic interrupted"):
        tx.restore(tx.probe_open(s.path))
    assert s.path.read_bytes() == before
    assert s.path.with_suffix(s.path.suffix + ".pre-recovery.bak").read_bytes() == before
    assert store.snapshot_path(s.path).exists()


def test_at_12_concurrent_restore_one_winner_one_conflict(tmp_path: Path) -> None:
    from threading import Barrier, Thread

    s = session(tmp_path)
    assert s.path is not None
    path = s.path
    store = ProvenanceStore()
    snapshot(s, store)
    tx = RecoveryTransactions(s, store=store)
    plan = tx.probe_open(path)
    barrier = Barrier(3)
    outcomes: list[str] = []

    def worker() -> None:
        barrier.wait()
        try:
            tx.restore(plan)
        except RecoveryRaceChanged:
            outcomes.append("RACE_CHANGED")
        else:
            outcomes.append("SUCCESS")

    threads = [Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()
    assert sorted(outcomes) == ["RACE_CHANGED", "SUCCESS"]
    assert len(list(tmp_path.glob("*.pre-recovery.bak"))) == 1
    assert load_project(path).title == "recovery"


def test_at_19_save_cleanup_failure_reports_committed_disk_and_preserves_quarantine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = session(tmp_path)
    assert s.path is not None
    store = ProvenanceStore()
    snapshot(s, store)
    original = s.path.read_bytes()
    s.execute(SetSceneDuration(1, 8))

    def fail_retire(_held: object) -> None:
        raise PermissionError("injected post-save cleanup failure")

    monkeypatch.setattr(store, "retire_quarantine", fail_retire)
    with pytest.raises(RecoveryCommitPartial, match="SAVE_CLEANUP_PARTIAL"):
        RecoveryTransactions(s, store=store).save()
    assert not s.is_dirty
    assert s.path.read_bytes() != original
    assert not store.snapshot_path(s.path).exists()
    assert len(list(tmp_path.glob(".*.quarantine-*"))) >= 1


def test_at_17_quarantine_rollback_collision_never_overwrites_other_writer(
    tmp_path: Path,
) -> None:
    s = session(tmp_path)
    assert s.path is not None
    store = ProvenanceStore()
    snapshot(s, store)
    before = s.path.read_bytes()

    def fault(phase: str) -> None:
        if phase == "before_disk_adoption":
            store.snapshot_path(s.path).write_bytes(b"other-writer-owned")
            raise OSError("synthetic adoption failed")

    tx = RecoveryTransactions(s, store=store, fault_hook=fault)
    with pytest.raises(RecoveryCommitPartial, match="DISCARD_ROLLBACK_PARTIAL"):
        tx.use_saved(tx.probe_open(s.path))
    assert store.snapshot_path(s.path).read_bytes() == b"other-writer-owned"
    assert s.path.read_bytes() == before
    assert len(list(tmp_path.glob(".*.quarantine-*"))) >= 1
