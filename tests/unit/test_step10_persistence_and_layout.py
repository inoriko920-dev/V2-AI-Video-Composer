from pathlib import Path

from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.layout import solve_layout
from aavc.persistence.serializer import dumps_project, loads_project

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def test_project_round_trip() -> None:
    state = create_project_state(
        title="demo",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
        narration_audio=FIXTURE / "narration.wav",
        subtitle_srt=FIXTURE / "subtitle.srt",
    )
    restored = loads_project(dumps_project(state))
    assert restored.title == state.title
    assert restored.scenes == state.scenes
    assert restored.bindings == state.bindings


def test_single_double_layout_contract() -> None:
    state = create_project_state(
        title="demo",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )
    single = solve_layout(state.scenes[0])
    double = solve_layout(state.scenes[1])
    assert len(single) == 1 and single[0].max_height == 0.84
    assert len(double) == 2 and double[0].anchor_x < double[1].anchor_x
