from __future__ import annotations

from collections.abc import Callable

from aavc.media import BackendAvailability, BackendCapabilities
from aavc.platform.process_runner import ProcessRunner
from aavc.platform.tool_registry import ToolResolution, resolve_ffmpeg

from .ffmpeg_capabilities import ffmpeg_reference_capabilities


class FFmpegToolCapabilityService:
    """Cached FFmpeg availability/version probe for V2 diagnostics."""

    def __init__(
        self,
        *,
        runner: ProcessRunner | None = None,
        resolver: Callable[[], ToolResolution] = resolve_ffmpeg,
    ) -> None:
        self._runner = runner or ProcessRunner()
        self._resolver = resolver
        self._cached: BackendAvailability | None = None

    def describe_capabilities(self) -> BackendCapabilities:
        return ffmpeg_reference_capabilities()

    def availability(self) -> BackendAvailability:
        if self._cached is not None:
            return self._cached
        try:
            tool = self._resolver()
            result = self._runner.run([tool.path, "-version"], timeout_seconds=10.0)
        except (OSError, RuntimeError) as error:
            self._cached = BackendAvailability(available=False, reason=str(error))
            return self._cached

        if result.returncode != 0:
            self._cached = BackendAvailability(
                available=False,
                reason=result.stderr[-1000:] or "FFmpeg version probe gagal",
            )
            return self._cached

        lines = result.stdout.splitlines()
        first_line = lines[0] if lines else ""
        version = first_line.removeprefix("ffmpeg version ").split(" ", 1)[0] or None
        self._cached = BackendAvailability(available=True, version=version)
        return self._cached

    def refresh(self) -> BackendAvailability:
        self._cached = None
        return self.availability()
