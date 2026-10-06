from collections.abc import Sequence
from pathlib import Path

from aavc.domain.project.models import RenderQualitySettings
from aavc.platform.process_runner import ProcessResult, ProcessRunner, windows_command_units
from aavc.rendering.executor import execute_ffmpeg
from aavc.rendering.ffmpeg_builder import build_ffmpeg_command
from aavc.rendering.render_plan import RenderPlan, SceneRenderPlan


class CapturingRunner(ProcessRunner):
    def __init__(self) -> None:
        self.command: list[str] | None = None
        self.graph: str | None = None
        self.graph_path: Path | None = None

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del timeout_seconds
        self.command = list(argv)
        graph_index = self.command.index("-/filter_complex") + 1
        self.graph_path = Path(self.command[graph_index])
        self.graph = self.graph_path.read_text(encoding="utf-8")
        Path(self.command[-1]).write_bytes(b"fake-mp4")
        return ProcessResult(0, "", "")


def test_large_filter_graph_is_moved_out_of_process_command(tmp_path: Path) -> None:
    output = tmp_path / "large.mp4"
    huge_graph = "null[v0];" + ("[v0]null[v0];" * 6000)
    command = [
        "ffmpeg",
        "-filter_complex",
        huge_graph,
        "-map",
        "[v0]",
        str(output),
    ]
    assert windows_command_units(command) > 32767

    runner = CapturingRunner()
    result = execute_ffmpeg(command, runner=runner)

    assert result.output_path == str(output)
    assert runner.command is not None
    assert "-filter_complex" not in runner.command
    assert "-/filter_complex" in runner.command
    assert windows_command_units(runner.command) < 32767
    assert runner.graph == huge_graph
    assert runner.graph_path is not None
    assert not runner.graph_path.exists()
    assert output.read_bytes() == b"fake-mp4"


def test_ass_path_is_escaped_for_two_filtergraph_levels(tmp_path: Path) -> None:
    subtitle = tmp_path / "Toni's video" / "sub,title[1];final.ass"
    scene = SceneRenderPlan(
        scene_number=1,
        duration_seconds=1.0,
        asset_paths=(str(tmp_path / "asset.png"),),
        placements=(),
        animations=(),
    )
    plan = RenderPlan(
        width=320,
        height=180,
        fps=30,
        scenes=(scene,),
        narration_audio=None,
        subtitle_ass=str(subtitle),
        output_path=str(tmp_path / "out.mp4"),
        quality=RenderQualitySettings(sharpen_amount=0.0),
    )

    command = build_ffmpeg_command(plan)
    graph = command[command.index("-filter_complex") + 1]

    assert "ass=filename=" in graph
    assert "Toni\\\\\\'s video" in graph
    assert "sub\\,title\\[1\\]\\;final.ass" in graph
