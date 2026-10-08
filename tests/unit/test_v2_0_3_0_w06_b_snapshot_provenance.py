"""W06-B test-first: real bytes, provenance, crash windows and quarantine.

No Qt, active Save/Open or Restore integration. Tests use only synthetic
ProjectState fixtures and isolated temporary directories.
"""
from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from aavc.domain.project.models import AssetBinding, ProjectState, Scene
from aavc.persistence.serializer import load_project, save_project
from aavc.persistence.snapshot_provenance import (
    ProvenanceStore,
    RecoveryCandidate,
    RecoveryRaceChanged,
)


def project(title: str = "Fixture", *, schema: int = 3) -> ProjectState:
    return ProjectState(
        schema_version=schema,
        title=title,
        source_docx="synthetic.docx",
        asset_directory="synthetic_assets",
        scenes=(Scene(1, ("asset-1",), ("synthetic",), 3.0),),
        bindings=(AssetBinding("asset-1", "synthetic", None, "MISSING"),),
        metadata={"fixture": "W06-B", **({"animation_keyframe_contract": "advanced-v1"} if schema == 4 else {})},
    )


def baseline(tmp_path: Path, *, schema: int = 3) -> tuple[Path, str]:
    path = save_project(project(schema=schema), tmp_path / "proyek.aavcproj")
    return path, sha256(path.read_bytes()).hexdigest()


def capture(store: ProvenanceStore, path: Path, digest: str, title: str = "Edited") -> RecoveryCandidate:
    return store.write_snapshot(replace(project(), title=title), path, saved_baseline_sha256=digest)


def test_at_01_rcv_11_reject_stale_baseline_without_any_disk_mutation(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    before = path.read_bytes()
    with pytest.raises(RecoveryRaceChanged, match="BASELINE_CHANGED"):
        ProvenanceStore().write_snapshot(project("edited"), path, saved_baseline_sha256="0" * 64)
    assert path.read_bytes() == before
    assert not list(tmp_path.glob("*.autosave*"))


def test_at_02_temp_snapshot_partial_write_keeps_existing_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, h, "old")
    before = store.snapshot_path(path).read_bytes()
    monkeypatch.setattr(store, "_publish_snapshot", lambda *args: (_ for _ in ()).throw(OSError("write failed")))
    with pytest.raises(OSError, match="write failed"):
        capture(store, path, h, "new")
    assert store.snapshot_path(path).read_bytes() == before
    assert store.inspect(path).status == "VERIFIED"
    assert path.read_bytes() == save_project(project(), tmp_path / "check.aavcproj").read_bytes()


def test_at_03_snapshot_before_metadata_crash_is_uncertain(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    ok = ProvenanceStore()
    capture(ok, path, h, "first")
    first_meta = ok.metadata_path(path).read_bytes()

    def fault(phase: str) -> None:
        if phase == "after_snapshot":
            raise OSError("injected crash before sidecar")

    with pytest.raises(OSError, match="injected crash"):
        capture(ProvenanceStore(fault_hook=fault), path, h, "second")
    assert ok.metadata_path(path).read_bytes() == first_meta
    assert ok.inspect(path).status == "UNCERTAIN"
    assert load_project(ok.snapshot_path(path)).title == "second"


def test_at_04_metadata_publish_failure_keeps_previous_metadata(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, h, "first")
    old_meta = store.metadata_path(path).read_bytes()

    def fault(phase: str) -> None:
        if phase == "before_meta_replace":
            raise PermissionError("injected meta replace")

    with pytest.raises(PermissionError):
        capture(ProvenanceStore(fault_hook=fault), path, h, "second")
    assert store.metadata_path(path).read_bytes() == old_meta
    assert store.inspect(path).status == "UNCERTAIN"
    assert not list(tmp_path.glob(".*aavc-meta-*.tmp"))


def test_at_05_rcv_20_external_disk_change_yields_conflict(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, h)
    path.write_bytes(save_project(project("external"), tmp_path / "other.aavcproj").read_bytes())
    assert store.inspect(path).status == "UNCERTAIN"
    assert store.inspect(path).reason == "BASELINE_CHANGED"


@pytest.mark.parametrize("value", [
    b"x" * 16385,
    b'{"format_version": 2}',
    b'{"format_version": true}',
    b'{"format_version": 1, "snapshot_sha256": 17}',
    b"{not json",
])
def test_at_06_malformed_oversize_unknown_descriptor_never_verified(tmp_path: Path, value: bytes) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, h)
    store.metadata_path(path).write_bytes(value)
    assert store.inspect(path).status == "UNCERTAIN"
    assert store.metadata_path(path).read_bytes() == value


@pytest.mark.parametrize("kind", ["corrupt", "future"])
def test_at_07_rcv_11_reject_corrupt_and_future_snapshot(tmp_path: Path, kind: str) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, h)
    snap = store.snapshot_path(path)
    if kind == "corrupt":
        snap.write_bytes(b"not-json")
    else:
        payload = json.loads(snap.read_text("utf-8"))
        payload["schema_version"] = 99
        snap.write_text(json.dumps(payload), encoding="utf-8")
    disk = path.read_bytes()
    assert store.inspect(path).status == "INVALID"
    assert path.read_bytes() == disk
    assert snap.is_file()


def test_at_08_rcv_18_legacy_snapshot_without_descriptor_is_uncertain(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, h)
    store.metadata_path(path).unlink()
    assert store.inspect(path).status == "UNCERTAIN"
    assert store.snapshot_path(path).is_file()


