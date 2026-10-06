from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from aavc.domain.errors import RenderError
from aavc.platform.process_runner import ProcessRunner, windows_command_units

_WINDOWS_COMMAND_LIMIT = 32767


@dataclass(frozen=True, slots=True)
class RenderResult:
    output_path: str
    returncode: int
    stderr_tail: str


def _temporary_output_path(output: Path) -> Path:
    return output.with_name(
        f".{output.stem}.aavc-render-{uuid4().hex}{output.suffix}"
    )


def _filter_graph_staging_path(output: Path) -> Path:
    return output.with_name(
        f".{output.stem}.aavc-filter-{uuid4().hex}.txt"
    )


def _externalize_filter_graph(command: list[str], graph_path: Path) -> list[str]:
    try:
        option_index = command.index("-filter_complex")
    except ValueError:
        return list(command)

    graph_index = option_index + 1
    if graph_index >= len(command):
        raise RenderError("Perintah FFmpeg memiliki -filter_complex tanpa graph")

    graph_path.write_text(command[graph_index], encoding="utf-8")
    transformed = list(command)
    transformed[option_index] = "-/filter_complex"
    transformed[graph_index] = str(graph_path)
    return transformed


def _enable_progress_protocol(command: list[str]) -> list[str]:
    if "-progress" in command:
        return list(command)
    return [command[0], "-progress", "pipe:1", "-nostats", *command[1:]]


def _progress_observer(
    *,
    expected_duration_seconds: float,
    callback: Callable[[float], None],
) -> Callable[[str], None]:
    total = max(0.001, expected_duration_seconds)

    def observe(line: str) -> None:
        if line.startswith("out_time_us="):
            try:
                elapsed = int(line.split("=", 1)[1]) / 1_000_000.0
            except ValueError:
                return
            callback(max(0.0, min(0.999, elapsed / total)))
        elif line == "progress=end":
            callback(1.0)

    return observe


def execute_ffmpeg(
    command: list[str],
    *,
    runner: ProcessRunner | None = None,
    validator: Callable[[Path], object] | None = None,
    cancel_requested: Callable[[], bool] | None = None,
    progress_callback: Callable[[float], None] | None = None,
    expected_duration_seconds: float | None = None,
) -> RenderResult:
    if not command:
        raise RenderError("Perintah FFmpeg kosong")

    process_runner = runner or ProcessRunner()
    output = Path(command[-1])
    temporary = _temporary_output_path(output)
    graph_path = _filter_graph_staging_path(output)
    render_command = [*command[:-1], str(temporary)]

    try:
        render_command = _externalize_filter_graph(render_command, graph_path)
        stdout_observer: Callable[[str], None] | None = None
        if progress_callback is not None:
            if expected_duration_seconds is None or expected_duration_seconds <= 0:
                raise RenderError("Durasi expected wajib tersedia untuk progress render")
            progress_callback(0.0)
            render_command = _enable_progress_protocol(render_command)
            stdout_observer = _progress_observer(
                expected_duration_seconds=expected_duration_seconds,
                callback=progress_callback,
            )

        if os.name == "nt":
            units = windows_command_units(render_command)
            if units > _WINDOWS_COMMAND_LIMIT:
                raise RenderError(
                    "Perintah FFmpeg masih terlalu panjang untuk Windows "
                    f"({units} > {_WINDOWS_COMMAND_LIMIT} UTF-16 units). "
                    "Pendekkan path input/output atau pecah project sebelum render."
                )

        if cancel_requested is not None or stdout_observer is not None:
            completed = process_runner.run_managed(
                render_command,
                cancel_requested=cancel_requested,
                stdout_line_callback=stdout_observer,
            )
        else:
            completed = process_runner.run(render_command)

        if (
            completed.returncode != 0
            or not temporary.exists()
            or temporary.stat().st_size == 0
        ):
            raise RenderError(
                completed.stderr[-4000:] or "FFmpeg gagal tanpa pesan error"
            )

        if validator is not None:
            validator(temporary)

        try:
            temporary.replace(output)
        except OSError as error:
            raise RenderError(
                f"Gagal menyelesaikan file output render: {error}"
            ) from error

        if progress_callback is not None:
            progress_callback(1.0)
        return RenderResult(
            str(output),
            completed.returncode,
            completed.stderr[-2000:],
        )
    finally:
        graph_path.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)
