from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from aavc.platform.process_runner import ProcessRunner
from aavc.platform.tool_registry import ToolResolution, resolve_ffmpeg


class AdvancedFFmpegFeature(StrEnum):
    OPACITY_RUNTIME_ALPHA = "opacity_runtime_alpha"
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
    """Feature-based FFmpeg capability detection for advanced animation waves.

    K1 promotes runtime opacity and K2 promotes dynamic spatial alpha only
    after independent real micro-render probes. Later waves add their own
    proofs without inheriting capability by version.
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
        features: set[AdvancedFFmpegFeature] = set()
        diagnostics: list[str] = []
        try:
            opacity_probe = self._runner.run(
                [
                    tool.path,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=red:s=16x16:r=4:d=0.25",
                    "-vf",
                    (
                        "format=rgba,"
                        "sendcmd=c='0-1 [expr] "
                        "colorchannelmixer@k1_opacity aa 0.5',"
                        "colorchannelmixer@k1_opacity=aa=1"
                    ),
                    "-frames:v",
                    "1",
                    "-f",
                    "null",
                    "-",
                ],
                timeout_seconds=10.0,
            )
        except (OSError, RuntimeError) as error:
            diagnostics.append(
                "K1 opacity runtime-alpha probe gagal: " + str(error)
            )
        else:
            if opacity_probe.returncode == 0:
                features.add(AdvancedFFmpegFeature.OPACITY_RUNTIME_ALPHA)
            else:
                diagnostics.append(
                    "K1 opacity runtime-alpha probe gagal: "
                    + (opacity_probe.stderr[-1000:] or "unknown FFmpeg error")
                )

        try:
            crop_probe = self._runner.run(
                [
                    tool.path,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=red:s=16x16:r=4:d=0.5",
                    "-vf",
                    (
                        "format=rgba,"
                        "sendcmd=c='"
                        "0-0.5 [expr] drawbox@k2_left w W*(0.10+0.10*TI);"
                        "0-0.5 [expr] drawbox@k2_right x "
                        "W*(1-(0.10+0.10*TI))',"
                        "drawbox@k2_left="
                        "x=0:y=0:w=iw*0.10:h=ih:"
                        "color=black@0:t=fill:replace=1,"
                        "drawbox@k2_right="
                        "x=iw*0.90:y=0:w=iw:h=ih:"
                        "color=black@0:t=fill:replace=1"
                    ),
                    "-frames:v",
                    "2",
                    "-f",
                    "null",
                    "-",
                ],
                timeout_seconds=10.0,
            )
        except (OSError, RuntimeError) as error:
            diagnostics.append(
                "K2 dynamic-spatial-alpha probe gagal: " + str(error)
            )
        else:
            if crop_probe.returncode == 0:
                features.add(AdvancedFFmpegFeature.DYNAMIC_SPATIAL_ALPHA)
            else:
                diagnostics.append(
                    "K2 dynamic-spatial-alpha probe gagal: "
                    + (crop_probe.stderr[-1000:] or "unknown FFmpeg error")
                )

        try:
            blur_probe = self._runner.run(
                [
                    tool.path,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    (
                        "color=c=black:s=32x32:r=4:d=1,"
                        "drawbox=x=15:y=15:w=2:h=2:"
                        "color=white:t=fill,format=rgba"
                    ),
                    "-vf",
                    (
                        "premultiply=inplace=1,"
                        "sendcmd=c='"
                        "0-1 [expr] gblur@k3_probe sigma 4*TI;"
                        "0-1 [expr] gblur@k3_probe sigmaV 4*TI',"
                        "gblur@k3_probe=sigma=0:sigmaV=0:steps=2,"
                        "unpremultiply=inplace=1"
                    ),
                    "-frames:v",
                    "4",
                    "-pix_fmt",
                    "rgba",
                    "-f",
                    "framemd5",
                    "-",
                ],
                timeout_seconds=10.0,
            )
        except (OSError, RuntimeError) as error:
            diagnostics.append(
                "K3 runtime-gblur probe gagal: " + str(error)
            )
        else:
            hashes = {
                line.rsplit(",", 1)[-1].strip()
                for line in blur_probe.stdout.splitlines()
                if line and not line.startswith("#") and "," in line
            }
            if blur_probe.returncode == 0 and len(hashes) >= 3:
                features.update(
                    {
                        AdvancedFFmpegFeature.NAMED_GBLUR,
                        AdvancedFFmpegFeature.SENDCMD_RUNTIME_SIGMA,
                        AdvancedFFmpegFeature.PREMULTIPLY_ALPHA,
                    }
                )
            else:
                detail = (
                    blur_probe.stderr[-1000:]
                    or "frame hashes tidak membuktikan perubahan sigma per frame"
                )
                diagnostics.append("K3 runtime-gblur probe gagal: " + detail)

        try:
            k4_probe = self._runner.run(
                [
                    tool.path,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    (
                        "color=c=black@0:s=32x32:r=4:d=1,"
                        "format=rgba,"
                        "drawbox=x=12:y=12:w=8:h=8:"
                        "color=red@1:t=fill:replace=1"
                    ),
                    "-filter_complex",
                    (
                        "[0:v]split=3[k4main][k4blanksrc][k4fxsrc];"
                        "[k4blanksrc]colorchannelmixer=aa=0[k4blank];"
                        "[k4fxsrc]split=2[k4colorsrc][k4alphasrc];"
                        "[k4alphasrc]alphaextract,"
                        "sendcmd=c='"
                        "0-1 [expr] gblur@k4_branch sigma 3*TI;"
                        "0-1 [expr] gblur@k4_branch sigmaV 3*TI',"
                        "gblur@k4_branch=sigma=0:sigmaV=0:steps=2[k4mask];"
                        "[k4colorsrc]lutrgb=r=255:g=255:b=255[k4color];"
                        "[k4color][k4mask]alphamerge,"
                        "sendcmd=c='0-1 [expr] "
                        "colorchannelmixer@k4_gain aa 0.6*TI',"
                        "colorchannelmixer@k4_gain=aa=0[k4layer];"
                        "[k4blank][k4layer]overlay="
                        "x='2*t':y='2*t':eval=frame:shortest=1:format=auto[k4bg];"
                        "[k4bg][k4main]overlay="
                        "x=0:y=0:shortest=1:format=auto[k4out]"
                    ),
                    "-map",
                    "[k4out]",
                    "-frames:v",
                    "4",
                    "-pix_fmt",
                    "rgba",
                    "-f",
                    "framemd5",
                    "-",
                ],
                timeout_seconds=10.0,
            )
        except (OSError, RuntimeError) as error:
            diagnostics.append(
                "K4 alpha-branch/overlay probe gagal: " + str(error)
            )
        else:
            hashes = {
                line.rsplit(",", 1)[-1].strip()
                for line in k4_probe.stdout.splitlines()
                if line and not line.startswith("#") and "," in line
            }
            if k4_probe.returncode == 0 and len(hashes) >= 3:
                features.update(
                    {
                        AdvancedFFmpegFeature.ALPHA_BRANCH,
                        AdvancedFFmpegFeature.OVERLAY_EXPRESSIONS,
                    }
                )
            else:
                detail = (
                    k4_probe.stderr[-1000:]
                    or "frame hashes tidak membuktikan alpha branch dinamis"
                )
                diagnostics.append(
                    "K4 alpha-branch/overlay probe gagal: " + detail
                )

        self._cached = AdvancedFFmpegCapabilities(
            available=True,
            executable_path=tool.path,
            version=version,
            fingerprint=fingerprint,
            features=frozenset(features),
            diagnostics=tuple(diagnostics),
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
