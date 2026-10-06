from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment
from aavc.persistence.migrations import migrate_project_payload
from aavc.persistence.serializer import (
    CURRENT_SCHEMA_VERSION,
    dumps_project,
    loads_project,
    migration_backup_path,
    save_project,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="wave-d-migration",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_v1_to_v3_migration_is_deterministic_and_non_mutating() -> None:
    payload = _project().to_dict()
    payload["schema_version"] = 1
    for key in [
        "animations",
        "subtitle_style",
        "subtitle_animation",
        "render_quality",
        "metadata",
    ]:
        payload.pop(key, None)
    original = json.loads(json.dumps(payload))

    first = migrate_project_payload(
        payload,
        source_version=1,
        target_version=CURRENT_SCHEMA_VERSION,
    )
    second = migrate_project_payload(
        payload,
        source_version=1,
        target_version=CURRENT_SCHEMA_VERSION,
    )

    assert payload == original
    assert first == second
    assert first["schema_version"] == 3
    assert first["animations"] == []


def test_v2_assignment_migrates_with_empty_keyframe_tracks() -> None:
    project = _project()
    scene = project.scenes[0]
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        enter_effect="Rise",
        exit_effect="Drift",
        intensity=0.75,
        locked=True,
    )
    payload = replace(project, animations=(assignment,)).to_dict()
    payload["schema_version"] = 2
    payload["animations"][0].pop("keyframe_tracks", None)

    restored = loads_project(json.dumps(payload))

    assert restored.schema_version == 3
    assert restored.animations[0].enter_effect == "Rise"
    assert restored.animations[0].exit_effect == "Drift"
    assert restored.animations[0].intensity == 0.75
    assert restored.animations[0].locked is True
    assert restored.animations[0].keyframe_tracks == ()


def test_schema_v3_keyframe_roundtrip() -> None:
    project = _project()
    scene = project.scenes[0]
    assignment = AnimationAssignment(
        scene_number=scene.scene_number,
        asset_id=scene.asset_ids[0],
        enter_effect="Fade",
        exit_effect="Fade",
        keyframe_tracks=(
            AnimationKeyframeTrack(
                property_name="opacity",
                keyframes=(
                    AnimationKeyframe(
                        time=0.0,
                        value=0.0,
                        interpolation="bezier",
                        easing="ease_in",
                        velocity=0.25,
                        overshoot=0.1,
                    ),
                    AnimationKeyframe(
                        time=1.0,
                        value=1.0,
                        easing="ease_out",
                    ),
                ),
            ),
        ),
    )
    state = replace(project, animations=(assignment,))

    restored = loads_project(dumps_project(state))

    assert restored.schema_version == 3
    assert restored.animations == state.animations


def test_first_save_over_legacy_schema_preserves_pre_migration_backup(
    tmp_path: Path,
) -> None:
    project = _project()
    destination = tmp_path / "legacy.aavcproj"
    legacy = project.to_dict()
    legacy["schema_version"] = 2
    destination.write_text(json.dumps(legacy), encoding="utf-8")
    original = destination.read_bytes()

    save_project(project, destination)

    backup = migration_backup_path(destination)
    assert backup.read_bytes() == original
    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 3


def test_existing_migration_backup_is_never_clobbered(tmp_path: Path) -> None:
    project = _project()
    destination = tmp_path / "legacy.aavcproj"
    legacy = project.to_dict()
    legacy["schema_version"] = 2
    destination.write_text(json.dumps(legacy), encoding="utf-8")

    backup = migration_backup_path(destination)
    backup.write_bytes(b"keep-original-backup")

    save_project(project, destination)

    assert backup.read_bytes() == b"keep-original-backup"
