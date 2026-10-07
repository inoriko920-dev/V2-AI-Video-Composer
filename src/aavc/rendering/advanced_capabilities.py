from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from aavc.platform.process_runner import ProcessRunner
from aavc.platform.tool_registry import ToolResolution, resolve_ffmpeg


class AdvancedFFmpegFeature(StrEnum):
    DYNAMIC_SPATIAL_ALPHA = "dynamic_spatial_alpha"
    NAMED_GBLUR = "named_gblur"
    SENDCMD_RUNTIME_SIGMA = "sendcmd_runtime_sigma"
    ALPHA_BRANCH = "alpha_branch"
    PREMULTIPLY_ALPHA = "premultiply_alpha"
    OVERLAY_EXPRESSIONS = "overlay_expressions"


@dataclass(frozen=True, slots=True)
class AdvancedFFmpegCapabilities:
    available: bool
    executable_path: str | None
    version: str | None
    fingerprint: str | None
    features: frozenset[AdvancedFFmpegFeature] = frozenset()
    diagnostics: tuple[str, ...] = ()

    def supports(self, feature: AdvancedFFmpegFeature) -> bool:
        return feature in self.features

    def missing(
        self,
        required: frozenset[AdvancedFFmpegFeature],
    ) -> frozenset[AdvancedFFmpegFeature]:
        return required.difference(self.features)


class AdvancedFFmpegCapabilityProbe:
    """K0 scaffold for feature-based FFmpeg capability detection.

    K0 intentionally claims no advanced render features. Later waves add real
    micro-render probes and only then populate the feature set.
    """

    def __init__(
        self,
        *,
        runner: ProcessRunner | None = None,
        resolver: Callable[[], ToolResolution] = resolve_ffmpeg,
    ) -> None:
        self._runner = runner or ProcessRunner()
        self._resolver = resolver
        self._cached: AdvancedFFmpegCapabilities | None = None

    def probe(self) -> AdvancedFFmpegCapabilities:
        if self._cached is not None:
            return self._cached

        try:
            tool = self._resolver()
            result = self._runner.run([tool.path, "-version"], timeout_seconds=10.0)
        except (OSError, RuntimeError) as error:
            self._cached = AdvancedFFmpegCapabilities(
                available=False,
                executable_path=None,
                version=None,
                fingerprint=None,
                diagnostics=(str(error),),
            )
            return self._cached

        if result.returncode != 0:
            self._cached = AdvancedFFmpegCapabilities(
                available=False,
                executable_path=tool.path,
                version=None,
                fingerprint=None,
                diagnostics=(result.stderr[-1000:] or "FFmpeg version probe gagal",),
            )
            return self._cached

        lines = result.stdout.splitlines()
        first_line = lines[0] if lines else ""
        version = first_line.removeprefix("ffmpeg version ").split(" ", 1)[0] or None
        fingerprint = self._fingerprint(tool, first_line)
        self._cached = AdvancedFFmpegCapabilities(
            available=True,
            executable_path=tool.path,
            version=version,
            fingerprint=fingerprint,
            features=frozenset(),
            diagnostics=(
                "K0 capability scaffold aktif; advanced feature micro-probes belum "
                "dipromosikan.",
            ),
        )
        return self._cached

    def invalidate(self) -> None:
        self._cached = None

    def refresh(self) -> AdvancedFFmpegCapabilities:
        self.invalidate()
        return self.probe()

    @staticmethod
    def _fingerprint(tool: ToolResolution, version_line: str) -> str:
        path = Path(tool.path)
        file_identity = "missing"
        try:
            stat = path.stat()
            file_identity = f"{stat.st_size}:{stat.st_mtime_ns}"
        except OSError:
            pass
        payload = "|".join((str(path), tool.source, version_line, file_identity))
        return sha256(payload.encode("utf-8")).hexdigest()
