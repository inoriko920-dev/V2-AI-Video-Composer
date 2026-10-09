"""Regression: invalid FFprobe metadata must not mark an MP4 export successful."""
from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from aavc.domain.errors import RenderError
from aavc.platform.process_runner import ProcessResult, ProcessRunner
from aavc.rendering.validation import RenderManifest, verify_render_output


class FakeProbe(ProcessRunner):
    def __init__(self, response: Any) -> None:
        self.response = response

    def run(
        self, argv: Sequence[str], *, timeout_seconds: float | None = None
    ) -> ProcessResult:
        del argv, timeout_seconds
        return ProcessResult(0, json.dumps(self.response), "")


def _manifest() -> RenderManifest:
    return RenderManifest(
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


def _probe_payload(*, duration: Any = "2.000", fps: Any = "30/1") -> dict[str, Any]:
    return {
        "streams": [
            {"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": fps}
        ],
        "format": {"duration": duration},
    }


@pytest.mark.parametrize("duration", ["NaN", "Infinity", "-Infinity", "0", "-2", "1e999"])
def test_render_rejects_nonfinite_or_nonpositive_duration(
    tmp_path: Path, duration: str
) -> None:
    output = tmp_path / "video.mp4"
    output.write_bytes(b"not-empty")
    with pytest.raises(RenderError, match="metadata|durasi|Validasi"):
        verify_render_output(
            output, _manifest(), ffprobe="fake", runner=FakeProbe(_probe_payload(duration=duration))
        )


@pytest.mark.parametrize(
    "fps", ["NaN", "Infinity", "-Infinity", "0", "0/0", "-30/1", "1e999"]
)
def test_render_rejects_nonfinite_or_nonpositive_frame_rate(
    tmp_path: Path, fps: str
) -> None:
    output = tmp_path / "video.mp4"
    output.write_bytes(b"not-empty")
    with pytest.raises(RenderError, match="metadata|fps|Validasi"):
        verify_render_output(
            output, _manifest(), ffprobe="fake", runner=FakeProbe(_probe_payload(fps=fps))
        )


@pytest.mark.parametrize(
    "payload",
    [
        [],
        None,
        {"streams": "not-an-array", "format": {"duration": 2}},
        {"streams": [None], "format": {"duration": 2}},
        {"streams": [{"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "30/1"}], "format": []},
        {"streams": [], "format": {"duration": 2}},
    ],
)
def test_render_handles_malformed_ffprobe_shapes_as_render_error(
    tmp_path: Path, payload: Any
) -> None:
    output = tmp_path / "video.mp4"
    output.write_bytes(b"not-empty")
    with pytest.raises(RenderError, match="metadata|valid"):
        verify_render_output(output, _manifest(), ffprobe="fake", runner=FakeProbe(payload))


def test_render_accepts_finite_matching_probe_metadata(tmp_path: Path) -> None:
    output = tmp_path / "video.mp4"
    output.write_bytes(b"not-empty")
    result = verify_render_output(
        output, _manifest(), ffprobe="fake", runner=FakeProbe(_probe_payload())
    )
    assert result.duration_seconds == 2.0
    assert result.fps == 30.0
