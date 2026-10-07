from __future__ import annotations

from collections.abc import Sequence

from aavc.platform.process_runner import ProcessResult, ProcessRunner
from aavc.platform.tool_registry import ToolResolution
from aavc.rendering.advanced_capabilities import (
    AdvancedFFmpegCapabilityProbe,
    AdvancedFFmpegFeature,
)
from aavc.rendering.ffmpeg_tool_capabilities import FFmpegToolCapabilityService


class RecordingVersionRunner(ProcessRunner):
    def __init__(self, *, returncode: int = 0) -> None:
        self.returncode = returncode
        self.calls = 0

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del argv, timeout_seconds
        self.calls += 1
        if self.returncode:
            return ProcessResult(self.returncode, "", "probe failed")
        return ProcessResult(0, "ffmpeg version 9.0.2 Copyright", "")


def _resolver() -> ToolResolution:
    return ToolResolution(name="ffmpeg", path="fake-ffmpeg", source="test")


def test_k0_advanced_probe_is_cached_fingerprinted_and_claims_no_features() -> None:
    runner = RecordingVersionRunner()
    probe = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver)

    first = probe.probe()
    second = probe.probe()

    assert first.available is True
    assert first.version == "9.0.2"
    assert first.fingerprint
    assert first.features == frozenset()
    assert not first.supports(AdvancedFFmpegFeature.DYNAMIC_SPATIAL_ALPHA)
    assert second == first
    assert runner.calls == 1

    refreshed = probe.refresh()
    assert refreshed.fingerprint == first.fingerprint
    assert runner.calls == 2


def test_advanced_probe_fails_closed_when_ffmpeg_probe_fails() -> None:
    runner = RecordingVersionRunner(returncode=1)
    result = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver).probe()

    assert result.available is False
    assert result.fingerprint is None
    assert result.features == frozenset()
    assert "probe failed" in result.diagnostics[0]


def test_tool_capability_refresh_invalidates_advanced_cache_without_extra_probe() -> None:
    runner = RecordingVersionRunner()
    service = FFmpegToolCapabilityService(runner=runner, resolver=_resolver)

    service.availability()
    advanced = service.advanced_capabilities()
    assert advanced.available is True
    assert runner.calls == 2

    service.refresh()
    assert runner.calls == 3

    service.advanced_capabilities()
    assert runner.calls == 4
