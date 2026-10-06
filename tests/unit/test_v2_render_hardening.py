from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from aavc.domain.errors import RenderError
from aavc.platform.process_runner import ProcessResult, ProcessRunner
from aavc.rendering.executor import execute_ffmpeg


class ManagedFakeRunner(ProcessRunner):
    def __init__(self) -> None:
        self.command: list[str] | None = None

    def run_managed(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
        cancel_requested: Callable[[], bool] | None = None,
        stdout_line_callback: Callable[[str], None] | None = None,
        poll_interval_seconds: float = 0.05,
    ) -> ProcessResult:
        del timeout_seconds, cancel_requested, poll_interval_seconds
        self.command = list(argv)
        Path(self.command[-1]).write_bytes(b"candidate")
        if stdout_line_callback is not None:
            stdout_line_callback("out_time_us=500000")
            stdout_line_callback("progress=end")
        return ProcessResult(0, "", "")


def test_validation_failure_preserves_previous_output(tmp_path: Path) -> None:
    output = tmp_path / "movie.mp4"
    output.write_bytes(b"previous-valid")
    runner = ManagedFakeRunner()

    def reject(_candidate: Path) -> object:
        raise RenderError("invalid candidate")

    with pytest.raises(RenderError, match="invalid candidate"):
        execute_ffmpeg(
            ["ffmpeg", "-i", "input", str(output)],
            runner=runner,
            validator=reject,
            cancel_requested=lambda: False,
        )

    assert output.read_bytes() == b"previous-valid"
    assert list(tmp_path.glob(".*.aavc-render-*.mp4")) == []


def test_progress_protocol_reports_fraction_without_changing_final_output(tmp_path: Path) -> None:
    output = tmp_path / "progress.mp4"
    runner = ManagedFakeRunner()
    progress: list[float] = []

    execute_ffmpeg(
        ["ffmpeg", "-i", "input", str(output)],
        runner=runner,
        progress_callback=progress.append,
        expected_duration_seconds=1.0,
    )

    assert output.read_bytes() == b"candidate"
    assert progress[0] == 0.0
    assert 0.49 <= progress[1] <= 0.51
    assert progress[-1] == 1.0
    assert runner.command is not None
    assert "-progress" in runner.command
