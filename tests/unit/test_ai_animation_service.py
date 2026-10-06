from __future__ import annotations

import json

import pytest

from aavc.application.commands import SetAnimationAssignmentsBatch
from aavc.application.services.ai_animation_service import (
    build_ai_animation_request,
    parse_ai_animation_response,
)
from aavc.application.services.project_session import ProjectSession
from aavc.domain.project.models import AnimationAssignment, ProjectState, Scene
from aavc.presentation.windows.ai_native_motion_window import AiNativeMotionMainWindow
from aavc.presentation.windows.narration_recording_window import NarrationRecordingMainWindow

ALLOWED = ("Fade", "Pan", "Rise")


def _project() -> ProjectState:
    return ProjectState(
        schema_version=1,
        title="AI Motion",
        source_docx="scene.docx",
        asset_directory="assets",
        scenes=(
            Scene(
                scene_number=1,
                asset_ids=("A001", "A002"),
                source_quotes=("opening map", "speaker portrait"),
            ),
            Scene(
                scene_number=2,
                asset_ids=("A003",),
                source_quotes=("closing chart",),
            ),
        ),
        bindings=(),
        animations=(
            AnimationAssignment(
                scene_number=1,
                asset_id="A002",
                enter_effect="Fade",
                exit_effect="Fade",
                intensity=0.8,
                locked=True,
            ),
        ),
    )


def test_ai_runtime_preserves_narration_recording_layer() -> None:
    assert issubclass(AiNativeMotionMainWindow, NarrationRecordingMainWindow)


def test_request_contains_only_unlocked_targets_and_allowed_effects() -> None:
    request = build_ai_animation_request(
        _project(),
        model="gemini-test",
        allowed_effects=ALLOWED,
    )

    assert request.model == "gemini-test"
    assert "A001" in request.prompt
    assert "A003" in request.prompt
    assert "A002" not in request.prompt
    for effect in ALLOWED:
        assert effect in request.prompt


def test_valid_ai_response_requires_every_unlocked_target() -> None:
    response = json.dumps(
        {
            "assignments": [
                {
                    "scene_number": 1,
                    "asset_id": "A001",
                    "enter_effect": "Rise",
                    "exit_effect": "Fade",
                    "intensity": 0.9,
                },
                {
                    "scene_number": 2,
                    "asset_id": "A003",
                    "enter_effect": "Pan",
                    "exit_effect": "Fade",
                    "intensity": 1.1,
                },
            ]
        }
    )

    assignments = parse_ai_animation_response(
        response,
        _project(),
        allowed_effects=ALLOWED,
    )

    assert [(item.scene_number, item.asset_id) for item in assignments] == [
        (1, "A001"),
        (2, "A003"),
    ]
    assert all(item.locked is False for item in assignments)


def test_ai_response_rejects_unknown_effect_without_mutating_project() -> None:
    project = _project()
    response = json.dumps(
        {
            "assignments": [
                {
                    "scene_number": 1,
                    "asset_id": "A001",
                    "enter_effect": "Invented",
                    "exit_effect": "Fade",
                    "intensity": 1.0,
                },
                {
                    "scene_number": 2,
                    "asset_id": "A003",
                    "enter_effect": "Pan",
                    "exit_effect": "Fade",
                    "intensity": 1.0,
                },
            ]
        }
    )

    with pytest.raises(ValueError, match="Efek masuk"):
        parse_ai_animation_response(response, project, allowed_effects=ALLOWED)
    assert project == _project()


def test_ai_response_rejects_missing_target() -> None:
    response = json.dumps(
        {
            "assignments": [
                {
                    "scene_number": 1,
                    "asset_id": "A001",
                    "enter_effect": "Rise",
                    "exit_effect": "Fade",
                    "intensity": 1.0,
                }
            ]
        }
    )

    with pytest.raises(ValueError, match="tidak lengkap"):
        parse_ai_animation_response(response, _project(), allowed_effects=ALLOWED)


def test_atomic_batch_preserves_locked_assignment_and_undoes_in_one_step() -> None:
    project = _project()
    session = ProjectSession()
    session.start(project)
    batch = SetAnimationAssignmentsBatch(
        (
            AnimationAssignment(1, "A001", "Rise", "Fade", 0.9, False),
            AnimationAssignment(2, "A003", "Pan", "Fade", 1.1, False),
        )
    )

    session.execute(batch)
    current = session.current
    assert current is not None
    assert len(current.animations) == 3
    locked = next(item for item in current.animations if item.asset_id == "A002")
    assert locked.locked is True
    assert session.can_undo is True

    restored = session.undo()
    assert restored == project
    assert session.can_undo is False


def test_atomic_batch_rejects_locked_replacement() -> None:
    project = _project()
    command = SetAnimationAssignmentsBatch(
        (
            AnimationAssignment(1, "A002", "Rise", "Fade", 1.0, False),
        )
    )

    with pytest.raises(ValueError, match="terkunci"):
        command.apply(project)
