from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4

from aavc.domain.errors import RenderError
from aavc.domain.project.models import ProjectState
from aavc.jobs import CancellationToken
from aavc.platform.process_runner import ProcessRunner
from aavc.platform.tool_registry import ToolResolution, resolve_ffmpeg, resolve_ffprobe
from aavc.rendering import (
    RenderManifest,
    RenderResult,
    build_ffmpeg_command,
    build_render_plan,
    execute_ffmpeg,
    validate_render_plan,
    verify_render_output,
)
from aavc.rendering.advanced_capabilities import (
    AdvancedFFmpegCapabilityProbe,
    AdvancedFFmpegFeature,
)
from aavc.rendering.advanced_filters import (
    render_plan_requires_k1_opacity,
    render_plan_requires_k2_crop,
)
from aavc.rendering.render_plan import RenderPlan
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


def ensure_advanced_render_capabilities(
    plan: RenderPlan,
    *,
    ffmpeg_path: str,
    runner: ProcessRunner | None = None,
) -> None:
    required: set[AdvancedFFmpegFeature] = set()
    if render_plan_requires_k1_opacity(plan):
        required.add(AdvancedFFmpegFeature.OPACITY_RUNTIME_ALPHA)
    if render_plan_requires_k2_crop(plan):
        required.add(AdvancedFFmpegFeature.DYNAMIC_SPATIAL_ALPHA)
    if not required:
        return

    capabilities = AdvancedFFmpegCapabilityProbe(
        runner=runner,
        resolver=lambda: ToolResolution(
            name="ffmpeg",
            path=ffmpeg_path,
            source="render",
        ),
    ).probe()
    missing = capabilities.missing(frozenset(required))
    if not missing:
        return

    missing_names = ", ".join(sorted(feature.value for feature in missing))
    detail = "; ".join(capabilities.diagnostics) or "capability probe gagal"
    raise RenderError(
        "ADVANCED_BACKEND_UNAVAILABLE: capability advanced-v1 tidak siap "
        f"({missing_names}): {detail}"
    )


def render_project(
    project: ProjectState,
    options: ExportOptions,
    *,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
    runner: ProcessRunner | None = None,
    probe_runner: ProcessRunner | None = None,
    capability_runner: ProcessRunner | None = None,
    cancellation_token: CancellationToken | None = None,
    progress_callback: Callable[[float], None] | None = None,
    verify_output: bool = True,
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
        ensure_advanced_render_capabilities(
            plan,
            ffmpeg_path=ffmpeg_path,
            runner=capability_runner,
        )
        command = build_ffmpeg_command(plan, ffmpeg=ffmpeg_path)
        manifest = RenderManifest.from_plan(plan)
        validator = None
        if verify_output:
            ffprobe_path = ffprobe or resolve_ffprobe().path
            validation_runner = probe_runner or ProcessRunner()
            def validator(candidate: Path) -> object:
                return verify_render_output(
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
