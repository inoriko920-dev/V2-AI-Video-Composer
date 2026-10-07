from __future__ import annotations

from pathlib import Path

from aavc.animation.compiler import (
    assignment_has_native_motion,
    compile_motion_overlay_position,
    compile_native_alpha_filters,
    compile_native_rotation_filter,
    compile_native_scale_filter,
)
from aavc.animation.contract import ResolvedAnimationKeyframeContract
from aavc.domain.project.models import AnimationAssignment

from .advanced_filters import (
    assignment_has_k4_glow,
    assignment_has_k4_shadow,
    compile_k1_opacity_filters,
    compile_k2_crop_filters,
    compile_k3_blur_filters,
    compile_k4_shadow_glow_clauses,
    compile_k5_mask_filters,
)
from .render_plan import RenderPlan, SceneRenderPlan


def _escape_filter_level(value: str, special: str) -> str:
    escaped: list[str] = []
    for character in value:
        if character in special:
            escaped.append("\\" + character)
        else:
            escaped.append(character)
    return "".join(escaped)


def _esc_filter_path(path: str) -> str:
    """Escape an ASS filename through option-value and filtergraph parsing."""

    normalized = str(Path(path).resolve()).replace("\\", "/")
    option_value = _escape_filter_level(normalized, "\\':")
    return _escape_filter_level(option_value, "\\'[],;")


def _animation_at(
    scene: SceneRenderPlan,
    asset_index: int,
) -> AnimationAssignment | None:
    if asset_index >= len(scene.animations):
        return None
    return scene.animations[asset_index]


def _scaled_asset_clause(
    *,
    input_index: int,
    output_name: str,
    max_width: int,
    max_height: int,
    scale_flags: str,
    assignment: AnimationAssignment | None,
    duration_seconds: float,
    fps: int,
    canvas_width: int,
    canvas_height: int,
    animation_keyframe_contract: ResolvedAnimationKeyframeContract,
    opacity_instance_id: str,
) -> str:
    base = (
        f"[{input_index}:v]scale=w={max_width}:h={max_height}:"
        f"force_original_aspect_ratio=decrease:flags={scale_flags},"
        "setpts=PTS-STARTPTS"
    )
    clauses: list[str] = []
    crop_filters: tuple[str, ...] = ()
    if animation_keyframe_contract == "advanced-v1":
        crop_filters = compile_k2_crop_filters(
            assignment,
            duration_seconds=duration_seconds,
            instance_id=f"crop_{opacity_instance_id}",
        )
        if crop_filters:
            base += "," + ",".join(crop_filters)

        blur_filters = compile_k3_blur_filters(
            assignment,
            duration_seconds=duration_seconds,
            fps=fps,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            instance_id=f"blur_{opacity_instance_id}",
        )
        if blur_filters:
            base += "," + ",".join(blur_filters)
            if crop_filters:
                post_crop_filters = compile_k2_crop_filters(
                    assignment,
                    duration_seconds=duration_seconds,
                    instance_id=f"crop_post_{opacity_instance_id}",
                )
                base += "," + ",".join(post_crop_filters)

    scale_filter = compile_native_scale_filter(
        assignment,
        duration_seconds=duration_seconds,
    )
    if scale_filter is not None:
        base += "," + scale_filter
    rotation_filter = compile_native_rotation_filter(
        assignment,
        duration_seconds=duration_seconds,
    )
    if rotation_filter is not None:
        base += "," + rotation_filter

    if animation_keyframe_contract == "advanced-v1":
        mask_filters = compile_k5_mask_filters(
            assignment,
            duration_seconds=duration_seconds,
            instance_id=f"mask_{opacity_instance_id}",
        )
        if mask_filters:
            base += "," + ",".join(mask_filters)

    if (
        animation_keyframe_contract == "advanced-v1"
        and (
            assignment_has_k4_shadow(assignment)
            or assignment_has_k4_glow(assignment)
        )
    ):
        pre_k4 = f"{output_name}_pre_k4"
        post_k4 = f"{output_name}_post_k4"
        clauses.append(f"{base},format=rgba[{pre_k4}]")
        clauses.extend(
            compile_k4_shadow_glow_clauses(
                pre_k4,
                post_k4,
                assignment,
                duration_seconds=duration_seconds,
                fps=fps,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
                instance_id=f"k4_{opacity_instance_id}",
            )
        )
        base = f"[{post_k4}]null"

    alpha_filters = compile_native_alpha_filters(
        assignment,
        duration_seconds=duration_seconds,
    )
    if alpha_filters:
        base += "," + ",".join(alpha_filters)
    if animation_keyframe_contract == "advanced-v1":
        opacity_filters = compile_k1_opacity_filters(
            assignment,
            duration_seconds=duration_seconds,
            instance_id=opacity_instance_id,
        )
        if opacity_filters:
            base += "," + ",".join(opacity_filters)
    clauses.append(f"{base}[{output_name}]")
    return ";".join(clauses)


def _overlay_clause(
    *,
    base_x: str,
    base_y: str,
    assignment: AnimationAssignment | None,
    duration_seconds: float,
) -> str:
    if not assignment_has_native_motion(assignment):
        return f"overlay=x={base_x}:y={base_y}:shortest=1"
    x_expr, y_expr = compile_motion_overlay_position(
        base_x=base_x,
        base_y=base_y,
        assignment=assignment,
        duration_seconds=duration_seconds,
    )
    return f"overlay=x='{x_expr}':y='{y_expr}':shortest=1"


