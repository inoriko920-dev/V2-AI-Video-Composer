from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from aavc.application.services.export_service import ExportOptions, render_project
from aavc.application.services.selection_export_service import render_project_selection
from aavc.application.services.vertical_slice import create_project_state
from aavc.domain.errors import RenderError
from aavc.domain.project.models import ProjectState
from aavc.platform.process_runner import ProcessResult, ProcessRunner

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
        Path(command[-1]).write_bytes(b"fake-mp4")
        return ProcessResult(0, "", "")


class FailingRunner(ProcessRunner):
    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del timeout_seconds
        command = list(argv)
        Path(command[-1]).write_bytes(b"partial-output")
        return ProcessResult(1, "", "ffmpeg failed")


def _project() -> ProjectState:
    return create_project_state(
        title="export-demo",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )


def test_render_project_maps_options_into_ffmpeg_command(tmp_path: Path) -> None:
    output = tmp_path / "video.mp4"
    runner = FakeRunner()
    options = ExportOptions(
        output_path=str(output),
        video_codec="libx265",
        encoder_preset="slow",
        crf=20,
        width=1280,
        height=720,
        fps=60,
        sharpen_amount=0.10,
        burn_subtitles=False,
    )

    result = render_project(_project(), options, ffmpeg="fake-ffmpeg", runner=runner)

    assert result.output_path == str(output.resolve())
    assert output.read_bytes() == b"fake-mp4"
    command = runner.commands[0]
    assert command[0] == "fake-ffmpeg"
    assert command[command.index("-c:v") + 1] == "libx265"
    assert command[command.index("-preset") + 1] == "slow"
    assert command[command.index("-crf") + 1] == "20"
    assert command[command.index("-r") + 1] == "60"
    assert "-/filter_complex" in command
    assert "s=1280x720" in runner.filter_graphs[0]


def test_render_project_uses_temporary_subtitle_ass_without_clobbering_sidecar(
    tmp_path: Path,
) -> None:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHalo dunia\n",
        encoding="utf-8",
    )
    project = replace(_project(), subtitle_source=str(subtitle))
    output = tmp_path / "with-subtitle.mp4"
    user_sidecar = output.with_suffix(".subtitle.ass")
    user_sidecar.write_text("user-owned", encoding="utf-8")
    runner = FakeRunner()

    render_project(
        project,
        ExportOptions(output_path=str(output), burn_subtitles=True),
        ffmpeg="fake-ffmpeg",
        runner=runner,
        verify_output=False,
    )

    filters = runner.filter_graphs[0]
    assert "ass=filename=" in filters
    assert ".aavc-subtitle-" in filters
    assert user_sidecar.read_text(encoding="utf-8") == "user-owned"
    assert list(tmp_path.glob(".*.aavc-subtitle-*.ass")) == []


def test_render_project_cleans_subtitle_staging_when_ffmpeg_fails(tmp_path: Path) -> None:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHalo dunia\n",
        encoding="utf-8",
    )
    project = replace(_project(), subtitle_source=str(subtitle))
    output = tmp_path / "failed.mp4"
    user_sidecar = output.with_suffix(".subtitle.ass")
    user_sidecar.write_text("keep-me", encoding="utf-8")

    with pytest.raises(RenderError, match="ffmpeg failed"):
        render_project(
            project,
            ExportOptions(output_path=str(output), burn_subtitles=True),
            ffmpeg="fake-ffmpeg",
            runner=FailingRunner(),
            verify_output=False,
        )

    assert user_sidecar.read_text(encoding="utf-8") == "keep-me"
    assert list(tmp_path.glob(".*.aavc-subtitle-*.ass")) == []


def test_selection_export_also_cleans_subtitle_staging(tmp_path: Path) -> None:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHalo dunia\n",
        encoding="utf-8",
    )
    project = replace(_project(), subtitle_source=str(subtitle))
    output = tmp_path / "selection.mp4"
    user_sidecar = output.with_suffix(".subtitle.ass")
    user_sidecar.write_text("selection-user-owned", encoding="utf-8")
    runner = FakeRunner()

    render_project_selection(
        project,
        ExportOptions(output_path=str(output), burn_subtitles=True),
        start_seconds=0.0,
        end_seconds=1.0,
        ffmpeg="fake-ffmpeg",
        runner=runner,
        verify_output=False,
    )

    filters = runner.filter_graphs[0]
    assert ".aavc-subtitle-" in filters
    assert user_sidecar.read_text(encoding="utf-8") == "selection-user-owned"
    assert list(tmp_path.glob(".*.aavc-subtitle-*.ass")) == []


def test_render_project_stops_on_preflight_error(tmp_path: Path) -> None:
    runner = FakeRunner()
    options = ExportOptions(output_path=str(tmp_path / "bad.mp4"), width=0)

    with pytest.raises(RenderError, match="Resolusi render tidak valid"):
        render_project(_project(), options, ffmpeg="fake-ffmpeg", runner=runner)

    assert runner.commands == []


class FakeProbeRunner(ProcessRunner):
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        del argv, timeout_seconds
        return ProcessResult(0, self.payload, "")


def test_render_project_validates_output_before_finalize(tmp_path: Path) -> None:
    project = _project()
    duration = sum(scene.duration_seconds for scene in project.scenes)
    output = tmp_path / "verified.mp4"
    runner = FakeRunner()
    probe = FakeProbeRunner(
        '{"streams":[{"codec_type":"video","width":1920,"height":1080,'
        '"r_frame_rate":"30/1"}],"format":{"duration":"'
        + f"{duration:.3f}"
        + '"}}'
    )

    result = render_project(
        project,
        ExportOptions(output_path=str(output), burn_subtitles=False),
        ffmpeg="fake-ffmpeg",
        ffprobe="fake-ffprobe",
        runner=runner,
        probe_runner=probe,
    )

    assert result.output_path == str(output.resolve())
    assert output.read_bytes() == b"fake-mp4"
