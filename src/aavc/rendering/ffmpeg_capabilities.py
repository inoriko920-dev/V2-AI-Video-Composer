from __future__ import annotations

from aavc.animation.compiler import native_visual_effect_names
from aavc.media import BackendCapabilities, MediaCapability


def ffmpeg_reference_capabilities() -> BackendCapabilities:
    """Describe the proven FFmpeg/ffprobe toolchain without probing the machine.

    This descriptor intentionally reports only capabilities already exercised by
    the current production path. Runtime availability/version probing belongs to
    ToolCapabilityService and is introduced separately from this static contract.
    """

    return BackendCapabilities(
        backend_id="ffmpeg-cli",
        display_name="FFmpeg CLI Reference Backend",
        capabilities=frozenset(
            {
                MediaCapability.PROBE,
                MediaCapability.FINAL_RENDER,
                MediaCapability.EFFECT_COMPILATION,
                MediaCapability.AUDIO_PIPELINE,
                MediaCapability.SUBTITLE_PIPELINE,
            }
        ),
        render_effects=native_visual_effect_names(),
        preview_effects=(),
        is_reference=True,
    )
