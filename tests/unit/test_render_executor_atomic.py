from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from aavc.domain.errors import RenderError
from aavc.platform.process_runner import ProcessResult, ProcessRunner
from aavc.rendering.executor import execute_ffmpeg


class RecordingRunner(ProcessRunner):
    def __init__(self, *, returncode: int, payload: bytes, stderr: str = "") -> None:
        self.returncode = returncode
        self.payload = payload
        self.stderr = stderr
        self.commands: list[list[str]] = []

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del timeout_seconds
        command = list(argv)
        self.commands.append(command)
        Path(command[-1]).write_bytes(self.payload)
        return ProcessResult(self.returncode, "", self.stderr)


def _temporary_candidates(output: Path) -> list[Path]:
    return list(output.parent.glob(f".{output.stem}.aavc-render-*{output.suffix}"))


def test_execute_ffmpeg_replaces_destination_only_after_success(tmp_path: Path) -> None:
    output = tmp_path / "video.mp4"
    output.write_bytes(b"old-valid-video")
    runner = RecordingRunner(returncode=0, payload=b"new-valid-video")

    result = execute_ffmpeg(["ffmpeg", "-y", str(output)], runner=runner)

    assert result.output_path == str(output)
    assert output.read_bytes() == b"new-valid-video"
    assert runner.commands[0][-1] != str(output)
    assert Path(runner.commands[0][-1]).suffix == ".mp4"
    assert _temporary_candidates(output) == []


def test_execute_ffmpeg_preserves_existing_destination_on_failure(tmp_path: Path) -> None:
    output = tmp_path / "video.mp4"
    output.write_bytes(b"old-valid-video")
    runner = RecordingRunner(returncode=1, payload=b"partial-corrupt-video", stderr="boom")

    with pytest.raises(RenderError, match="boom"):
        execute_ffmpeg(["ffmpeg", "-y", str(output)], runner=runner)

    assert output.read_bytes() == b"old-valid-video"
    assert _temporary_candidates(output) == []


def test_execute_ffmpeg_rejects_empty_temporary_output_without_clobbering_destination(
    tmp_path: Path,
) -> None:
    output = tmp_path / "video.mp4"
    output.write_bytes(b"old-valid-video")
    runner = RecordingRunner(returncode=0, payload=b"")

    with pytest.raises(RenderError, match="FFmpeg gagal tanpa pesan error"):
        execute_ffmpeg(["ffmpeg", "-y", str(output)], runner=runner)

    assert output.read_bytes() == b"old-valid-video"
    assert _temporary_candidates(output) == []
