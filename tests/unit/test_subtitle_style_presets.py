from aavc.subtitles import STYLE_PRESETS, get_style_preset


def test_official_subtitle_style_presets_are_available() -> None:
    assert tuple(STYLE_PRESETS) == ("Clean", "Dokumenter", "Cinematic", "Social")


def test_official_subtitle_style_presets_have_render_safe_values() -> None:
    for name in STYLE_PRESETS:
        style = get_style_preset(name)
        assert style.preset_name == name
        assert style.font_family.strip()
        assert 1 <= style.font_size <= 400
        assert style.fill_color.startswith("#") and len(style.fill_color) == 7
        assert style.outline_color.startswith("#") and len(style.outline_color) == 7
        assert 0 <= style.outline_width <= 20
        assert 0 <= style.shadow <= 20
        assert 0 <= style.background_opacity <= 100
        assert 1 <= style.alignment <= 9
        assert 0 <= style.margin_v <= 5000
