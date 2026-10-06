from pathlib import Path

import pytest

from aavc.presentation.dialogs.export_settings import build_export_options, quality_slider_to_crf


def test_quality_slider_maps_to_crf_range() -> None:
    assert quality_slider_to_crf(0) == 30
    assert quality_slider_to_crf(78) == 18
    assert quality_slider_to_crf(100) == 15
    assert quality_slider_to_crf(999) == 15


def test_build_export_options_maps_supported_controls(tmp_path: Path) -> None:
    options = build_export_options(
        output_directory=str(tmp_path),
        output_name="Final Video",
        format_label="MP4 (H.265)",
        preset_label="Kualitas Tinggi (Rekomendasi)",
        resolution_label="2560 × 1440",
        fps_label="60 fps",
        quality_value=78,
        sharpen_label="Documentary Crisp",
        burn_subtitles=False,
    )

    assert Path(options.output_path) == tmp_path / "Final Video.mp4"
    assert options.video_codec == "libx265"
    assert options.encoder_preset == "slow"
    assert options.crf == 18
    assert (options.width, options.height) == (2560, 1440)
    assert options.fps == 60
    assert options.sharpen_amount == 0.18
    assert not options.burn_subtitles


def test_build_export_options_rejects_blank_output_fields(tmp_path: Path) -> None:
    common = {
        "format_label": "MP4 (H.264)",
        "preset_label": "Documentary Crisp",
        "resolution_label": "1920 × 1080 (Full HD)",
        "fps_label": "30 fps",
        "quality_value": 78,
        "sharpen_label": "Normal",
        "burn_subtitles": True,
    }
    with pytest.raises(ValueError, match="Lokasi output"):
        build_export_options(output_directory="", output_name="video", **common)
    with pytest.raises(ValueError, match="Nama file"):
        build_export_options(output_directory=str(tmp_path), output_name="", **common)
