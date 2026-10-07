from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from aavc.application.services.validation import validate_project
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="wave-f-validation",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_validation_detects_missing_optional_media_only_when_configured(
    tmp_path: Path,
) -> None:
    project = _project()
    assert not any(
        issue.code in {"NARRATION_NOT_FOUND", "SUBTITLE_NOT_FOUND"}
        for issue in validate_project(project)
    )

    configured = replace(
        project,
        narration_audio=str(tmp_path / "missing.mp3"),
        subtitle_source=str(tmp_path / "missing.srt"),
    )
    codes = {issue.code for issue in validate_project(configured)}

    assert "NARRATION_NOT_FOUND" in codes
    assert "SUBTITLE_NOT_FOUND" in codes


def test_validation_surfaces_wave_e_keyframe_fallback() -> None:
    project = _project()
    scene = project.scenes[0]
    track = AnimationKeyframeTrack(
        property_name="opacity",
        keyframes=(
            AnimationKeyframe(time=0.0, value=0.0),
            AnimationKeyframe(time=1.0, value=1.0),
        ),
    )
    assignment = AnimationAssignment(
        scene.scene_number,
        scene.asset_ids[0],
        intensity=0.0,
        keyframe_tracks=(track,),
    )
    project = replace(project, animations=(assignment,))

    issues = validate_project(project)
    fallback = next(
        issue for issue in issues if issue.code == "ADVANCED_TRACK_DORMANT"
    )

    assert fallback.scene_number == scene.scene_number
    assert fallback.asset_id == scene.asset_ids[0]
    assert "opacity" in fallback.message


def test_ready_binding_with_missing_file_is_reported(tmp_path: Path) -> None:
    project = _project()
    first = project.bindings[0]
    missing = replace(
        first,
        path=str(tmp_path / "gone.png"),
        status="READY",
    )
    project = replace(project, bindings=(missing, *project.bindings[1:]))

    issues = validate_project(project)

    assert any(
        issue.code == "ASSET_NOT_READY" and issue.asset_id == first.asset_id
        for issue in issues
    )
