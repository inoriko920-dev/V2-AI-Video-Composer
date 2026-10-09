"""RED-first: a non-finite planned/expected duration must never pass render checks."""
from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from aavc.domain.errors import RenderError
from aavc.domain.project.models import RenderQualitySettings
from aavc.platform.process_runner import ProcessResult, ProcessRunner
from aavc.rendering.preflight import validate_render_plan
from aavc.rendering.render_plan import RenderPlan, SceneRenderPlan
from aavc.rendering.validation import RenderManifest, verify_render_output


def _plan(asset: Path, *durations: float) -> RenderPlan:
    return RenderPlan(
        width=1920,
        height=1080,
        fps=30,
        scenes=tuple(
            SceneRenderPlan(
                scene_number=i,
                duration_seconds=duration,
                asset_paths=(str(asset),),
                placements=(),
            )
            for i, duration in enumerate(durations, start=1)
        ),
        narration_audio=None,
        subtitle_ass=None,
        output_path=str(asset.parent / "render.mp4"),
        quality=RenderQualitySettings(),
    )


@pytest.mark.parametrize("duration", [float("nan"), float("inf"), float("-inf"), 0.0, -1.0])
def test_preflight_rejects_invalid_scene_duration(tmp_path: Path, duration: float) -> None:
    asset = tmp_path / "A001.png"
    asset.write_bytes(b"valid-enough-for-path-preflight")
    report = validate_render_plan(_plan(asset, duration))
    assert not report.ok
    assert "INVALID_SCENE_DURATION" in [issue.code for issue in report.issues]


def test_preflight_rejects_total_duration_overflow(tmp_path: Path) -> None:
    asset = tmp_path / "A001.png"
    asset.write_bytes(b"valid-enough-for-path-preflight")
    report = validate_render_plan(_plan(asset, 1e308, 1e308))
    assert not report.ok
    assert "INVALID_TOTAL_DURATION" in [issue.code for issue in report.issues]


class _Probe(ProcessRunner):
    def run(
        self, argv: Sequence[str], *, timeout_seconds: float | None = None
    ) -> ProcessResult:
        del argv, timeout_seconds
        return ProcessResult(
            0,
            json.dumps(
                {
                    "streams": [
                        {
                            "codec_type": "video",
                            "width": 1920,
                            "height": 1080,
                            "r_frame_rate": "30/1",
                        }
                    ],
                    "format": {"duration": "2.0"},
                }
            ),
            "",
        )


@pytest.mark.parametrize("expected", [float("nan"), float("inf"), float("-inf"), 0.0, -1.0])
def test_verifier_rejects_invalid_expected_duration(
    tmp_path: Path, expected: float
) -> None:
    output = tmp_path / "video.mp4"
    output.write_bytes(b"nonempty")
    manifest = RenderManifest(
        backend_id="ffmpeg-cli",
        expected_duration_seconds=2.0,
        width=1920,
        height=1080,
        fps=30,
        scene_count=1,
        expects_audio=False,
        burns_subtitles=False,
        video_codec="libx264",
        encoder_preset="medium",
        crf=18,
    )
    manifest = replace(manifest, expected_duration_seconds=expected)
    with pytest.raises(RenderError, match="durasi|metadata|valid"):
        verify_render_output(output, manifest, ffprobe="fake-ffprobe", runner=_Probe())


def test_finite_plan_and_expected_duration_still_pass(tmp_path: Path) -> None:
    asset = tmp_path / "A001.png"
    asset.write_bytes(b"valid-enough-for-path-preflight")
    assert validate_render_plan(_plan(asset, 2.0)).ok
    output = tmp_path / "video.mp4"
    output.write_bytes(b"nonempty")
    manifest = RenderManifest.from_plan(_plan(asset, 2.0))
    assert verify_render_output(
        output, manifest, ffprobe="fake-ffprobe", runner=_Probe()
    ).duration_seconds == 2.0
