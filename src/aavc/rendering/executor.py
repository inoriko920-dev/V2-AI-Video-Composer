from __future__ import annotations

import os
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


def execute_ffmpeg(
    command: list[str],
    *,
    runner: ProcessRunner | None = None,
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
        if os.name == "nt":
            units = windows_command_units(render_command)
            if units > _WINDOWS_COMMAND_LIMIT:
                raise RenderError(
                    "Perintah FFmpeg masih terlalu panjang untuk Windows "
                    f"({units} > {_WINDOWS_COMMAND_LIMIT} UTF-16 units). "
                    "Pendekkan path input/output atau pecah project sebelum render."
                )

        completed = process_runner.run(render_command)
        if (
            completed.returncode != 0
            or not temporary.exists()
            or temporary.stat().st_size == 0
        ):
            raise RenderError(
                completed.stderr[-4000:] or "FFmpeg gagal tanpa pesan error"
            )

        try:
            temporary.replace(output)
        except OSError as error:
            raise RenderError(
                f"Gagal menyelesaikan file output render: {error}"
            ) from error

        return RenderResult(
            str(output),
            completed.returncode,
            completed.stderr[-2000:],
        )
    finally:
        graph_path.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)
