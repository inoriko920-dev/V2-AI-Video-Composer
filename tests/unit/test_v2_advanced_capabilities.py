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
        blur_returncode: int = 0,
        blur_frame_change: bool = True,
        k4_returncode: int = 0,
        k4_frame_change: bool = True,
    ) -> None:
        self.version_returncode = version_returncode
        self.opacity_returncode = opacity_returncode
        self.crop_returncode = crop_returncode
        self.blur_returncode = blur_returncode
        self.blur_frame_change = blur_frame_change
        self.k4_returncode = k4_returncode
        self.k4_frame_change = k4_frame_change
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
        if "drawbox@k2_left" in joined:
            if self.crop_returncode:
                return ProcessResult(
                    self.crop_returncode,
                    "",
                    "crop probe failed",
                )
            return ProcessResult(0, "", "")
        if "gblur@k3_probe" in joined:
            if self.blur_returncode:
                return ProcessResult(
                    self.blur_returncode,
                    "",
                    "gblur probe failed",
                )
            hashes = (
                (
                    "0, 0, 0, 1, 4096, aaaa\n"
                    "0, 1, 1, 1, 4096, bbbb\n"
                    "0, 2, 2, 1, 4096, cccc\n"
                    "0, 3, 3, 1, 4096, dddd\n"
                )
                if self.blur_frame_change
                else (
                    "0, 0, 0, 1, 4096, aaaa\n"
                    "0, 1, 1, 1, 4096, aaaa\n"
                    "0, 2, 2, 1, 4096, aaaa\n"
                    "0, 3, 3, 1, 4096, aaaa\n"
                )
            )
            return ProcessResult(0, hashes, "")
        if "gblur@k4_branch" in joined:
            if self.k4_returncode:
                return ProcessResult(
                    self.k4_returncode,
                    "",
                    "k4 branch probe failed",
                )
            hashes = (
                (
                    "0, 0, 0, 1, 4096, aaaa\n"
                    "0, 1, 1, 1, 4096, bbbb\n"
                    "0, 2, 2, 1, 4096, cccc\n"
                    "0, 3, 3, 1, 4096, dddd\n"
                )
                if self.k4_frame_change
                else (
                    "0, 0, 0, 1, 4096, aaaa\n"
                    "0, 1, 1, 1, 4096, aaaa\n"
                    "0, 2, 2, 1, 4096, aaaa\n"
                    "0, 3, 3, 1, 4096, aaaa\n"
                )
            )
            return ProcessResult(0, hashes, "")
        if self.opacity_returncode:
            return ProcessResult(
                self.opacity_returncode,
                "",
                "opacity probe failed",
            )
        return ProcessResult(0, "", "")


def _resolver() -> ToolResolution:
    return ToolResolution(name="ffmpeg", path="fake-ffmpeg", source="test")


def test_k4_probe_promotes_all_capabilities_through_shadow_glow() -> None:
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
            AdvancedFFmpegFeature.NAMED_GBLUR,
            AdvancedFFmpegFeature.SENDCMD_RUNTIME_SIGMA,
            AdvancedFFmpegFeature.PREMULTIPLY_ALPHA,
            AdvancedFFmpegFeature.ALPHA_BRANCH,
            AdvancedFFmpegFeature.OVERLAY_EXPRESSIONS,
        }
    )
    assert first.supports(AdvancedFFmpegFeature.OPACITY_RUNTIME_ALPHA)
    assert first.supports(AdvancedFFmpegFeature.DYNAMIC_SPATIAL_ALPHA)
    assert first.supports(AdvancedFFmpegFeature.NAMED_GBLUR)
    assert first.supports(AdvancedFFmpegFeature.SENDCMD_RUNTIME_SIGMA)
    assert first.supports(AdvancedFFmpegFeature.PREMULTIPLY_ALPHA)
    assert first.supports(AdvancedFFmpegFeature.ALPHA_BRANCH)
    assert first.supports(AdvancedFFmpegFeature.OVERLAY_EXPRESSIONS)
    assert second == first
    assert runner.calls == 5

    refreshed = probe.refresh()
    assert refreshed.fingerprint == first.fingerprint
    assert runner.calls == 10


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
    assert runner.calls == 6

    service.refresh()
    assert runner.calls == 7

    service.advanced_capabilities()
    assert runner.calls == 12


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


def test_k3_gblur_features_are_not_promoted_when_micro_render_fails() -> None:
    runner = RecordingVersionRunner(blur_returncode=1)
    result = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver).probe()

    assert result.available is True
    assert not result.supports(AdvancedFFmpegFeature.NAMED_GBLUR)
    assert not result.supports(AdvancedFFmpegFeature.SENDCMD_RUNTIME_SIGMA)
    assert not result.supports(AdvancedFFmpegFeature.PREMULTIPLY_ALPHA)
    assert any("gblur probe failed" in item for item in result.diagnostics)


def test_k3_gblur_features_are_not_promoted_without_frame_change() -> None:
    runner = RecordingVersionRunner(blur_frame_change=False)
    result = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver).probe()

    assert result.available is True
    assert not result.supports(AdvancedFFmpegFeature.NAMED_GBLUR)
    assert not result.supports(AdvancedFFmpegFeature.SENDCMD_RUNTIME_SIGMA)
    assert any(
        "frame hashes tidak membuktikan" in item
        for item in result.diagnostics
    )


def test_k4_features_are_not_promoted_when_alpha_branch_probe_fails() -> None:
    runner = RecordingVersionRunner(k4_returncode=1)
    result = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver).probe()

    assert result.available is True
    assert not result.supports(AdvancedFFmpegFeature.ALPHA_BRANCH)
    assert not result.supports(AdvancedFFmpegFeature.OVERLAY_EXPRESSIONS)
    assert any("k4 branch probe failed" in item for item in result.diagnostics)


def test_k4_features_are_not_promoted_without_dynamic_frame_change() -> None:
    runner = RecordingVersionRunner(k4_frame_change=False)
    result = AdvancedFFmpegCapabilityProbe(runner=runner, resolver=_resolver).probe()

    assert result.available is True
    assert not result.supports(AdvancedFFmpegFeature.ALPHA_BRANCH)
    assert not result.supports(AdvancedFFmpegFeature.OVERLAY_EXPRESSIONS)
    assert any(
        "frame hashes tidak membuktikan alpha branch dinamis" in item
        for item in result.diagnostics
    )
