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
    def __init__(
        self,
        *,
        version_returncode: int = 0,
        opacity_returncode: int = 0,
        crop_returncode: int = 0,
    ) -> None:
        self.version_returncode = version_returncode
        self.opacity_returncode = opacity_returncode
        self.crop_returncode = crop_returncode
        self.calls = 0

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del timeout_seconds
        self.calls += 1
        if "-version" in argv:
            if self.version_returncode:
                return ProcessResult(
                    self.version_returncode,
                    "",
                    "version probe failed",
                )
            return ProcessResult(0, "ffmpeg version 9.0.2 Copyright", "")
        joined = " ".join(argv)
        if "geq=" in joined:
            if self.crop_returncode:
                return ProcessResult(
                    self.crop_returncode,
                    "",
                    "crop probe failed",
                )
            return ProcessResult(0, "", "")
        if self.opacity_returncode:
            return ProcessResult(
                self.opacity_returncode,
                "",
                "opacity probe failed",
            )
        return ProcessResult(0, "", "")


def _resolver() -> ToolResolution:
    return ToolResolution(name="ffmpeg", path="fake-ffmpeg", source="test")


def test_k2_advanced_probe_is_cached_and_promotes_opacity_and_spatial_alpha() -> None:
    runner = RecordingVersionRunner()
    probe = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver)

    first = probe.probe()
    second = probe.probe()

    assert first.available is True
    assert first.version == "9.0.2"
    assert first.fingerprint
    assert first.features == frozenset(
        {
            AdvancedFFmpegFeature.OPACITY_RUNTIME_ALPHA,
            AdvancedFFmpegFeature.DYNAMIC_SPATIAL_ALPHA,
        }
    )
    assert first.supports(AdvancedFFmpegFeature.OPACITY_RUNTIME_ALPHA)
    assert first.supports(AdvancedFFmpegFeature.DYNAMIC_SPATIAL_ALPHA)
    assert second == first
    assert runner.calls == 3

    refreshed = probe.refresh()
    assert refreshed.fingerprint == first.fingerprint
    assert runner.calls == 6


def test_advanced_probe_fails_closed_when_ffmpeg_probe_fails() -> None:
    runner = RecordingVersionRunner(version_returncode=1)
    result = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver).probe()

    assert result.available is False
    assert result.fingerprint is None
    assert result.features == frozenset()
    assert "version probe failed" in result.diagnostics[0]


def test_tool_capability_refresh_invalidates_advanced_cache_without_extra_probe() -> None:
    runner = RecordingVersionRunner()
    service = FFmpegToolCapabilityService(runner=runner, resolver=_resolver)

    service.availability()
    advanced = service.advanced_capabilities()
    assert advanced.available is True
    assert advanced.supports(AdvancedFFmpegFeature.OPACITY_RUNTIME_ALPHA)
    assert runner.calls == 4

    service.refresh()
    assert runner.calls == 5

    service.advanced_capabilities()
    assert runner.calls == 8



def test_k1_opacity_feature_is_not_promoted_when_micro_probe_fails() -> None:
    runner = RecordingVersionRunner(opacity_returncode=1)
    result = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver).probe()

    assert result.available is True
    assert not result.supports(AdvancedFFmpegFeature.OPACITY_RUNTIME_ALPHA)
    assert any("opacity probe failed" in item for item in result.diagnostics)



def test_k2_crop_feature_is_not_promoted_when_spatial_alpha_probe_fails() -> None:
    runner = RecordingVersionRunner(crop_returncode=1)
    result = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver).probe()

    assert result.available is True
    assert result.supports(AdvancedFFmpegFeature.OPACITY_RUNTIME_ALPHA)
    assert not result.supports(AdvancedFFmpegFeature.DYNAMIC_SPATIAL_ALPHA)
    assert any("crop probe failed" in item for item in result.diagnostics)
