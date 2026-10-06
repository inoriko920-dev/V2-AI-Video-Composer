import json
from pathlib import Path

import pytest

from aavc.application.commands import SetSceneDuration
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.persistence.recovery import RecoveryManager
from aavc.persistence.serializer import loads_project, save_project

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="astra-validation",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


@pytest.mark.parametrize("payload", ["[]", "null", "42", '"text"'])
def test_non_object_project_root_is_rejected(payload: str) -> None:
    with pytest.raises(ValueError, match="root harus berupa object JSON"):
        loads_project(payload)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            lambda data: data["scenes"][0].update(
                {"asset_ids": [], "source_quotes": []}
            ),
            "tepat 1 atau 2 aset",
        ),
        (
            lambda data: data["scenes"][0].update(
                {
                    "asset_ids": ["A001", "A002", "A003"],
                    "source_quotes": ["a", "b", "c"],
                }
            ),
            "tepat 1 atau 2 aset",
        ),
        (
            lambda data: data.update(
                {"scenes": (*data["scenes"], dict(data["scenes"][0]))}
            ),
            "scene_number harus unik",
        ),
        (
            lambda data: data["scenes"][0].update({"duration_seconds": -1}),
            "lebih besar dari 0",
        ),
        (
            lambda data: data["scenes"][0].update({"duration_seconds": float("nan")}),
            "harus finite",
        ),
        (
            lambda data: data["scenes"][0].update({"duration_seconds": float("inf")}),
            "harus finite",
        ),
        (
            lambda data: data.update({"fps": 0}),
            "fps harus lebih besar dari 0",
        ),
        (
            lambda data: data.update({"subtitle_style": []}),
            "subtitle_style harus berupa object JSON",
        ),
    ],
)
def test_structurally_invalid_project_payload_is_rejected(mutate, expected: str) -> None:
    payload = _project().to_dict()
    mutate(payload)

    with pytest.raises(ValueError, match=expected):
        loads_project(json.dumps(payload))


def test_missing_media_path_remains_loadable_for_relink() -> None:
    payload = _project().to_dict()
    payload["bindings"][0]["path"] = "Z:/moved/missing-file.png"
    payload["bindings"][0]["status"] = "MISSING"

    restored = loads_project(json.dumps(payload))

    assert restored.bindings[0].status == "MISSING"
    assert restored.bindings[0].path == "Z:/moved/missing-file.png"


def test_failed_structural_open_preserves_session_path_dirty_and_history(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "good.aavcproj"
    session = ProjectSession()
    session.create(_project(), destination)
    session.execute(SetSceneDuration(1, 4.5))
    session.undo()

    before_current = session.current
    before_path = session.path
    before_dirty = session.is_dirty
    before_can_undo = session.can_undo
    before_can_redo = session.can_redo

    invalid = before_current.to_dict()
    invalid["scenes"][0]["asset_ids"] = []
    invalid["scenes"][0]["source_quotes"] = []
    broken = tmp_path / "invalid.aavcproj"
    broken.write_text(json.dumps(invalid), encoding="utf-8")

    with pytest.raises(ValueError, match="tepat 1 atau 2 aset"):
        session.open(broken)

    assert session.current == before_current
    assert session.path == before_path
    assert session.is_dirty == before_dirty
    assert session.can_undo == before_can_undo
    assert session.can_redo == before_can_redo


def test_failed_structural_recovery_preserves_project_backup_and_temp(
    tmp_path: Path,
) -> None:
    project = _project()
    project_path = save_project(project, tmp_path / "demo.aavcproj")
    original_bytes = project_path.read_bytes()
    manager = RecoveryManager()

    backup = project_path.with_suffix(project_path.suffix + ".pre-recovery.bak")
    backup.write_bytes(b"existing-backup")

    invalid = project.to_dict()
    invalid["scenes"][0]["asset_ids"] = []
    invalid["scenes"][0]["source_quotes"] = []
    manager.recovery_path_for(project_path).write_text(
        json.dumps(invalid),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="tepat 1 atau 2 aset"):
        manager.restore_snapshot(project_path)

    assert project_path.read_bytes() == original_bytes
    assert backup.read_bytes() == b"existing-backup"
    assert list(tmp_path.glob(".*.aavc-restore-*.tmp")) == []
