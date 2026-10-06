from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from aavc.domain.errors import RenderError
from aavc.domain.project.models import RenderQualitySettings
from aavc.platform.process_runner import ProcessResult, ProcessRunner
from aavc.rendering.render_plan import RenderPlan, SceneRenderPlan
from aavc.rendering.validation import RenderManifest, verify_render_output


class ProbeRunner(ProcessRunner):
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del argv, timeout_seconds
        return ProcessResult(0, json.dumps(self.payload), "")


def _manifest() -> RenderManifest:
    plan = RenderPlan(
        width=1920,
        height=1080,
        fps=30,
        scenes=(
            SceneRenderPlan(
                scene_number=1,
                duration_seconds=2.0,
                asset_paths=("A001.png",),
                placements=(),
            ),
        ),
        narration_audio=None,
        subtitle_ass=None,
        output_path="out.mp4",
        quality=RenderQualitySettings(),
    )
    return RenderManifest.from_plan(plan)


def test_verify_render_output_accepts_matching_metadata(tmp_path: Path) -> None:
    output = tmp_path / "candidate.mp4"
    output.write_bytes(b"not-empty")
    runner = ProbeRunner(
        {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                }
            ],
            "format": {"duration": "2.000"},
        }
    )

    result = verify_render_output(
        output,
        _manifest(),
        ffprobe="fake-ffprobe",
        runner=runner,
    )

    assert result.width == 1920
    assert result.height == 1080
    assert result.fps == 30.0


def test_verify_render_output_rejects_truncated_duration(tmp_path: Path) -> None:
    output = tmp_path / "candidate.mp4"
    output.write_bytes(b"not-empty")
    runner = ProbeRunner(
        {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                }
            ],
            "format": {"duration": "0.500"},
        }
    )

    with pytest.raises(RenderError, match="durasi"):
        verify_render_output(
            output,
            _manifest(),
            ffprobe="fake-ffprobe",
            runner=runner,
        )
