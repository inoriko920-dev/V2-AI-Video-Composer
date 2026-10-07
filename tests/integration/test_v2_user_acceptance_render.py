from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aavc.animation.registry import effect_names
from aavc.application.services.export_service import ExportOptions
from aavc.application.services.selection_export_service import render_project_selection
from aavc.domain.project.models import (
    AnimationAssignment,
    AssetBinding,
    ProjectState,
    RenderQualitySettings,
    Scene,
)
from aavc.rendering import (
    RenderManifest,
    build_ffmpeg_command,
    build_render_plan,
    execute_ffmpeg,
    validate_render_plan,
    verify_render_output,
)


def _write_ppm(path: Path, *, width: int = 160, height: int = 90) -> None:
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    pixel = bytes((216, 224, 232))
    path.write_bytes(header + pixel * width * height)


def _acceptance_project(tmp_path: Path) -> ProjectState:
    asset = tmp_path / "A001.ppm"
    _write_ppm(asset)

    effects = effect_names()
    scenes = tuple(
        Scene(
            scene_number=index,
            asset_ids=("A001",),
            source_quotes=(f"Acceptance {effect}",),
            duration_seconds=0.55,
        )
        for index, effect in enumerate(effects, start=1)
    )
    animations = tuple(
        AnimationAssignment(
            scene_number=scene.scene_number,
            asset_id="A001",
            enter_effect=effect,
            exit_effect=effect,
            intensity=1.0,
        )
        for scene, effect in zip(scenes, effects, strict=True)
    )
    return ProjectState(
        schema_version=3,
        title="V2 automated user acceptance",
        source_docx="synthetic-acceptance.docx",
        asset_directory=str(tmp_path),
        scenes=scenes,
        bindings=(
            AssetBinding(
                asset_id="A001",
                source_quote="synthetic acceptance asset",
                path=str(asset),
                status="READY",
            ),
        ),
        fps=10,
        width=320,
        height=180,
        animations=animations,
        render_quality=RenderQualitySettings(
            preset_name="Acceptance Fast",
            video_codec="libx264",
            encoder_preset="ultrafast",
            crf=30,
            audio_bitrate_kbps=128,
            scale_algorithm="bilinear",
            sharpen_amount=0.0,
        ),
    )


@pytest.mark.integration
def test_all_21_native_effects_complete_one_real_ffmpeg_render(tmp_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("ffmpeg/ffprobe not available")

    project = _acceptance_project(tmp_path)
    assert len(effect_names()) == 21

    output = tmp_path / "all-21-effects.mp4"
    plan = build_render_plan(project, output)
    report = validate_render_plan(plan)
    assert report.ok
    assert not any(issue.code == "VISUAL_EFFECT_FALLBACK" for issue in report.issues)

    manifest = RenderManifest.from_plan(plan)
    progress: list[float] = []
    result = execute_ffmpeg(
        build_ffmpeg_command(plan, ffmpeg=ffmpeg),
        validator=lambda candidate: verify_render_output(
            candidate,
            manifest,
            ffprobe=ffprobe,
        ),
        progress_callback=progress.append,
        expected_duration_seconds=manifest.expected_duration_seconds,
    )

    assert Path(result.output_path).is_file()
    assert Path(result.output_path).stat().st_size > 1_000
    assert progress
    assert progress[0] == pytest.approx(0.0)
    assert progress[-1] == pytest.approx(1.0)


@pytest.mark.integration
def test_real_selection_in_out_render_succeeds_after_21_effect_project(
    tmp_path: Path,
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("ffmpeg/ffprobe not available")

    project = _acceptance_project(tmp_path)
    output = tmp_path / "selection-in-out.mp4"
    start_seconds = 0.75
    end_seconds = 2.25

    result = render_project_selection(
        project,
        ExportOptions(
            output_path=str(output),
            video_codec="libx264",
            encoder_preset="ultrafast",
            crf=30,
            width=320,
            height=180,
            fps=10,
            sharpen_amount=0.0,
            burn_subtitles=False,
        ),
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )

    assert Path(result.output_path).is_file()
    assert Path(result.output_path).stat().st_size > 1_000
