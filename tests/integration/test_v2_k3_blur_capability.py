from __future__ import annotations

import shutil

import pytest

from aavc.platform.tool_registry import ToolResolution
from aavc.rendering.advanced_capabilities import (
    AdvancedFFmpegCapabilityProbe,
    AdvancedFFmpegFeature,
)


@pytest.mark.integration
def test_k3_real_ffmpeg_proves_frame_accurate_runtime_gblur() -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg not available")

    capabilities = AdvancedFFmpegCapabilityProbe(
        resolver=lambda: ToolResolution(
            name="ffmpeg",
            path=ffmpeg,
            source="integration",
        )
    ).probe()

    assert capabilities.available
    assert capabilities.supports(AdvancedFFmpegFeature.NAMED_GBLUR)
    assert capabilities.supports(AdvancedFFmpegFeature.SENDCMD_RUNTIME_SIGMA)
    assert capabilities.supports(AdvancedFFmpegFeature.PREMULTIPLY_ALPHA)
