from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from aavc.animation.contract import (
    ADVANCED_KEYFRAME_CONTRACT,
    ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY,
    ADVANCED_SCHEMA_VERSION,
    LEGACY_SCHEMA_VERSION,
    dormant_advanced_track_locations,
    validate_project_animation_contract,
)
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment
from aavc.persistence.recovery import RecoveryManager
from aavc.persistence.serializer import (
    dumps_project,
    loads_project,
    migration_backup_path,
    save_project,
)
from aavc.rendering import build_render_plan, validate_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="v0.2.1-contract",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _opacity_track() -> AnimationKeyframeTrack:
    return AnimationKeyframeTrack(
        property_name="opacity",
        keyframes=(
            AnimationKeyframe(time=0.0, value=0.0),
            AnimationKeyframe(time=1.0, value=1.0),
        ),
    )


def _with_opacity_track(project):
    scene = project.scenes[0]
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
        keyframe_tracks=(_opacity_track(),),
    )
    return replace(project, animations=(assignment,))


def _promote(project):
    metadata = dict(project.metadata)
    metadata[ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY] = ADVANCED_KEYFRAME_CONTRACT
    return replace(
        project,
        schema_version=ADVANCED_SCHEMA_VERSION,
        metadata=metadata,
    )


def test_new_project_remains_legacy_v3_without_advanced_marker() -> None:
    project = _project()

    assert project.schema_version == LEGACY_SCHEMA_VERSION
    assert ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY not in project.metadata
    assert validate_project_animation_contract(project) == "legacy-v3"


def test_schema_v4_advanced_contract_roundtrips_without_auto_migration() -> None:
    project = _promote(_with_opacity_track(_project()))

    restored = loads_project(dumps_project(project))

    assert restored.schema_version == ADVANCED_SCHEMA_VERSION
    assert (
        restored.metadata[ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY]
        == ADVANCED_KEYFRAME_CONTRACT
    )
    assert validate_project_animation_contract(restored) == "advanced-v1"
    assert restored.animations == project.animations


@pytest.mark.parametrize(
    ("schema_version", "marker", "expected"),
    [
        (3, ADVANCED_KEYFRAME_CONTRACT, "ADVANCED_CONTRACT_SCHEMA_MISMATCH"),
        (4, None, "ADVANCED_CONTRACT_INVALID"),
        (4, "advanced-v2", "ADVANCED_CONTRACT_INVALID"),
    ],
)
def test_schema_marker_mismatch_is_rejected(
    schema_version: int,
    marker: str | None,
    expected: str,
) -> None:
    project = _project()
    payload = project.to_dict()
    payload["schema_version"] = schema_version
    metadata = dict(payload["metadata"])
    if marker is None:
        metadata.pop(ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY, None)
    else:
        metadata[ADVANCED_KEYFRAME_CONTRACT_METADATA_KEY] = marker
    payload["metadata"] = metadata

    with pytest.raises(ValueError, match=expected):
        loads_project(json.dumps(payload))


def test_future_schema_is_rejected_against_max_readable_v4() -> None:
    payload = _project().to_dict()
    payload["schema_version"] = 5

    with pytest.raises(ValueError, match="schema 5 lebih baru"):
        loads_project(json.dumps(payload))


def test_legacy_v3_preserves_advanced_track_as_dormant() -> None:
    project = _with_opacity_track(_project())

    restored = loads_project(dumps_project(project))

    assert restored.schema_version == LEGACY_SCHEMA_VERSION
    assert dormant_advanced_track_locations(restored) == (
        (
            restored.scenes[0].scene_number,
            restored.scenes[0].asset_ids[0],
            "opacity",
        ),
    )


def test_render_plan_propagates_resolved_contract(tmp_path: Path) -> None:
    legacy = _project()
    advanced = _promote(_with_opacity_track(legacy))

    legacy_plan = build_render_plan(legacy, tmp_path / "legacy.mp4")
    advanced_plan = build_render_plan(advanced, tmp_path / "advanced.mp4")

    assert legacy_plan.project_schema_version == 3
    assert legacy_plan.animation_keyframe_contract == "legacy-v3"
    assert advanced_plan.project_schema_version == 4
    assert advanced_plan.animation_keyframe_contract == "advanced-v1"


def test_preflight_keeps_v3_opacity_dormant_and_activates_it_only_in_v4(
    tmp_path: Path,
) -> None:
    legacy = _with_opacity_track(_project())
    advanced = _promote(legacy)

    legacy_report = validate_render_plan(build_render_plan(legacy, tmp_path / "legacy.mp4"))
    advanced_report = validate_render_plan(
        build_render_plan(advanced, tmp_path / "advanced.mp4")
    )

    assert any(issue.code == "ADVANCED_TRACK_DORMANT" for issue in legacy_report.issues)
    assert legacy_report.ok
    assert not any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in advanced_report.issues
    )
    assert advanced_report.ok


def test_active_v4_accepts_k6_bezier_interpolation(
    tmp_path: Path,
) -> None:
    project = _project()
    scene = project.scenes[0]
    bezier_track = AnimationKeyframeTrack(
        property_name="mask_progress",
        keyframes=(
            AnimationKeyframe(
                time=0.0,
                value=0.0,
                interpolation="bezier",
            ),
            AnimationKeyframe(time=1.0, value=1.0),
        ),
    )
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        intensity=0.0,
        keyframe_tracks=(bezier_track,),
    )
    advanced = _promote(replace(project, animations=(assignment,)))

    report = validate_render_plan(
        build_render_plan(advanced, tmp_path / "advanced-mask-bezier.mp4")
    )

    assert not any(
        issue.code == "ADVANCED_BACKEND_UNAVAILABLE"
        for issue in report.issues
    )
    assert report.ok


def test_first_v3_to_v4_overwrite_creates_non_clobbering_backup(
    tmp_path: Path,
) -> None:
    destination = save_project(_project(), tmp_path / "demo.aavcproj")
    original = destination.read_bytes()
    advanced = _promote(_with_opacity_track(_project()))

    save_project(advanced, destination)

    backup = migration_backup_path(destination, target_version=4)
    assert backup.read_bytes() == original

    backup.write_bytes(b"keep-first-backup")
    save_project(advanced, destination)
    assert backup.read_bytes() == b"keep-first-backup"


def test_normal_save_cannot_downgrade_existing_v4_file(tmp_path: Path) -> None:
    destination = tmp_path / "demo.aavcproj"
    advanced = _promote(_with_opacity_track(_project()))
    save_project(advanced, destination)
    original = destination.read_bytes()

    with pytest.raises(ValueError, match="SCHEMA_DOWNGRADE_BLOCKED"):
        save_project(_project(), destination)

    assert destination.read_bytes() == original


def test_autosave_can_follow_undo_across_v4_to_v3_without_schema_backup(
    tmp_path: Path,
) -> None:
    project_path = tmp_path / "demo.aavcproj"
    manager = RecoveryManager()
    advanced = _promote(_with_opacity_track(_project()))

    manager.write_snapshot(advanced, project_path)
    manager.write_snapshot(_project(), project_path)

    autosave = manager.recovery_path_for(project_path)
    restored = loads_project(autosave.read_text(encoding="utf-8"))
    assert restored.schema_version == 3
    assert not autosave.with_suffix(autosave.suffix + ".pre-schema-v4.bak").exists()
