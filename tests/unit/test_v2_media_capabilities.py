from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from aavc.animation.compiler import native_visual_effect_names
from aavc.media import (
    CAPABILITY_SCHEMA_VERSION,
    BackendAvailability,
    BackendCapabilities,
    MediaCapability,
)
from aavc.rendering import ffmpeg_reference_capabilities


def test_ffmpeg_reference_descriptor_matches_current_render_backing() -> None:
    descriptor = ffmpeg_reference_capabilities()

    assert descriptor.backend_id == "ffmpeg-cli"
    assert descriptor.is_reference is True
    assert descriptor.schema_version == CAPABILITY_SCHEMA_VERSION
    assert descriptor.supports(MediaCapability.FINAL_RENDER)
    assert descriptor.supports(MediaCapability.EFFECT_COMPILATION)
    assert descriptor.supports(MediaCapability.PROBE)
    assert descriptor.render_effects == native_visual_effect_names()


def test_ffmpeg_descriptor_does_not_claim_preview_capability() -> None:
    descriptor = ffmpeg_reference_capabilities()

    assert not descriptor.supports(MediaCapability.PREVIEW_FRAME)
    assert descriptor.preview_effects == ()
    assert descriptor.parity_effects == ()


def test_backend_capabilities_are_immutable_and_validate_duplicates() -> None:
    descriptor = BackendCapabilities(
        backend_id="test",
        display_name="Test Backend",
        capabilities=frozenset({MediaCapability.FINAL_RENDER}),
    )

    with pytest.raises(FrozenInstanceError):
        descriptor.backend_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="render_effects"):
        BackendCapabilities(
            backend_id="bad",
            display_name="Bad Backend",
            capabilities=frozenset(),
            render_effects=("Fade", "Fade"),
        )


def test_backend_availability_requires_consistent_reason() -> None:
    assert BackendAvailability(available=True, version="1.2").reason is None

    unavailable = BackendAvailability(
        available=False,
        reason="ffmpeg tidak ditemukan",
    )
    assert unavailable.available is False

    with pytest.raises(ValueError, match="reason"):
        BackendAvailability(available=False)
