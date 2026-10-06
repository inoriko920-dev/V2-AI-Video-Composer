from __future__ import annotations

import shutil
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path


class ToolNotFoundError(RuntimeError):
    """Raised when a required external media tool cannot be resolved safely."""


@dataclass(frozen=True, slots=True)
class ToolResolution:
    name: str
    path: str
    source: str


def _default_tool_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    if getattr(sys, "frozen", False):
        roots.append(Path(sys.executable).resolve().parent / "tools" / "ffmpeg")
    repository_root = Path(__file__).resolve().parents[3]
    roots.append(repository_root / "tools" / "ffmpeg")
    roots.append(Path.cwd() / "tools" / "ffmpeg")
    return tuple(dict.fromkeys(roots))


def resolve_media_tool(
    name: str,
    *,
    extra_roots: Iterable[str | Path] = (),
    which: Callable[[str], str | None] = shutil.which,
) -> ToolResolution:
    """Resolve ffmpeg/ffprobe from app-local slots first, then the system PATH.

    Final release intentionally does not redistribute FFmpeg. Users may place an
    approved build in ``tools/ffmpeg`` next to the portable application, or make
    the executable available on PATH. The resolver never downloads a binary.
    """

    executable_names = (f"{name}.exe", name)
    roots = tuple(Path(root) for root in extra_roots) + _default_tool_roots()
    for root in roots:
        for executable in executable_names:
            candidate = (root / executable).resolve()
            if candidate.is_file():
                return ToolResolution(name=name, path=str(candidate), source="app-local")

    system_path = which(name)
    if system_path:
        return ToolResolution(
            name=name,
            path=str(Path(system_path).resolve()),
            source="system-path",
        )

    raise ToolNotFoundError(
        f"{name} tidak ditemukan. Letakkan {name}.exe di tools/ffmpeg pada folder "
        "aplikasi atau tambahkan instalasi FFmpeg yang sesuai lisensi ke PATH."
    )


def resolve_ffmpeg(*, extra_roots: Iterable[str | Path] = ()) -> ToolResolution:
    return resolve_media_tool("ffmpeg", extra_roots=extra_roots)


def resolve_ffprobe(*, extra_roots: Iterable[str | Path] = ()) -> ToolResolution:
    return resolve_media_tool("ffprobe", extra_roots=extra_roots)
