from pathlib import Path

import pytest

from aavc.application.commands import SetSubtitleStyle
from aavc.application.services.project_session import ProjectSession
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.project.models import SubtitleStyle

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _project():
    return create_project_state(
        title="subtitle-style",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_subtitle_style_enters_project_history_and_undo_redo() -> None:
    session = ProjectSession()
    project = _project()
    session.start(project)
    style = SubtitleStyle(
        preset_name="Cinematic",
        font_family="Arial",
        font_size=62,
        fill_color="#F8FAFC",
        outline_color="#0F172A",
        outline_width=2.5,
        shadow=0.5,
        background_box=True,
        background_opacity=35,
        alignment=2,
        margin_v=90,
    )

    changed = session.execute(SetSubtitleStyle(style))
    assert changed.subtitle_style == style
    assert session.can_undo

    undone = session.undo()
    assert undone.subtitle_style == project.subtitle_style

    redone = session.redo()
    assert redone.subtitle_style == style


@pytest.mark.parametrize(
    ("style", "message"),
    [
        (SubtitleStyle(fill_color="white"), "#RRGGBB"),
        (SubtitleStyle(outline_color="#ZZZZZZ"), "#RRGGBB"),
        (SubtitleStyle(font_size=0), "1–400"),
        (SubtitleStyle(background_opacity=101), "0–100"),
        (SubtitleStyle(alignment=10), "1–9"),
        (SubtitleStyle(margin_v=-1), "0–5000"),
    ],
)
def test_subtitle_style_rejects_invalid_values(
    style: SubtitleStyle,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        SetSubtitleStyle(style).apply(_project())
