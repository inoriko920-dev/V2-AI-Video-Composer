"""W06-E final acceptance: byte-preserving equivalent candidate and frozen Qt UX.

All files in tmp_path; no user footage, tokens, network, or modified stable tag.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from aavc.application.services.project_session import ProjectSession
from aavc.application.services.recovery_transactions import (
    RecoveryRaceChanged,
    RecoveryTransactions,
)
from aavc.domain.project.models import AssetBinding, ProjectState, Scene
from aavc.persistence.serializer import load_project, save_project
from aavc.persistence.snapshot_provenance import ProvenanceStore


def fixture(*, schema: int = 3, title: str = "Proyek Uji") -> ProjectState:
    metadata = {"fixture": "W06-E"}
    if schema == 4:
        metadata["animation_keyframe_contract"] = "advanced-v1"
    return ProjectState(
        schema_version=schema, title=title,
        source_docx="sample.docx", asset_directory="sample-assets",
        scenes=(Scene(1, ("asset-1",), ("synthetic",), 3.0),),
        bindings=(AssetBinding("asset-1", "synthetic", None, "MISSING"),),
        metadata=metadata,
    )


def restore_fixture(folder: Path, *, schema: int = 3) -> tuple[Path, ProvenanceStore]:
    path = save_project(fixture(schema=schema), folder / "dokumen proyek.aavcproj")
    store = ProvenanceStore()
    edited = replace(fixture(schema=schema, title="Proyek Dipulihkan"),
                     scenes=(Scene(1, ("asset-1",), ("synthetic",), 4.0),))
    store.write_snapshot(edited, path, saved_baseline_sha256=sha256(path.read_bytes()).hexdigest())
    return path, store


@pytest.mark.parametrize("schema", [3, 4])
def test_comp_01_02_reopen_after_restore_no_false_recovery_prompt(
    tmp_path: Path, schema: int,
) -> None:
    path, store = restore_fixture(tmp_path, schema=schema)
    s = ProjectSession()
    s.create(fixture(), tmp_path / "active.aavcproj")
    tx = RecoveryTransactions(s, store=store)
    plan = tx.probe_open(path)
    assert plan.candidate.status == "VERIFIED"
    result = tx.restore(plan)
    assert result.backup_path.is_file()
    disk_sha = sha256(path.read_bytes()).hexdigest()
    assert store.inspect(path).status == "UNCERTAIN"  # historical descriptor remains
    second = tx.probe_open(path)
    assert second.equivalent_snapshot is True
    assert second.candidate.snapshot_sha256 == disk_sha
    before = (path.read_bytes(), store.snapshot_path(path).read_bytes(),
              store.metadata_path(path).read_bytes())
    reloaded = tx.open_identical_saved(second)
    assert reloaded.title == "Proyek Dipulihkan"
    assert s.path == path.resolve() and not s.is_dirty
    assert before == (path.read_bytes(), store.snapshot_path(path).read_bytes(),
                      store.metadata_path(path).read_bytes())
    assert sha256(result.backup_path.read_bytes()).hexdigest() != disk_sha


def test_comp_03_equal_content_does_not_skip_corrupt_candidate(tmp_path: Path) -> None:
    path, store = restore_fixture(tmp_path)
    snap = store.snapshot_path(path)
    snap.write_bytes(b"corrupt-json")
    session = ProjectSession()
    tx = RecoveryTransactions(session, store=store)
    plan = tx.probe_open(path)
    assert plan.candidate.status == "INVALID"
    assert plan.equivalent_snapshot is False
    with pytest.raises(RecoveryRaceChanged):
        tx.open_identical_saved(plan)
    assert snap.read_bytes() == b"corrupt-json"


def test_comp_04_equal_content_preflight_rejects_external_change(tmp_path: Path) -> None:
    path, store = restore_fixture(tmp_path)
    active = ProjectSession()
    tx = RecoveryTransactions(active, store=store)
    tx.restore(tx.probe_open(path))
    repeat = tx.probe_open(path)
    assert repeat.equivalent_snapshot
    path.write_bytes(path.read_bytes() + b"changed externally")
    with pytest.raises(RecoveryRaceChanged, match="RECOVERY_RACE_CHANGED"):
        tx.open_identical_saved(repeat)


def test_comp_05_unicode_spaced_path_sha_roundtrip(tmp_path: Path) -> None:
    folder = tmp_path / "Proyek 'Bojonegoro' 你好"
    folder.mkdir()
    path, store = restore_fixture(folder, schema=4)
    assert store.inspect(path).status == "VERIFIED"
    s = ProjectSession()
    tx = RecoveryTransactions(s, store=store)
    tx.restore(tx.probe_open(path))
    again = tx.probe_open(path)
    assert again.equivalent_snapshot
    tx.open_identical_saved(again)
    assert load_project(path).schema_version == 4
    assert store.snapshot_path(path).exists()


def test_comp_06_corrupt_descriptor_cannot_be_mistaken_for_verified(
    tmp_path: Path,
) -> None:
    path, store = restore_fixture(tmp_path)
    store.metadata_path(path).write_bytes(b"bad descriptor")
    plan = RecoveryTransactions(ProjectSession(), store=store).probe_open(path)
    assert plan.candidate.status == "UNCERTAIN"
    assert not plan.equivalent_snapshot


def test_comp_07_worker_never_reads_gui_session_from_worker_thread() -> None:
    """Protect against Qt/main-session access on the worker IO thread."""
    import ast
    import inspect

    from aavc.presentation.windows.recovery_main_window import RecoveryMainWindow

    source = inspect.getsource(RecoveryMainWindow._write_snapshot_task)
    tree = ast.parse(source.lstrip() if not source.startswith("    ") else
                     __import__("textwrap").dedent(source))
    forbidden = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr in ("project_session", "_recovery_coordinator")
    ]
    assert forbidden == [], "Worker may only use captured immutable token and ProvenanceStore"


def test_comp_08_qt_repeat_open_no_recovery_modal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QFileDialog

    from aavc.bootstrap.composition_root import build_foundation_services
    from aavc.presentation.windows.recovery_main_window import RecoveryMainWindow

    app = QApplication.instance() or QApplication([])
    path, store = restore_fixture(tmp_path)
    tx = RecoveryTransactions(ProjectSession(), store=store)
    tx.restore(tx.probe_open(path))
    preserved = (
        path.read_bytes(),
        store.snapshot_path(path).read_bytes(),
        store.metadata_path(path).read_bytes(),
    )
    services = build_foundation_services()
    window = RecoveryMainWindow(services)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(path), ""))
    def forbidden_dialog(*_args: object) -> None:
        raise AssertionError("Should not prompt to recover identical persisted data")
    monkeypatch.setattr(
        "aavc.presentation.windows.recovery_main_window.choose_recovery", forbidden_dialog
    )
    window.open_project()
    assert services.project_session.current is not None
    assert services.project_session.current.title == "Proyek Dipulihkan"
    assert not services.project_session.is_dirty
    assert (
        path.read_bytes(),
        store.snapshot_path(path).read_bytes(),
        store.metadata_path(path).read_bytes(),
    ) == preserved
    window.shutdown_recovery()
    window.window.deleteLater()
    services.jobs.shutdown(wait=False)
    assert app is not None


def test_comp_09_rollback_token_after_two_file_crash_fail_closed(tmp_path: Path) -> None:
    path, store = restore_fixture(tmp_path)
    before = path.read_bytes()
    def fault(phase: str) -> None:
        if phase == "after_snapshot":
            raise OSError("simulated sudden process loss between two files")
    with pytest.raises(OSError, match="simulated sudden"):
        ProvenanceStore(fault_hook=fault).write_snapshot(
            replace(fixture(), title="newer edit"),
            path, saved_baseline_sha256=sha256(before).hexdigest()
        )
    assert path.read_bytes() == before
    classification = store.inspect(path)
    assert classification.status == "UNCERTAIN"
    plan = RecoveryTransactions(ProjectSession(), store=store).probe_open(path)
    assert plan.candidate.status == "UNCERTAIN"
    assert not plan.equivalent_snapshot


def test_comp_10_no_secret_material_in_sidecar(tmp_path: Path) -> None:
    path, store = restore_fixture(tmp_path)
    raw = store.metadata_path(path).read_bytes()
    assert b"Proyek Uji" not in raw
    assert b"sample.docx" not in raw
    assert b"AIza" not in raw
    assert str(path).encode() not in raw
    assert b"saved_baseline_sha256" in raw
