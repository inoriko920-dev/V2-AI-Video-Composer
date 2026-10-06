from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnimationEffect:
    effect_id: str
    display_name: str
    category: str


_EFFECTS = (
    AnimationEffect("rise", "Rise", "General"),
    AnimationEffect("pan", "Pan", "General"),
    AnimationEffect("fade", "Fade", "General"),
    AnimationEffect("pop", "Pop", "General"),
    AnimationEffect("wipe", "Wipe", "General"),
    AnimationEffect("blur", "Blur", "General"),
    AnimationEffect("succession", "Succession", "General"),
    AnimationEffect("breathe", "Breathe", "General"),
    AnimationEffect("baseline", "Baseline", "General"),
    AnimationEffect("drift", "Drift", "General"),
    AnimationEffect("tectonic", "Tectonic", "General"),
    AnimationEffect("tumble", "Tumble", "General"),
    AnimationEffect("neon", "Neon", "General"),
    AnimationEffect("scrapbook", "Scrapbook", "General"),
    AnimationEffect("stomp", "Stomp", "General"),
    AnimationEffect("brush", "Brush", "Reveal"),
    AnimationEffect("ink", "Ink", "Reveal"),
    AnimationEffect("digital", "Digital", "Reveal"),
    AnimationEffect("spray_paint", "Spray Paint", "Reveal"),
    AnimationEffect("sketch", "Sketch", "Reveal"),
    AnimationEffect("gradient", "Gradient", "Reveal"),
)

_BY_NAME = {effect.display_name: effect for effect in _EFFECTS}


def all_effects() -> tuple[AnimationEffect, ...]:
    return _EFFECTS


def effect_names() -> tuple[str, ...]:
    return tuple(effect.display_name for effect in _EFFECTS)


def get_effect(name: str) -> AnimationEffect:
    try:
        return _BY_NAME[name]
    except KeyError as exc:
        raise ValueError(f"Efek animasi tidak didukung: {name}") from exc


def validate_effect(name: str) -> None:
    get_effect(name)
