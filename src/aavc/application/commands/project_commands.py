from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from aavc.animation.registry import validate_effect
from aavc.application.media_import import classify_media_path
from aavc.domain.project.models import (
    AnimationAssignment,
    AssetBinding,
    ProjectState,
    Scene,
    SubtitleAnimationSettings,
    SubtitleStyle,
)


class ProjectCommand(Protocol):
    def apply(self, project: ProjectState) -> ProjectState: ...

    def describe(self) -> str: ...


def _validate_hex_color(value: str, field_name: str) -> None:
    if len(value) != 7 or not value.startswith("#"):
        raise ValueError(f"{field_name} harus berformat #RRGGBB")
    try:
        int(value[1:], 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} harus berformat #RRGGBB") from exc


@dataclass(frozen=True, slots=True)
class SetSceneDuration:
    scene_number: int
    duration_seconds: float

    def apply(self, project: ProjectState) -> ProjectState:
        if self.duration_seconds <= 0:
            raise ValueError("Durasi scene harus lebih dari 0")
        found = False
        scenes: list[Scene] = []
        for scene in project.scenes:
            if scene.scene_number == self.scene_number:
                found = True
                scenes.append(replace(scene, duration_seconds=self.duration_seconds))
            else:
                scenes.append(scene)
        if not found:
            raise ValueError(f"Scene {self.scene_number} tidak ditemukan")
        return replace(project, scenes=tuple(scenes))

    def describe(self) -> str:
        return f"Ubah durasi Scene {self.scene_number} menjadi {self.duration_seconds:.3f}s"


@dataclass(frozen=True, slots=True)
class RelinkAsset:
    asset_id: str
    replacement_path: str

    def apply(self, project: ProjectState) -> ProjectState:
        path = Path(self.replacement_path)
        if not path.is_file():
            raise ValueError(f"File pengganti tidak ditemukan: {path}")
        found = False
        bindings: list[AssetBinding] = []
        for binding in project.bindings:
            if binding.asset_id == self.asset_id:
                found = True
                bindings.append(replace(binding, path=str(path.resolve()), status="READY"))
            else:
                bindings.append(binding)
        if not found:
            raise ValueError(f"Asset {self.asset_id} tidak ditemukan")
        return replace(project, bindings=tuple(bindings))

    def describe(self) -> str:
        return f"Relink {self.asset_id}"


@dataclass(frozen=True, slots=True)
class SetNarrationAudio:
    source_path: str

    def apply(self, project: ProjectState) -> ProjectState:
        source = Path(self.source_path)
        if classify_media_path(source) != "narration":
            raise ValueError("File yang dipilih bukan audio narasi yang didukung")
        return replace(project, narration_audio=str(source.resolve()))

    def describe(self) -> str:
        return f"Atur narasi audio: {Path(self.source_path).name}"


@dataclass(frozen=True, slots=True)
class SetSubtitleSource:
    source_path: str

    def apply(self, project: ProjectState) -> ProjectState:
        source = Path(self.source_path)
        if classify_media_path(source) != "subtitle":
            raise ValueError("File yang dipilih bukan subtitle SRT")
        return replace(project, subtitle_source=str(source.resolve()))

    def describe(self) -> str:
        return f"Atur subtitle: {Path(self.source_path).name}"


@dataclass(frozen=True, slots=True)
class SetSubtitleStyle:
    style: SubtitleStyle

    def apply(self, project: ProjectState) -> ProjectState:
        style = self.style
        if not style.font_family.strip():
            raise ValueError("Font subtitle tidak boleh kosong")
        if not 1 <= style.font_size <= 400:
            raise ValueError("Ukuran font subtitle harus 1–400")
        _validate_hex_color(style.fill_color, "Warna isi subtitle")
        _validate_hex_color(style.outline_color, "Warna outline subtitle")
        if not 0 <= style.outline_width <= 20:
            raise ValueError("Outline subtitle harus 0–20")
        if not 0 <= style.shadow <= 20:
            raise ValueError("Shadow subtitle harus 0–20")
        if not 0 <= style.background_opacity <= 100:
            raise ValueError("Opacity background subtitle harus 0–100")
        if not 1 <= style.alignment <= 9:
            raise ValueError("Alignment subtitle harus 1–9")
        if not 0 <= style.margin_v <= 5000:
            raise ValueError("Margin vertikal subtitle harus 0–5000")
        return replace(project, subtitle_style=style)

    def describe(self) -> str:
        return f"Atur gaya subtitle: {self.style.preset_name}"


SUPPORTED_SUBTITLE_ANIMATION_PRESETS = {
    "Fade",
    "Clean Documentary",
    "Pop",
    "Slide Up",
}


@dataclass(frozen=True, slots=True)
class SetSubtitleAnimation:
    animation: SubtitleAnimationSettings

    def apply(self, project: ProjectState) -> ProjectState:
        animation = self.animation
        if animation.preset not in SUPPORTED_SUBTITLE_ANIMATION_PRESETS:
            raise ValueError("Preset animasi subtitle tidak didukung")
        if not 0 <= animation.enter_duration_ms <= 10000:
            raise ValueError("Durasi masuk subtitle harus 0–10000 ms")
        if not 0 <= animation.exit_duration_ms <= 10000:
            raise ValueError("Durasi keluar subtitle harus 0–10000 ms")
        if not 0.0 <= animation.intensity <= 2.0:
            raise ValueError("Intensitas animasi subtitle harus 0–2")
        _validate_hex_color(animation.highlight_color, "Warna highlight subtitle")
        return replace(project, subtitle_animation=animation)

    def describe(self) -> str:
        return f"Atur animasi subtitle: {self.animation.preset}"


@dataclass(frozen=True, slots=True)
class SetAnimationAssignment:
    assignment: AnimationAssignment

    def apply(self, project: ProjectState) -> ProjectState:
        validate_effect(self.assignment.enter_effect)
        validate_effect(self.assignment.exit_effect)
        valid_assets = {
            (scene.scene_number, asset_id)
            for scene in project.scenes
            for asset_id in scene.asset_ids
        }
        key = (self.assignment.scene_number, self.assignment.asset_id)
        if key not in valid_assets:
            raise ValueError("Target animasi tidak ada di scene")
        items = [
            item
            for item in project.animations
            if (item.scene_number, item.asset_id) != key
        ]
        items.append(self.assignment)
        items.sort(key=lambda item: (item.scene_number, item.asset_id))
        return replace(project, animations=tuple(items))

    def describe(self) -> str:
        return f"Atur animasi {self.assignment.asset_id} pada Scene {self.assignment.scene_number}"