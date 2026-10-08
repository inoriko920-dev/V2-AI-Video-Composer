"""W06-C / v0.2.2 regression tests: persistence and recovery file safety.

Intentionally landed before production changes to capture FB-03B / FB-03C.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from aavc.application.commands import SetSceneDuration
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.persistence.recovery import RecoveryManager
from aavc.persistence.serializer import load_project, save_project

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="w06c-project",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _put_snapshot(manager: RecoveryManager, path: Path, title: str) -> bytes:
    payload = _project().to_dict()
    payload["title"] = title
    data = json.dumps(payload, sort_keys=True).encode("utf-8")
    manager.recovery_path_for(path).write_bytes(data)
    return data


def _assert_no_owned_temp(path: Path) -> None:
    assert not list(path.parent.glob(f".{path.name}.aavc-save-*.tmp"))
    assert not list(path.parent.glob(f".{path.name}.aavc-restore-*.tmp"))


def test_fb03b_repeated_valid_restore_keeps_all_pre_recovery_versions(tmp_path: Path) -> None:
    path = save_project(_project(), tmp_path / "history.aavcproj")
    manager = RecoveryManager()
    original = path.read_bytes()
    first_snapshot = _put_snapshot(manager, path, "first")
    manager.restore_snapshot(path)

    first_backup = path.with_suffix(path.suffix + ".pre-recovery.bak")
    assert first_backup.read_bytes() == original
    assert path.read_bytes() == first_snapshot

    second_snapshot = _put_snapshot(manager, path, "second")
    manager.restore_snapshot(path)

    second_backup = path.with_suffix(path.suffix + ".pre-recovery.1.bak")
    assert first_backup.read_bytes() == original
    assert second_backup.read_bytes() == first_snapshot
    assert path.read_bytes() == second_snapshot
    assert load_project(path).title == "second"
    _assert_no_owned_temp(path)


def test_recovery_numbering_skips_existing_backups_without_clobber(tmp_path: Path) -> None:
    path = save_project(_project(), tmp_path / "occupied.aavcproj")
    manager = RecoveryManager()
    first = path.with_suffix(path.suffix + ".pre-recovery.bak")
    numbered = path.with_suffix(path.suffix + ".pre-recovery.1.bak")
    first.write_bytes(b"user-owned-first")
    numbered.write_bytes(b"user-owned-second")
    original = path.read_bytes()
    snapshot = _put_snapshot(manager, path, "third")

    manager.restore_snapshot(path)

    assert first.read_bytes() == b"user-owned-first"
    assert numbered.read_bytes() == b"user-owned-second"
    assert path.with_suffix(path.suffix + ".pre-recovery.2.bak").read_bytes() == original
    assert path.read_bytes() == snapshot
    _assert_no_owned_temp(path)


@pytest.mark.parametrize(
    "corrupt",
    [b"{definitely not JSON", b"\xff\xfe", b"[]", b"{}", b'{"schema_version": "four"}'],
)
def test_fb03c_existing_corrupt_target_never_overwritten_by_save(
    tmp_path: Path, corrupt: bytes
) -> None:
    path = tmp_path / "unreadable.aavcproj"
    path.write_bytes(corrupt)
    with pytest.raises(ValueError, match="PROJECT_DESTINATION_UNREADABLE"):
        save_project(_project(), path)
    assert path.read_bytes() == corrupt
    _assert_no_owned_temp(path)


def test_fb03c_failed_save_as_keeps_path_dirty_and_history(tmp_path: Path) -> None:
    original = tmp_path / "original.aavcproj"
    destination = tmp_path / "broken.aavcproj"
    destination.write_bytes(b"{broken")
    session = ProjectSession()
    session.create(_project(), original)
    session.execute(SetSceneDuration(1, 4.5))
    assert session.is_dirty
    before = session.current
    before_path = session.path
    before_undo = session.can_undo
    before_redo = session.can_redo
    before_original = original.read_bytes()

    with pytest.raises(ValueError, match="PROJECT_DESTINATION_UNREADABLE"):
        session.save(destination)

    assert destination.read_bytes() == b"{broken"
    assert original.read_bytes() == before_original
    assert session.path == before_path
    assert session.current == before
    assert session.is_dirty
    assert session.can_undo == before_undo
    assert session.can_redo == before_redo
    _assert_no_owned_temp(destination)


def test_existing_future_schema_preserves_downgrade_error(tmp_path: Path) -> None:
    path = tmp_path / "future.aavcproj"
    payload = _project().to_dict()
    payload["schema_version"] = 5
    raw = json.dumps(payload).encode("utf-8")
    path.write_bytes(raw)

    with pytest.raises(ValueError, match="SCHEMA_DOWNGRADE_BLOCKED"):
        save_project(_project(), path)

    assert path.read_bytes() == raw
    _assert_no_owned_temp(path)


def test_fresh_target_and_autosave_schema_backtracking_remain_allowed(tmp_path: Path) -> None:
    path = tmp_path / "fresh.aavcproj"
    save_project(_project(), path)
    assert load_project(path).title == "w06c-project"
    manager = RecoveryManager()
    snapshot = manager.write_snapshot(_project(), path)
    assert snapshot.recovery_path.is_file()
    _assert_no_owned_temp(path)
    _assert_no_owned_temp(snapshot.recovery_path)


def test_restore_invalid_snapshot_cannot_change_existing_backup(tmp_path: Path) -> None:
    path = save_project(_project(), tmp_path / "invalid-snapshot.aavcproj")
    original = path.read_bytes()
    manager = RecoveryManager()
    first_backup = path.with_suffix(path.suffix + ".pre-recovery.bak")
    first_backup.write_bytes(b"precious")
    manager.recovery_path_for(path).write_bytes(b"{bad")

    with pytest.raises(ValueError):
        manager.restore_snapshot(path)

    assert path.read_bytes() == original
    assert first_backup.read_bytes() == b"precious"
    assert not path.with_suffix(path.suffix + ".pre-recovery.1.bak").exists()
    _assert_no_owned_temp(path)


def test_failed_recovery_replace_preserves_project_snapshot_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = save_project(_project(), tmp_path / "replace-failure.aavcproj")
    manager = RecoveryManager()
    original = path.read_bytes()
    snapshot = _put_snapshot(manager, path, "recover-me")
    original_replace = Path.replace

    def fail_only_project_replace(self: Path, target: Path) -> Path:
        if Path(target) == path:
            raise OSError("injected restore replace failure")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", fail_only_project_replace)
    with pytest.raises(OSError, match="injected restore replace failure"):
        manager.restore_snapshot(path)

    assert path.read_bytes() == original
    assert manager.recovery_path_for(path).read_bytes() == snapshot
    _assert_no_owned_temp(path)



def test_backup_copy_failure_keeps_project_and_cleans_partial_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = save_project(_project(), tmp_path / "backup-copy-failure.aavcproj")
    manager = RecoveryManager()
    original = path.read_bytes()
    recovery_bytes = _put_snapshot(manager, path, "not-restored")
    first_backup = path.with_suffix(path.suffix + ".pre-recovery.bak")
    first_backup.write_bytes(b"older-backup")

    def inject_partial_copy(source, output) -> None:
        output.write(b"incomplete-copy")
        raise OSError("injected backup copy failure")

    monkeypatch.setattr(shutil, "copyfileobj", inject_partial_copy)
    with pytest.raises(OSError, match="injected backup copy failure"):
        manager.restore_snapshot(path)

    assert path.read_bytes() == original
    assert manager.recovery_path_for(path).read_bytes() == recovery_bytes
    assert first_backup.read_bytes() == b"older-backup"
    assert not path.with_suffix(path.suffix + ".pre-recovery.1.bak").exists()
    _assert_no_owned_temp(path)


def test_corrupt_autosave_may_be_replaced_explicitly_without_project_backup(
    tmp_path: Path,
) -> None:
    path = save_project(_project(), tmp_path / "autosave-project.aavcproj")
    original = path.read_bytes()
    manager = RecoveryManager()
    autosave = manager.recovery_path_for(path)
    autosave.write_bytes(b"broken previous snapshot")

    manager.write_snapshot(_project(), path)

    assert manager.load_snapshot(path).title == "w06c-project"
    assert path.read_bytes() == original
    assert not autosave.with_suffix(autosave.suffix + ".pre-schema-v4.bak").exists()
    _assert_no_owned_temp(autosave)
