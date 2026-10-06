from __future__ import annotations

from collections.abc import Sequence

from aavc.platform.process_runner import ProcessResult, ProcessRunner
from aavc.platform.tool_registry import ToolResolution
from aavc.rendering.ffmpeg_tool_capabilities import FFmpegToolCapabilityService


class VersionRunner(ProcessRunner):
    def __init__(self) -> None:
        self.calls = 0

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del argv, timeout_seconds
        self.calls += 1
        return ProcessResult(0, "ffmpeg version 8.0.1 Copyright", "")


def test_ffmpeg_availability_probe_is_cached_and_refreshable() -> None:
    runner = VersionRunner()
    service = FFmpegToolCapabilityService(
        runner=runner,
        resolver=lambda: ToolResolution(
            name="ffmpeg",
            path="fake-ffmpeg",
            source="test",
        ),
    )

    first = service.availability()
    second = service.availability()

    assert first.available is True
    assert first.version == "8.0.1"
    assert second == first
    assert runner.calls == 1

    service.refresh()
    assert runner.calls == 2
