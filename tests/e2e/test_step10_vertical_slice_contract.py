from pathlib import Path

from aavc.application.services.vertical_slice import create_project_state
from aavc.rendering import build_render_plan

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def test_vertical_slice_contract_from_docx_to_render_plan(tmp_path: Path) -> None:
    state = create_project_state(
        title="Demo",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
        narration_audio=FIXTURE / "narration.wav",
        subtitle_srt=FIXTURE / "subtitle.srt",
    )
    assert state.ready
    assert state.duration_seconds == 6.0
    plan = build_render_plan(state, tmp_path / "out.mp4")
    assert len(plan.scenes) == 2
    assert plan.scenes[0].placements[0].asset_id == "A001"
