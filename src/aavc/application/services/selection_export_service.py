from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from aavc.application.services.export_service import ExportOptions, subtitle_staging_path
from aavc.domain.errors import RenderError
from aavc.domain.project.models import ProjectState
from aavc.platform.process_runner import ProcessRunner
from aavc.platform.tool_registry import resolve_ffmpeg
from aavc.rendering import RenderResult, build_render_plan, execute_ffmpeg, validate_render_plan
from aavc.rendering.selection import (
    RenderSelection,
    build_ffmpeg_selection_command,
    validate_render_selection,
)
from aavc.subtitles import compile_srt_to_ass


def render_project_selection(
    project: ProjectState,
    options: ExportOptions,
    *,
    start_seconds: float,
    end_seconds: float,
    ffmpeg: str | None = None,
    runner: ProcessRunner | None = None,
) -> RenderResult:
    """Render only a global In/Out range through the canonical render pipeline."""

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

        try:
            selection: RenderSelection = validate_render_selection(
                start_seconds,
                end_seconds,
                plan.duration_seconds,
            )
        except ValueError as error:
            raise RenderError(f"Range In/Out render tidak valid: {error}") from error

        ffmpeg_path = ffmpeg or resolve_ffmpeg().path
        command = build_ffmpeg_selection_command(plan, selection, ffmpeg=ffmpeg_path)
        return execute_ffmpeg(command, runner=runner)
    finally:
        if subtitle_ass is not None:
            subtitle_ass.unlink(missing_ok=True)
