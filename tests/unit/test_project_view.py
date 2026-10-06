from dataclasses import replace
from pathlib import Path

from aavc.application.services.vertical_slice import create_project_state
from aavc.presentation.project_view import (
    build_asset_views,
    build_project_summary,
    build_scene_views,
    format_duration,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="overview-live",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_project_summary_comes_from_project_state() -> None:
    project = replace(
        _project(),
        width=2560,
        height=1440,
        fps=60,
        narration_audio="C:/media/voice.wav",
        subtitle_source="C:/media/caption.srt",
    )

    summary = build_project_summary(project)

    assert summary.title == "overview-live"
    assert summary.resolution == "2560 × 1440"
    assert summary.fps == 60
    assert summary.scene_count == len(project.scenes)
    assert summary.ready_count == len(project.bindings)
    assert summary.not_ready_count == 0
    assert summary.narration_label == "voice.wav"
    assert summary.subtitle_label == "caption.srt"


def test_scene_and_asset_views_keep_canonical_project_data() -> None:
    project = _project()

    scenes = build_scene_views(project)
    assets = build_asset_views(project)

    assert scenes[0].scene_number == project.scenes[0].scene_number
    assert scenes[0].mode == project.scenes[0].mode
    assert scenes[0].asset_ids == project.scenes[0].asset_ids
    assert assets[0].asset_id == project.bindings[0].asset_id
    assert assets[0].status == "READY"
    assert assets[0].file_label == Path(project.bindings[0].path or "").name


def test_missing_asset_is_visible_in_summary_and_asset_view() -> None:
    project = _project()
    first = project.bindings[0]
    broken = replace(first, path=None, status="MISSING")
    project = replace(project, bindings=(broken, *project.bindings[1:]))

    summary = build_project_summary(project)
    assets = build_asset_views(project)

    assert summary.not_ready_count == 1
    assert assets[0].status == "MISSING"
    assert assets[0].file_label == "File belum ditemukan"


def test_format_duration_keeps_fraction_only_when_needed() -> None:
    assert format_duration(65.0) == "01:05"
    assert format_duration(65.125) == "01:05.125"
