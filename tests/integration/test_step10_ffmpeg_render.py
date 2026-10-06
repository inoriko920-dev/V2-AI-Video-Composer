import shutil
from pathlib import Path

import pytest

from aavc.application.services.vertical_slice import run_vertical_slice

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


@pytest.mark.integration
def test_ffmpeg_vertical_slice_renders(tmp_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg not available")
    result = run_vertical_slice(
        title="Integration Demo",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
        narration_audio=FIXTURE / "narration.wav",
        subtitle_srt=FIXTURE / "subtitle.srt",
        output_directory=tmp_path,
        ffmpeg=ffmpeg,
    )
    video = Path(result["video"])
    assert video.exists()
    assert video.stat().st_size > 10_000