def test_at_09_symlink_project_rejected_without_touching_target(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    alias = tmp_path / "alias.aavcproj"
    try:
        alias.symlink_to(path)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="PATH_ALIAS_UNSAFE"):
        ProvenanceStore().write_snapshot(project("new"), alias, saved_baseline_sha256=h)
    assert before == path.read_bytes()
    assert not (tmp_path / "alias.aavcproj.autosave").exists()


@pytest.mark.parametrize("which", ["disk", "snapshot"])
def test_at_10_11_rcv_17_recheck_denies_changed_bytes(tmp_path: Path, which: str) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, h)
    inspection = store.inspect(path)
    assert inspection.status == "VERIFIED"
    if which == "disk":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        store.snapshot_path(path).write_bytes(store.snapshot_path(path).read_bytes() + b" ")
    with pytest.raises(RecoveryRaceChanged, match="RECOVERY_RACE_CHANGED"):
        store.revalidate(path, inspection)


def test_at_12_exclusive_quarantine_stage_and_rollback(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, h)
    before = store.snapshot_path(path).read_bytes()
    inspection = store.inspect(path)
    held = store.quarantine_candidate(path, inspection)
    assert not store.snapshot_path(path).exists()
    assert held.snapshot_copy.read_bytes() == before
    assert held.metadata_copy.is_file()
    with pytest.raises(RecoveryRaceChanged):
        store.quarantine_candidate(path, inspection)
    store.rollback_quarantine(held)
    assert store.snapshot_path(path).read_bytes() == before
    assert store.inspect(path).status == "VERIFIED"


def test_quarantine_never_overwrites_new_candidate_during_rollback(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, h)
    held = store.quarantine_candidate(path, store.inspect(path))
    store.snapshot_path(path).write_bytes(b"other-process")
    with pytest.raises(RecoveryRaceChanged, match="QUARANTINE_COLLISION"):
        store.rollback_quarantine(held)
    assert store.snapshot_path(path).read_bytes() == b"other-process"
    assert held.snapshot_copy.is_file()


def test_quarantine_partial_rename_failure_rolls_back_first_file(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    s = ProvenanceStore()
    capture(s, path, h)
    before=s.snapshot_path(path).read_bytes()
    def fault(phase: str) -> None:
        if phase == "after_quarantine_snapshot":
            raise OSError("cannot move metadata")
    with pytest.raises(OSError):
        ProvenanceStore(fault_hook=fault).quarantine_candidate(path, s.inspect(path))
    assert s.snapshot_path(path).read_bytes() == before
    assert s.metadata_path(path).exists()


def test_preserves_schema_v4_and_does_not_write_secrets_in_descriptor(tmp_path: Path) -> None:
    path, h = baseline(tmp_path, schema=4)
    store = ProvenanceStore()
    payload = replace(project(schema=4), title="v4")
    store.write_snapshot(payload, path, saved_baseline_sha256=h)
    assert load_project(store.snapshot_path(path)).schema_version == 4
    descriptor = store.metadata_path(path).read_text("utf-8")
    assert "synthetic.docx" not in descriptor
    assert str(path) not in descriptor
    assert "Fixture" not in descriptor
    assert store.inspect(path).status == "VERIFIED"


def test_rcv_14_rejects_secret_canary_without_leaking_to_sidecar(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    secret = "AIza" + "A" * 35
    bad = replace(project("Sensitive"), metadata={"api_key": secret})
    with pytest.raises(ValueError, match="SENSITIVE_PROJECT_FIELD"):
        ProvenanceStore().write_snapshot(bad, path, saved_baseline_sha256=h)
    assert not list(tmp_path.glob("*.autosave*"))
    assert secret.encode() not in path.read_bytes()


def test_snapshot_writer_rechecks_disk_before_publishing_descriptor(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    old = path.read_bytes()
    def fault(phase: str) -> None:
        if phase == "after_snapshot":
            path.write_bytes(old + b" ")
    store = ProvenanceStore(fault_hook=fault)
    with pytest.raises(RecoveryRaceChanged, match="BASELINE_CHANGED"):
        capture(store, path, h)
    assert store.inspect(path).status != "VERIFIED"


def test_write_cannot_replace_existing_symlink_snapshot(tmp_path: Path) -> None:
    path, h = baseline(tmp_path)
    store = ProvenanceStore()
    target = tmp_path / "foreign.txt"
    target.write_text("untouched", encoding="utf-8")
    try:
        store.snapshot_path(path).symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError, match="PATH_ALIAS_UNSAFE"):
        capture(store, path, h)
    assert target.read_text("utf-8") == "untouched"


def test_revalidate_rejects_mutated_but_well_formed_metadata(tmp_path: Path) -> None:
    path, digest = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, digest)
    original = store.inspect(path)
    assert original.status == "VERIFIED" and original.metadata_sha256 is not None
    data = json.loads(store.metadata_path(path).read_text("utf-8"))
    data["write_generation"] = "f" * 32
    store.metadata_path(path).write_text(json.dumps(data), encoding="utf-8")
    assert store.inspect(path).status == "VERIFIED"
    with pytest.raises(RecoveryRaceChanged, match="RECOVERY_RACE_CHANGED"):
        store.revalidate(path, original)
    with pytest.raises(RecoveryRaceChanged):
        store.quarantine_candidate(path, original)


def test_descriptor_not_published_when_snapshot_rejected(tmp_path: Path) -> None:
    path, digest = baseline(tmp_path)
    store = ProvenanceStore()
    capture(store, path, digest)
    before = store.metadata_path(path).read_bytes()
    path.write_bytes(path.read_bytes() + b" changed")
    with pytest.raises(RecoveryRaceChanged, match="BASELINE_CHANGED"):
        capture(store, path, digest, "changed")
    assert store.metadata_path(path).read_bytes() == before
