from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from aavc.domain.project.models import ProjectState
from aavc.importing.assets import bind_assets
from aavc.importing.docx_scene import parse_scene_docx
from aavc.persistence.serializer import save_project
from aavc.platform.tool_registry import resolve_ffmpeg
from aavc.rendering import (
    build_ffmpeg_command,
    build_render_plan,
    execute_ffmpeg,
    validate_render_plan,
)
from aavc.subtitles import compile_srt_to_ass


def create_project_state(
    *,
    title: str,
    scene_docx: str | Path,
    asset_directory: str | Path,
    narration_audio: str | Path | None = None,
    subtitle_srt: str | Path | None = None,
    default_scene_duration: float = 3.0,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
) -> ProjectState:
    scenes = parse_scene_docx(scene_docx, default_duration_seconds=default_scene_duration)
    bindings = bind_assets(scenes, asset_directory)
    return ProjectState(
        schema_version=2,
        title=title,
        source_docx=str(Path(scene_docx).resolve()),
        asset_directory=str(Path(asset_directory).resolve()),
        scenes=scenes,
        bindings=bindings,
        narration_audio=str(Path(narration_audio).resolve()) if narration_audio else None,
        subtitle_source=str(Path(subtitle_srt).resolve()) if subtitle_srt else None,
        width=width,
        height=height,
        fps=fps,
        metadata={
            "vertical_slice": "STEP10",
            "feature_wave": "STEP11",
            "hardening": "STEP13",
            "release": "STEP15",
        },
    )


def run_vertical_slice(
    *,
    title: str,
    scene_docx: str | Path,
    asset_directory: str | Path,
    output_directory: str | Path,
    narration_audio: str | Path | None = None,
    subtitle_srt: str | Path | None = None,
    ffmpeg: str | None = None,
    default_scene_duration: float = 3.0,
) -> dict[str, str]:
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    project = create_project_state(
        title=title,
        scene_docx=scene_docx,
        asset_directory=asset_directory,
        narration_audio=narration_audio,
        subtitle_srt=subtitle_srt,
        default_scene_duration=default_scene_duration,
    )
    if not project.ready:
        not_ready = [binding.asset_id for binding in project.bindings if binding.status != "READY"]
        raise ValueError(f"Asset belum READY: {', '.join(not_ready)}")

    project_path = save_project(project, output_dir / "step10_demo.aavcproj")
    ass_path: Path | None = None
    if subtitle_srt:
        ass_path = compile_srt_to_ass(
            subtitle_srt,
            output_dir / "step10_demo.ass",
            width=project.width,
            height=project.height,
            style=project.subtitle_style,
            animation=project.subtitle_animation,
        )
    render_plan = build_render_plan(
        project,
        output_dir / "step10_demo.mp4",
        str(ass_path) if ass_path else None,
    )
    preflight = validate_render_plan(render_plan)
    if not preflight.ok:
        errors = [issue.message for issue in preflight.issues if issue.severity.value == "ERROR"]
        raise ValueError(f"Render preflight gagal: {'; '.join(errors)}")

    plan_path = output_dir / "render_plan.json"
    plan_path.write_text(
        json.dumps(asdict(render_plan), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    ffmpeg_path = ffmpeg or resolve_ffmpeg().path
    command = build_ffmpeg_command(render_plan, ffmpeg=ffmpeg_path)
    command_path = output_dir / "ffmpeg_command.txt"
    command_path.write_text(" ".join(command), encoding="utf-8")
    result = execute_ffmpeg(command)
    return {
        "project": str(project_path),
        "ass": str(ass_path) if ass_path else "",
        "render_plan": str(plan_path),
        "ffmpeg_command": str(command_path),
        "video": result.output_path,
    }
