from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from PySide6.QtWidgets import QMessageBox

from aavc.application.commands import (
    AdvancedAnimationActivationRequired,
    ApplyAnimationKeyframeEdit,
)
from aavc.domain.animation import AnimationKeyframe, AnimationKeyframeTrack
from aavc.domain.project.models import AnimationAssignment
from aavc.presentation.dialogs.asset_motion import AssetMotionDialogResult
from aavc.presentation.windows import animation_menu_window as module
from aavc.presentation.windows.animation_menu_window import AnimationMenuMainWindow


class _StatusBar:
    def __init__(self) -> None:
        self.messages: list[tuple[str, int]] = []

    def showMessage(self, message: str, timeout: int) -> None:
        self.messages.append((message, timeout))


class _FakeSession:
    def __init__(
        self,
        project: Any,
        *,
        activation_required: AdvancedAnimationActivationRequired | None = None,
    ) -> None:
        self.current = project
        self.activation_required = activation_required
        self.commands: list[Any] = []

    def execute(self, command: Any) -> Any:
        self.commands.append(command)
        if isinstance(command, ApplyAnimationKeyframeEdit):
            if self.activation_required is not None and not command.activate_advanced:
                raise self.activation_required
            updated = SimpleNamespace(
                animations=(command.assignment,),
                schema_version=(
                    4 if command.activate_advanced else self.current.schema_version
                ),
            )
            self.current = updated
            return updated
        raise AssertionError(
            f"Unexpected command type: {type(command).__name__}"
        )


def _candidate(*, scene_number: int = 1, asset_id: str = "asset-1") -> AnimationAssignment:
    track = AnimationKeyframeTrack(
        property_name="opacity",
        keyframes=(
            AnimationKeyframe(time=0.0, value=0.2),
            AnimationKeyframe(time=1.0, value=1.0),
        ),
    )
    return AnimationAssignment(
        scene_number=scene_number,
        asset_id=asset_id,
        enter_effect="Fade",
        exit_effect="Fade",
        keyframe_tracks=(track,),
    )


def _controller(session: _FakeSession) -> AnimationMenuMainWindow:
    controller = object.__new__(AnimationMenuMainWindow)
    controller.services = SimpleNamespace(project_session=session)
    controller._selected_scene_number = 1
    controller.window = SimpleNamespace(statusBar=lambda: _StatusBar())
    controller._refresh_window_title = lambda: None
    controller.refresh_editor_overview = lambda: None
    controller._refresh_animation_menu_state = lambda: None
    return controller


def _project(*, schema_version: int) -> Any:
    return SimpleNamespace(
        schema_version=schema_version,
        metadata={},
        scenes=(SimpleNamespace(scene_number=1),),
        animations=(),
    )


def test_controller_passes_real_schema_version_to_asset_motion_dialog(
    monkeypatch: Any,
) -> None:
    session = _FakeSession(_project(schema_version=4))
    controller = _controller(session)
    captured: dict[str, Any] = {}

    def fake_dialog(*args: Any, **kwargs: Any) -> None:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return None

    monkeypatch.setattr(module, "show_asset_motion_dialog", fake_dialog)

    controller.edit_selected_scene_asset_motion()

    assert captured["kwargs"]["project_schema_version"] == 4
    assert session.commands == []


def test_v3_advanced_apply_rejects_activation_without_mutation(
    monkeypatch: Any,
) -> None:
    candidate = _candidate()
    activation = AdvancedAnimationActivationRequired(
        scene_number=1,
        asset_id="asset-1",
        changed_properties=("opacity",),
        dormant_locations=(),
        requires_dormant_acknowledgement=False,
    )
    project = _project(schema_version=3)
    session = _FakeSession(project, activation_required=activation)
    controller = _controller(session)

    monkeypatch.setattr(
        module,
        "show_asset_motion_dialog",
        lambda *args, **kwargs: AssetMotionDialogResult(
            action="apply",
            asset_id="asset-1",
            assignment=candidate,
        ),
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )

    controller.edit_selected_scene_asset_motion()

    assert len(session.commands) == 1
    first = session.commands[0]
    assert isinstance(first, ApplyAnimationKeyframeEdit)
    assert first.activate_advanced is False
    assert session.current is project


def test_v3_advanced_apply_accepts_activation_as_one_retry(
    monkeypatch: Any,
) -> None:
    candidate = _candidate()
    activation = AdvancedAnimationActivationRequired(
        scene_number=1,
        asset_id="asset-1",
        changed_properties=("opacity",),
        dormant_locations=(),
        requires_dormant_acknowledgement=False,
    )
    session = _FakeSession(
        _project(schema_version=3),
        activation_required=activation,
    )
    controller = _controller(session)

    monkeypatch.setattr(
        module,
        "show_asset_motion_dialog",
        lambda *args, **kwargs: AssetMotionDialogResult(
            action="apply",
            asset_id="asset-1",
            assignment=candidate,
        ),
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    controller.edit_selected_scene_asset_motion()

    assert len(session.commands) == 2
    first, second = session.commands
    assert isinstance(first, ApplyAnimationKeyframeEdit)
    assert isinstance(second, ApplyAnimationKeyframeEdit)
    assert first.activate_advanced is False
    assert second.activate_advanced is True
    assert second.acknowledge_dormant is False
    assert session.current.schema_version == 4


def test_v3_activation_acknowledges_unrelated_dormant_tracks(
    monkeypatch: Any,
) -> None:
    candidate = _candidate()
    activation = AdvancedAnimationActivationRequired(
        scene_number=1,
        asset_id="asset-1",
        changed_properties=("opacity",),
        dormant_locations=((2, "asset-2", "blur"),),
        requires_dormant_acknowledgement=True,
    )
    session = _FakeSession(
        _project(schema_version=3),
        activation_required=activation,
    )
    controller = _controller(session)
    prompts: list[str] = []

    monkeypatch.setattr(
        module,
        "show_asset_motion_dialog",
        lambda *args, **kwargs: AssetMotionDialogResult(
            action="apply",
            asset_id="asset-1",
            assignment=candidate,
        ),
    )

    def accept(*args: Any, **kwargs: Any) -> QMessageBox.StandardButton:
        if len(args) >= 3:
            prompts.append(str(args[2]))
        return QMessageBox.StandardButton.Yes

    monkeypatch.setattr(QMessageBox, "question", accept)

    controller.edit_selected_scene_asset_motion()

    assert len(session.commands) == 2
    retry = session.commands[1]
    assert isinstance(retry, ApplyAnimationKeyframeEdit)
    assert retry.activate_advanced is True
    assert retry.acknowledge_dormant is True
    assert any("asset-2" in prompt and "blur" in prompt for prompt in prompts)


def test_v4_advanced_apply_uses_canonical_command_without_reprompt(
    monkeypatch: Any,
) -> None:
    candidate = _candidate()
    session = _FakeSession(_project(schema_version=4))
    controller = _controller(session)

    monkeypatch.setattr(
        module,
        "show_asset_motion_dialog",
        lambda *args, **kwargs: AssetMotionDialogResult(
            action="apply",
            asset_id="asset-1",
            assignment=candidate,
        ),
    )

    def unexpected_prompt(*args: Any, **kwargs: Any) -> QMessageBox.StandardButton:
        raise AssertionError("Existing v4 project must not prompt for activation")

    monkeypatch.setattr(QMessageBox, "question", unexpected_prompt)

    controller.edit_selected_scene_asset_motion()

    assert len(session.commands) == 1
    command = session.commands[0]
    assert isinstance(command, ApplyAnimationKeyframeEdit)
    assert command.activate_advanced is False
