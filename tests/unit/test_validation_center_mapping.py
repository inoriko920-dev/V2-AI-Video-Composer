from aavc.application.services.validation import ValidationIssue
from aavc.presentation.dialogs.validation_center import (
    summarize_validation_issues,
    validation_category,
    validation_issue_action,
)


def test_validation_summary_counts_errors_and_warnings() -> None:
    issues = (
        ValidationIssue("ASSET_NOT_READY", "ERROR", "A001 belum READY", 1, "A001"),
        ValidationIssue("SCENE_DURATION_SHORT", "WARNING", "Scene pendek", 2),
        ValidationIssue("OTHER", "WARNING", "Peringatan lain"),
    )

    summary = summarize_validation_issues(issues)

    assert summary.errors == 1
    assert summary.warnings == 2
    assert summary.total == 3
    assert not summary.ok


def test_empty_validation_summary_is_ok() -> None:
    summary = summarize_validation_issues(())

    assert summary.errors == 0
    assert summary.warnings == 0
    assert summary.total == 0
    assert summary.ok


def test_validation_category_matches_engine_issue_types() -> None:
    asset_issue = ValidationIssue(
        "ASSET_NOT_READY",
        "ERROR",
        "A001 belum READY",
        1,
        "A001",
    )
    scene_issue = ValidationIssue(
        "SCENE_DURATION_SHORT",
        "WARNING",
        "Durasi pendek",
        2,
    )
    render_issue = ValidationIssue(
        "VISUAL_EFFECT_FALLBACK",
        "WARNING",
        "Wipe fallback",
        2,
        "A001",
    )
    other_issue = ValidationIssue("OTHER", "WARNING", "Lainnya")

    assert validation_category(asset_issue) == "Media"
    assert validation_category(scene_issue) == "Scene"
    keyframe_issue = ValidationIssue(
        "KEYFRAME_TRACK_FALLBACK",
        "WARNING",
        "Opacity fallback",
        2,
        "A001",
    )
    media_file_issue = ValidationIssue(
        "SUBTITLE_NOT_FOUND",
        "ERROR",
        "Subtitle hilang",
    )

    assert validation_category(render_issue) == "Render"
    assert validation_category(keyframe_issue) == "Render"
    assert validation_category(media_file_issue) == "Media"
    assert validation_category(other_issue) == "Project"


def test_validation_actions_route_to_repair_or_scene() -> None:
    asset_issue = ValidationIssue(
        "ASSET_NOT_READY",
        "ERROR",
        "A009 belum READY",
        3,
        "A009",
    )
    scene_issue = ValidationIssue(
        "SCENE_DURATION_SHORT",
        "WARNING",
        "Durasi pendek",
        3,
    )

    render_issue = ValidationIssue(
        "KEYFRAME_TRACK_FALLBACK",
        "WARNING",
        "Opacity belum aktif",
        4,
        "A010",
    )
    media_issue = ValidationIssue(
        "NARRATION_NOT_FOUND",
        "ERROR",
        "Narasi hilang",
    )

    assert validation_issue_action(asset_issue) == ("Relink", "A009")
    assert validation_issue_action(scene_issue) == ("Buka Scene", "3")
    assert validation_issue_action(render_issue) == ("Buka Scene", "4")
    assert validation_issue_action(media_issue) == ("Impor Media", "")
