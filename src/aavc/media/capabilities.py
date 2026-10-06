from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

CAPABILITY_SCHEMA_VERSION = 1


class MediaCapability(StrEnum):
    """Backend-neutral media capabilities exposed to application/UI layers."""

    PROBE = "probe"
    PREVIEW_FRAME = "preview_frame"
    FINAL_RENDER = "final_render"
    EFFECT_COMPILATION = "effect_compilation"
    AUDIO_PIPELINE = "audio_pipeline"
    SUBTITLE_PIPELINE = "subtitle_pipeline"
    TIMELINE_ADAPTER = "timeline_adapter"


@dataclass(frozen=True, slots=True)
class BackendAvailability:
    available: bool
    version: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.available and self.reason:
            raise ValueError("Backend tersedia tidak boleh memiliki reason error")
        if not self.available and not self.reason:
            raise ValueError("Backend tidak tersedia harus memiliki reason")


@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    """Versioned, immutable description of what one media backend can do."""

    backend_id: str
    display_name: str
    capabilities: frozenset[MediaCapability]
    render_effects: tuple[str, ...] = ()
    preview_effects: tuple[str, ...] = ()
    is_reference: bool = False
    schema_version: int = CAPABILITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.backend_id.strip():
            raise ValueError("backend_id tidak boleh kosong")
        if not self.display_name.strip():
            raise ValueError("display_name tidak boleh kosong")
        if self.schema_version <= 0:
            raise ValueError("schema_version harus > 0")
        if len(self.render_effects) != len(set(self.render_effects)):
            raise ValueError("render_effects tidak boleh duplikat")
        if len(self.preview_effects) != len(set(self.preview_effects)):
            raise ValueError("preview_effects tidak boleh duplikat")

    def supports(self, capability: MediaCapability) -> bool:
        return capability in self.capabilities

    def supports_render_effect(self, effect_name: str) -> bool:
        return effect_name in self.render_effects

    def supports_preview_effect(self, effect_name: str) -> bool:
        return effect_name in self.preview_effects

    @property
    def parity_effects(self) -> tuple[str, ...]:
        preview = set(self.preview_effects)
        return tuple(name for name in self.render_effects if name in preview)
