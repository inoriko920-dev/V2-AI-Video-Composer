from pathlib import Path

import pytest

from aavc.application.commands import SetSubtitleAnimation
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import SubtitleAnimationSettings

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="subtitle-animation",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_subtitle_animation_enters_project_history_and_undo_redo() -> None:
    session = ProjectSession()
    project = _project()
    session.start(project)
    animation = SubtitleAnimationSettings(
        preset="Pop",
        enter_duration_ms=300,
        exit_duration_ms=450,
        intensity=1.0,
        highlight_color="#FFAA00",
    )

    changed = session.execute(SetSubtitleAnimation(animation))
    assert changed.subtitle_animation == animation
    assert session.can_undo

    undone = session.undo()
    assert undone.subtitle_animation == project.subtitle_animation

    redone = session.redo()
    assert redone.subtitle_animation == animation


@pytest.mark.parametrize(
    ("animation", "message"),
    [
        (SubtitleAnimationSettings(preset="Unknown"), "tidak didukung"),
        (SubtitleAnimationSettings(enter_duration_ms=-1), "0–10000"),
        (SubtitleAnimationSettings(exit_duration_ms=10001), "0–10000"),
        (SubtitleAnimationSettings(intensity=-0.1), "0–2"),
        (SubtitleAnimationSettings(intensity=2.1), "0–2"),
        (SubtitleAnimationSettings(highlight_color="yellow"), "#RRGGBB"),
        (SubtitleAnimationSettings(highlight_color="#GGGGGG"), "#RRGGBB"),
    ],
)
def test_subtitle_animation_rejects_invalid_values(
    animation: SubtitleAnimationSettings,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        SetSubtitleAnimation(animation).apply(_project())
