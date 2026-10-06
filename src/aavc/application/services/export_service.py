from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4

from aavc.domain.errors import RenderError
from aavc.domain.project.models import ProjectState
from aavc.platform.process_runner import ProcessRunner
from aavc.platform.tool_registry import resolve_ffmpeg
from aavc.rendering import (
    RenderResult,
    build_ffmpeg_command,
    build_render_plan,
    execute_ffmpeg,
    validate_render_plan,
)
from aavc.subtitles import compile_srt_to_ass


@dataclass(frozen=True, slots=True)
class ExportOptions:
    output_path: str
    video_codec: str = "libx264"
    encoder_preset: str = "medium"
    crf: int = 18
    width: int = 1920
    height: int = 1080
    fps: int = 30
    sharpen_amount: float = 0.18
    burn_subtitles: bool = True


def subtitle_staging_path(output: str | Path) -> Path:
    final_output = Path(output).resolve()
    return final_output.with_name(
        f".{final_output.stem}.aavc-subtitle-{uuid4().hex}.ass"
    )


def render_project(
    project: ProjectState,
    options: ExportOptions,
    *,
    ffmpeg: str | None = None,
    runner: ProcessRunner | None = None,
) -> RenderResult:
    """Render one ProjectState using the canonical FFmpeg pipeline."""

    output = Path(options.output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    quality = replace(
        project.render_quality,
        video_codec=options.video_codec,
        encoder_preset=options.encoder_preset,
        crf=options.crf,
        sharpen_amount=options.sharpen_amount,
    )
    export_project = replace(
        project,
        width=options.width,
        height=options.height,
        fps=options.fps,
        render_quality=quality,
    )

    subtitle_ass: Path | None = None
    try:
        if options.burn_subtitles and project.subtitle_source:
            subtitle_ass = subtitle_staging_path(output)
            compile_srt_to_ass(
                project.subtitle_source,
                subtitle_ass,
                width=options.width,
                height=options.height,
                style=project.subtitle_style,
                animation=project.subtitle_animation,
            )

        plan = build_render_plan(
            export_project,
            output,
            str(subtitle_ass) if subtitle_ass is not None else None,
        )
        preflight = validate_render_plan(plan)
        errors = [
            issue.message for issue in preflight.issues if issue.severity.value == "ERROR"
        ]
        if errors:
            raise RenderError(f"Render preflight gagal: {'; '.join(errors)}")

        ffmpeg_path = ffmpeg or resolve_ffmpeg().path
        command = build_ffmpeg_command(plan, ffmpeg=ffmpeg_path)
        return execute_ffmpeg(command, runner=runner)
    finally:
        if subtitle_ass is not None:
            subtitle_ass.unlink(missing_ok=True)
