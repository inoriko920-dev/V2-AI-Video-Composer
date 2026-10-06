from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from aavc.domain.project.models import RenderQualitySettings
from aavc.platform.process_runner import windows_command_units

from .ffmpeg_builder import build_ffmpeg_command
from .render_plan import RenderPlan, SceneRenderPlan


@dataclass(frozen=True, slots=True)
class RenderBenchmarkResult:
    scene_count: int
    command_build_seconds: float
    filter_graph_characters: int
    windows_command_units_before_externalization: int


def build_benchmark_plan(scene_count: int) -> RenderPlan:
    if scene_count < 1:
        raise ValueError("scene_count harus >= 1")
    long_unicode_root = Path(
        "C:/AAVC Benchmark/Toni's Ünicode Project/" + ("nested-folder-" * 8)
    )
    asset = str(long_unicode_root / "A001.png")
    scenes = tuple(
        SceneRenderPlan(
            scene_number=index + 1,
            duration_seconds=0.5,
            asset_paths=(asset,),
            placements=(),
            animations=(),
        )
        for index in range(scene_count)
    )
    return RenderPlan(
        width=1920,
        height=1080,
        fps=30,
        scenes=scenes,
        narration_audio=None,
        subtitle_ass=None,
        output_path=str(long_unicode_root / f"benchmark-{scene_count}.mp4"),
        quality=RenderQualitySettings(sharpen_amount=0.0),
    )


def benchmark_command_build(scene_count: int) -> RenderBenchmarkResult:
    plan = build_benchmark_plan(scene_count)
    started = perf_counter()
    command = build_ffmpeg_command(plan)
    elapsed = perf_counter() - started
    graph = command[command.index("-filter_complex") + 1]
    return RenderBenchmarkResult(
        scene_count=scene_count,
        command_build_seconds=elapsed,
        filter_graph_characters=len(graph),
        windows_command_units_before_externalization=windows_command_units(command),
    )


def benchmark_standard_scene_counts() -> tuple[RenderBenchmarkResult, ...]:
    return tuple(benchmark_command_build(count) for count in (10, 100, 500))