def build_ffmpeg_command(plan: RenderPlan, ffmpeg: str = "ffmpeg") -> list[str]:
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "warning"]
    asset_input_indices: list[tuple[int, ...]] = []
    input_index = 0
    for scene in plan.scenes:
        indices: list[int] = []
        for asset in scene.asset_paths:
            cmd += ["-loop", "1", "-framerate", str(plan.fps), "-i", asset]
            indices.append(input_index)
            input_index += 1
        asset_input_indices.append(tuple(indices))

    audio_index: int | None = None
    if plan.narration_audio:
        audio_index = input_index
        cmd += ["-i", plan.narration_audio]

    filters: list[str] = []
    scene_outputs: list[str] = []
    scale_flags = plan.quality.scale_algorithm
    for sidx, (scene, scene_indices) in enumerate(
        zip(plan.scenes, asset_input_indices, strict=True)
    ):
        duration = scene.duration_seconds
        bg = f"bg{sidx}"
        filters.append(
            f"color=c=0xF4F7FB:s={plan.width}x{plan.height}:r={plan.fps}:d={duration}[{bg}]"
        )
        if len(scene_indices) == 1:
            inp = scene_indices[0]
            scaled = f"sc{sidx}_0"
            max_h = int(plan.height * 0.84)
            max_w = int(plan.width * 0.72)
            assignment = _animation_at(scene, 0)
            filters.append(
                _scaled_asset_clause(
                    input_index=inp,
                    output_name=scaled,
                    max_width=max_w,
                    max_height=max_h,
                    scale_flags=scale_flags,
                    assignment=assignment,
                    duration_seconds=duration,
                    fps=plan.fps,
                    canvas_width=plan.width,
                    canvas_height=plan.height,
                    animation_keyframe_contract=plan.animation_keyframe_contract,
                    opacity_instance_id=f"opacity_{sidx}_0",
                )
            )
            out = f"scene{sidx}"
            fade_out_start = max(0.0, duration - 0.25)
            overlay = _overlay_clause(
                base_x="(W-w)/2",
                base_y="(H-h)/2",
                assignment=assignment,
                duration_seconds=duration,
            )
            filters.append(
                f"[{bg}][{scaled}]{overlay},"
                f"fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out_start:.3f}:d=0.25[{out}]"
            )
        else:
            max_w = int(plan.width * 0.46)
            max_h = int(plan.height * 0.66)
            scaled_names: list[str] = []
            for aidx, inp in enumerate(scene_indices):
                scaled = f"sc{sidx}_{aidx}"
                scaled_names.append(scaled)
                filters.append(
                    _scaled_asset_clause(
                        input_index=inp,
                        output_name=scaled,
                        max_width=max_w,
                        max_height=max_h,
                        scale_flags=scale_flags,
                        assignment=_animation_at(scene, aidx),
                        duration_seconds=duration,
                        fps=plan.fps,
                        canvas_width=plan.width,
                        canvas_height=plan.height,
                        animation_keyframe_contract=plan.animation_keyframe_contract,
                        opacity_instance_id=f"opacity_{sidx}_{aidx}",
                    )
                )
            tmp = f"tmp{sidx}"
            out = f"scene{sidx}"
            first_overlay = _overlay_clause(
                base_x="W/2-w-12",
                base_y="(H-h)/2",
                assignment=_animation_at(scene, 0),
                duration_seconds=duration,
            )
            filters.append(
                f"[{bg}][{scaled_names[0]}]{first_overlay}[{tmp}]"
            )
            fade_out_start = max(0.0, duration - 0.25)
            second_overlay = _overlay_clause(
                base_x="W/2+12",
                base_y="(H-h)/2",
                assignment=_animation_at(scene, 1),
                duration_seconds=duration,
            )
            filters.append(
                f"[{tmp}][{scaled_names[1]}]{second_overlay},"
                f"fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out_start:.3f}:d=0.25[{out}]"
            )
        scene_outputs.append(f"[{out}]")

    concat_out = "vcat"
    filters.append(
        "".join(scene_outputs)
        + f"concat=n={len(scene_outputs)}:v=1:a=0[{concat_out}]"
    )
    final_video = concat_out
    if plan.subtitle_ass:
        final_video = "vsub"
        filters.append(
            f"[{concat_out}]ass=filename={_esc_filter_path(plan.subtitle_ass)}[{final_video}]"
        )

    sharpen = max(0.0, min(1.0, plan.quality.sharpen_amount))
    if sharpen > 0:
        sharpened = "vsharp"
        amount = 0.5 + sharpen * 0.8
        filters.append(
            f"[{final_video}]unsharp=5:5:{amount:.3f}:5:5:0[{sharpened}]"
        )
        final_video = sharpened

    cmd += ["-filter_complex", ";".join(filters), "-map", f"[{final_video}]"]
    if audio_index is not None:
        cmd += [
            "-map",
            f"{audio_index}:a:0",
            "-c:a",
            "aac",
            "-b:a",
            f"{plan.quality.audio_bitrate_kbps}k",
        ]
    cmd += [
        "-t",
        f"{plan.duration_seconds:.3f}",
        "-r",
        str(plan.fps),
        "-c:v",
        plan.quality.video_codec,
        "-preset",
        plan.quality.encoder_preset,
        "-crf",
        str(plan.quality.crf),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        plan.output_path,
    ]
    return cmd
