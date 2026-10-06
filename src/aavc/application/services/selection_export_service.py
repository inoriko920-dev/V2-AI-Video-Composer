from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from aavc.application.services.export_service import ExportOptions, subtitle_staging_path
from aavc.domain.errors import RenderError
from aavc.domain.project.models import ProjectState
from aavc.jobs import CancellationToken
from aavc.platform.process_runner import ProcessRunner
from aavc.platform.tool_registry import resolve_ffmpeg, resolve_ffprobe
from aavc.rendering import (
    RenderManifest,
    RenderResult,
    build_render_plan,
    execute_ffmpeg,
    validate_render_plan,
    verify_render_output,
)
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
    ffprobe: str | None = None,
    runner: ProcessRunner | None = None,
    probe_runner: ProcessRunner | None = None,
    cancellation_token: CancellationToken | None = None,
    progress_callback: Callable[[float], None] | None = None,
    verify_output: bool = True,
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
        manifest = RenderManifest.from_plan(
            plan,
            expected_duration_seconds=selection.duration_seconds,
        )
        validator = None
        if verify_output:
            ffprobe_path = ffprobe or resolve_ffprobe().path
            validation_runner = probe_runner or ProcessRunner()
            validator = lambda candidate: verify_render_output(
                candidate,
                manifest,
                ffprobe=ffprobe_path,
                runner=validation_runner,
            )
        return execute_ffmpeg(
            command,
            runner=runner,
            validator=validator,
            cancel_requested=(
                (lambda: cancellation_token.is_cancelled)
                if cancellation_token is not None
                else None
            ),
            progress_callback=progress_callback,
            expected_duration_seconds=manifest.expected_duration_seconds,
        )
    finally:
        if subtitle_ass is not None:
            subtitle_ass.unlink(missing_ok=True)
