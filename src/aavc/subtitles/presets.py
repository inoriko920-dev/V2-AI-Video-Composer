from __future__ import annotations

from aavc.domain.project.models import SubtitleAnimationSettings, SubtitleStyle

STYLE_PRESETS: dict[str, SubtitleStyle] = {
    "Clean": SubtitleStyle(preset_name="Clean", font_size=50, outline_width=2.0, shadow=0.5),
    "Dokumenter": SubtitleStyle(),
    "Cinematic": SubtitleStyle(preset_name="Cinematic", font_size=56, outline_width=2.5, margin_v=80),
    "Social": SubtitleStyle(preset_name="Social", font_size=60, outline_width=4.0, margin_v=54),
}

ANIMATION_PRESETS: dict[str, SubtitleAnimationSettings] = {
    "Fade": SubtitleAnimationSettings(preset="Fade"),
    "Pop": SubtitleAnimationSettings(preset="Pop", enter_duration_ms=180, exit_duration_ms=180),
    "Slide Up": SubtitleAnimationSettings(preset="Slide Up", enter_duration_ms=260, exit_duration_ms=220),
    "Word Reveal": SubtitleAnimationSettings(preset="Word Reveal", enter_duration_ms=120, exit_duration_ms=180),
    "Karaoke Highlight": SubtitleAnimationSettings(preset="Karaoke Highlight"),
    "Typewriter": SubtitleAnimationSettings(preset="Typewriter", enter_duration_ms=80, exit_duration_ms=180),
    "Bounce Soft": SubtitleAnimationSettings(preset="Bounce Soft", enter_duration_ms=220, exit_duration_ms=180),
    "Emphasis Word": SubtitleAnimationSettings(preset="Emphasis Word"),
    "Clean Documentary": SubtitleAnimationSettings(preset="Clean Documentary", enter_duration_ms=300, exit_duration_ms=300),
    "Social Caption": SubtitleAnimationSettings(preset="Social Caption", enter_duration_ms=160, exit_duration_ms=160),
}


def get_style_preset(name: str) -> SubtitleStyle:
    try:
        return STYLE_PRESETS[name]
    except KeyError as exc:
        raise ValueError(f"Preset gaya subtitle tidak dikenal: {name}") from exc


def get_animation_preset(name: str) -> SubtitleAnimationSettings:
    try:
        return ANIMATION_PRESETS[name]
    except KeyError as exc:
        raise ValueError(f"Preset animasi subtitle tidak dikenal: {name}") from exc
