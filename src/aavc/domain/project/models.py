from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from aavc.domain.animation import AnimationKeyframeTrack

SceneMode = Literal["SINGLE", "DOUBLE"]
AssetStatus = Literal["READY", "MISSING", "CORRUPT", "DUPLICATE"]


@dataclass(frozen=True, slots=True)
class AssetBinding:
    asset_id: str
    source_quote: str
    path: str | None
    status: AssetStatus


@dataclass(frozen=True, slots=True)
class Scene:
    scene_number: int
    asset_ids: tuple[str, ...]
    source_quotes: tuple[str, ...]
    duration_seconds: float = 3.0

    @property
    def mode(self) -> SceneMode:
        if len(self.asset_ids) == 1:
            return "SINGLE"
        if len(self.asset_ids) == 2:
            return "DOUBLE"
        raise ValueError("A scene must contain exactly one or two assets")


@dataclass(frozen=True, slots=True)
class AnimationAssignment:
    scene_number: int
    asset_id: str
    enter_effect: str = "Fade"
    exit_effect: str = "Fade"
    intensity: float = 1.0
    locked: bool = False
    keyframe_tracks: tuple[AnimationKeyframeTrack, ...] = ()

    def __post_init__(self) -> None:
        properties = [track.property_name for track in self.keyframe_tracks]
        if len(properties) != len(set(properties)):
            raise ValueError(
                "Satu assignment tidak boleh memiliki track keyframe property duplikat"
            )


@dataclass(frozen=True, slots=True)
class SubtitleStyle:
    preset_name: str = "Dokumenter"
    font_family: str = "Arial"
    font_size: int = 54
    fill_color: str = "#FFFFFF"
    outline_color: str = "#111111"
    outline_width: float = 3.0
    shadow: float = 1.0
    background_box: bool = False
    background_opacity: int = 0
    alignment: int = 2
    margin_v: int = 64


@dataclass(frozen=True, slots=True)
class SubtitleAnimationSettings:
    preset: str = "Fade"
    enter_duration_ms: int = 250
    exit_duration_ms: int = 250
    intensity: float = 1.0
    highlight_color: str = "#FFD400"


@dataclass(frozen=True, slots=True)
class RenderQualitySettings:
    preset_name: str = "Documentary Crisp"
    video_codec: str = "libx264"
    encoder_preset: str = "medium"
    crf: int = 18
    audio_bitrate_kbps: int = 192
    scale_algorithm: str = "lanczos"
    sharpen_amount: float = 0.18


@dataclass(frozen=True, slots=True)
class ProjectState:
    schema_version: int
    title: str
    source_docx: str
    asset_directory: str
    scenes: tuple[Scene, ...]
    bindings: tuple[AssetBinding, ...]
    narration_audio: str | None = None
    subtitle_source: str | None = None
    background_source: str | None = None
    fps: int = 30
    width: int = 1920
    height: int = 1080
    animations: tuple[AnimationAssignment, ...] = ()
    subtitle_style: SubtitleStyle = field(default_factory=SubtitleStyle)
    subtitle_animation: SubtitleAnimationSettings = field(default_factory=SubtitleAnimationSettings)
    render_quality: RenderQualitySettings = field(default_factory=RenderQualitySettings)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return sum(scene.duration_seconds for scene in self.scenes)

    @property
    def ready(self) -> bool:
        return all(binding.status == "READY" for binding in self.bindings)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def output_default(self, project_path: Path) -> Path:
        return project_path.with_suffix(".mp4")
