from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from aavc.application.services.export_service import ExportOptions
from aavc.application.services.selection_export_service import render_project_selection
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.errors import RenderError
from aavc.domain.project.models import ProjectState
from aavc.platform.process_runner import ProcessResult, ProcessRunner
from aavc.rendering.selection import RenderSelection, validate_render_selection

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


class FakeRunner(ProcessRunner):
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.filter_graphs: list[str] = []

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del timeout_seconds
        command = list(argv)
        self.commands.append(command)
        if "-/filter_complex" in command:
            graph_path = Path(command[command.index("-/filter_complex") + 1])
            self.filter_graphs.append(graph_path.read_text(encoding="utf-8"))
        Path(command[-1]).write_bytes(b"selection-mp4")
        return ProcessResult(0, "", "")


def _project() -> ProjectState:
    return create_project_state(
        title="selection-export-demo",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def _range(project: ProjectState) -> tuple[float, float]:
    total = sum(scene.duration_seconds for scene in project.scenes)
    return total * 0.2, total * 0.7


def test_validate_render_selection_is_strict_and_reports_duration() -> None:
    selection = validate_render_selection(1.25, 4.75, 10.0)

    assert selection == RenderSelection(1.25, 4.75)
    assert selection.duration_seconds == pytest.approx(3.5)

    with pytest.raises(ValueError, match="durasi lebih dari 0"):
        validate_render_selection(2.0, 2.0, 10.0)
    with pytest.raises(ValueError, match="melewati akhir project"):
        validate_render_selection(2.0, 11.0, 10.0)


def test_render_selection_adds_video_trim_and_output_duration(tmp_path: Path) -> None:
    project = _project()
    start, end = _range(project)
    output = tmp_path / "selection.mp4"
    runner = FakeRunner()

    result = render_project_selection(
        project,
        ExportOptions(output_path=str(output), burn_subtitles=False),
        start_seconds=start,
        end_seconds=end,
        ffmpeg="fake-ffmpeg",
        runner=runner,
    )

    assert result.output_path == str(output.resolve())
    assert output.read_bytes() == b"selection-mp4"
    command = runner.commands[0]
    filters = runner.filter_graphs[0]
    assert f"trim=start={start:.6f}:end={end:.6f}" in filters
    assert "setpts=PTS-STARTPTS[vselection]" in filters
    first_map = command.index("-map")
    assert command[first_map + 1] == "[vselection]"
    assert command[command.index("-t") + 1] == f"{end - start:.3f}"


def test_render_selection_trims_audio_on_same_global_range(tmp_path: Path) -> None:
    project = _project()
    narration = tmp_path / "narration.wav"
    narration.write_bytes(b"placeholder-audio")
    project = replace(project, narration_audio=str(narration))
    start, end = _range(project)
    runner = FakeRunner()

    render_project_selection(
        project,
        ExportOptions(output_path=str(tmp_path / "audio-selection.mp4"), burn_subtitles=False),
        start_seconds=start,
        end_seconds=end,
        ffmpeg="fake-ffmpeg",
        runner=runner,
    )

    command = runner.commands[0]
    filters = runner.filter_graphs[0]
    assert f"atrim=start={start:.6f}:end={end:.6f}" in filters
    assert "asetpts=PTS-STARTPTS[aselection]" in filters
    map_positions = [index for index, value in enumerate(command) if value == "-map"]
    assert len(map_positions) == 2
    assert command[map_positions[1] + 1] == "[aselection]"


def test_render_selection_burns_subtitles_before_video_trim(tmp_path: Path) -> None:
    project = _project()
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHalo selection\n",
        encoding="utf-8",
    )
    project = replace(project, subtitle_source=str(subtitle))
    start, end = _range(project)
    runner = FakeRunner()

    render_project_selection(
        project,
        ExportOptions(output_path=str(tmp_path / "subtitle-selection.mp4"), burn_subtitles=True),
        start_seconds=start,
        end_seconds=end,
        ffmpeg="fake-ffmpeg",
        runner=runner,
    )

    filters = runner.filter_graphs[0]
    assert "ass=filename=" in filters
    assert filters.index("ass=filename=") < filters.index("trim=start=")


def test_render_selection_rejects_invalid_range_before_execution(tmp_path: Path) -> None:
    project = _project()
    total = sum(scene.duration_seconds for scene in project.scenes)
    runner = FakeRunner()

    with pytest.raises(RenderError, match="Range In/Out render tidak valid"):
        render_project_selection(
            project,
            ExportOptions(output_path=str(tmp_path / "bad-selection.mp4")),
            start_seconds=total,
            end_seconds=total,
            ffmpeg="fake-ffmpeg",
            runner=runner,
        )

    assert runner.commands == []
