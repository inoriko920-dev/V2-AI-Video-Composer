from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .capabilities import BackendAvailability, BackendCapabilities

if TYPE_CHECKING:
    from aavc.rendering.executor import RenderResult
    from aavc.rendering.render_plan import RenderPlan


@dataclass(frozen=True, slots=True)
class MediaProbe:
    source_path: str
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    has_video: bool = False
    has_audio: bool = False


@dataclass(frozen=True, slots=True)
class PreviewFrameRequest:
    source_path: str
    timestamp_seconds: float
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class PreviewFrame:
    width: int
    height: int
    pixel_format: str
    data: bytes


@runtime_checkable
class CapabilityProvider(Protocol):
    def describe_capabilities(self) -> BackendCapabilities: ...


@runtime_checkable
class ToolCapabilityService(CapabilityProvider, Protocol):
    def availability(self) -> BackendAvailability: ...


@runtime_checkable
class ProbeService(CapabilityProvider, Protocol):
    def probe(self, source_path: str) -> MediaProbe: ...


@runtime_checkable
class PreviewFrameSource(CapabilityProvider, Protocol):
    def frame_at(self, request: PreviewFrameRequest) -> PreviewFrame: ...


@runtime_checkable
class RenderBackend(CapabilityProvider, Protocol):
    def render(self, plan: RenderPlan) -> RenderResult: ...


@runtime_checkable
class EffectCompiler(CapabilityProvider, Protocol):
    def supports_effect(self, effect_name: str) -> bool: ...


@runtime_checkable
class AudioPipeline(CapabilityProvider, Protocol):
    def supports_audio_codec(self, codec_name: str) -> bool: ...


@runtime_checkable
class SubtitlePipeline(CapabilityProvider, Protocol):
    def supports_subtitle_format(self, format_name: str) -> bool: ...


@runtime_checkable
class TimelineAdapter(CapabilityProvider, Protocol):
    def supports_timeline_format(self, format_name: str) -> bool: ...
