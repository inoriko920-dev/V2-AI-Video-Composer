from __future__ import annotations

from pathlib import Path

from aavc.domain.project.models import SubtitleAnimationSettings, SubtitleStyle

from .srt import SubtitleCue, parse_srt


def _ass_time(seconds: float) -> str:
    centiseconds = int(round(seconds * 100))
    h, rem = divmod(centiseconds, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _hex_to_ass(value: str, *, alpha: int = 0) -> str:
    raw = value.strip().lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"Warna harus #RRGGBB: {value}")
    r, g, b = raw[0:2], raw[2:4], raw[4:6]
    return f"&H{alpha:02X}{b}{g}{r}"


def _event_text(cue: SubtitleCue, animation: SubtitleAnimationSettings) -> str:
    enter = max(0, animation.enter_duration_ms)
    exit_ = max(0, animation.exit_duration_ms)
    if animation.preset in {"Fade", "Clean Documentary"}:
        return f"{{\\fad({enter},{exit_})}}{cue.text}"
    if animation.preset == "Pop":
        return f"{{\\fad({enter},{exit_})\\fscx105\\fscy105}}{cue.text}"
    if animation.preset == "Slide Up":
        return f"{{\\fad({enter},{exit_})\\move(960,1040,960,960,0,{enter})}}{cue.text}"
    return f"{{\\fad({enter},{exit_})}}{cue.text}"


def compile_srt_to_ass(
    source: str | Path,
    destination: str | Path,
    *,
    width: int = 1920,
    height: int = 1080,
    style: SubtitleStyle | None = None,
    animation: SubtitleAnimationSettings | None = None,
) -> Path:
    cues: tuple[SubtitleCue, ...] = parse_srt(source)
    out = Path(destination)
    style = style or SubtitleStyle()
    animation = animation or SubtitleAnimationSettings()
    primary = _hex_to_ass(style.fill_color)
    secondary = _hex_to_ass(animation.highlight_color)
    outline = _hex_to_ass(style.outline_color)
    back_alpha = max(0, min(255, 255 - round(style.background_opacity * 2.55)))
    back = _hex_to_ass("#000000", alpha=back_alpha)
    border_style = 3 if style.background_box else 1
    bold = -1 if style.preset_name in {"Dokumenter", "Social"} else 0
    header = f"""[Script Info]\nScriptType: v4.00+\nPlayResX: {width}\nPlayResY: {height}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,{style.font_family},{style.font_size},{primary},{secondary},{outline},{back},{bold},0,0,0,100,100,0,0,{border_style},{style.outline_width},{style.shadow},{style.alignment},80,80,{style.margin_v},1\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"""
    events = [
        f"Dialogue: 0,{_ass_time(c.start_seconds)},{_ass_time(c.end_seconds)},Default,,0,0,0,,{_event_text(c, animation)}"
        for c in cues
    ]
    out.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return out
