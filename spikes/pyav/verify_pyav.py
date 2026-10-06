from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


PYAV_VERSION = "19.0.1"
MAX_IMPORT_SECONDS = 5.0
MAX_ROUNDTRIP_SECONDS = 10.0
MAX_INSTALLED_BYTES = 250 * 1024 * 1024


def _distribution_size_bytes(distribution_name: str) -> int:
    distribution = importlib.metadata.distribution(distribution_name)
    total = 0
    for entry in distribution.files or ():
        path = Path(distribution.locate_file(entry))
        if path.is_file():
            total += path.stat().st_size
    return total


def _license_expression(distribution_name: str) -> str:
    metadata = importlib.metadata.metadata(distribution_name)
    return (
        metadata.get("License-Expression")
        or metadata.get("License")
        or ""
    ).strip()


def _make_sample_video(av: Any, path: Path) -> dict[str, Any]:
    encode_started = time.perf_counter()
    output = av.open(str(path), mode="w")
    stream = output.add_stream("mpeg4", rate=24)
    stream.width = 64
    stream.height = 64
    stream.pix_fmt = "yuv420p"

    for frame_index in range(3):
        frame = av.VideoFrame(64, 64, format="yuv420p")
        values = (32 + frame_index * 24, 128, 128)
        for plane, value in zip(frame.planes, values, strict=False):
            plane.update(bytes([value]) * plane.buffer_size)
        frame.pts = frame_index
        for packet in stream.encode(frame):
            output.mux(packet)

    for packet in stream.encode():
        output.mux(packet)
    output.close()
    encode_seconds = time.perf_counter() - encode_started

    decode_started = time.perf_counter()
    with av.open(str(path), mode="r") as opened:
        video_stream = opened.streams.video[0]
        decoded = list(opened.decode(video=0))
        metadata = {
            "codec": video_stream.codec_context.name,
            "width": video_stream.codec_context.width,
            "height": video_stream.codec_context.height,
            "frames_decoded": len(decoded),
        }
    decode_seconds = time.perf_counter() - decode_started

    metadata["encode_seconds"] = encode_seconds
    metadata["decode_seconds"] = decode_seconds
    metadata["file_bytes"] = path.stat().st_size
    return metadata


def run_probe() -> dict[str, Any]:
    import_started = time.perf_counter()
    import av
    import_seconds = time.perf_counter() - import_started

    installed_bytes = _distribution_size_bytes("av")
    license_expression = _license_expression("av")

    with tempfile.TemporaryDirectory(prefix="aavc-pyav-spike-") as temporary:
        sample_path = Path(temporary) / "sample.mp4"
        media = _make_sample_video(av, sample_path)

    roundtrip_seconds = float(media["encode_seconds"]) + float(media["decode_seconds"])
    library_versions = {
        name: ".".join(str(part) for part in version)
        for name, version in av.library_versions.items()
    }

    result = {
        "candidate": "PyAV",
        "version": str(av.__version__),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "license_expression": license_expression,
        "import_seconds": import_seconds,
        "roundtrip_seconds": roundtrip_seconds,
        "installed_bytes": installed_bytes,
        "media": media,
        "ffmpeg_libraries": library_versions,
        "thresholds": {
            "max_import_seconds": MAX_IMPORT_SECONDS,
            "max_roundtrip_seconds": MAX_ROUNDTRIP_SECONDS,
            "max_installed_bytes": MAX_INSTALLED_BYTES,
        },
    }

    failures: list[str] = []
    if str(av.__version__) != PYAV_VERSION:
        failures.append(f"expected PyAV {PYAV_VERSION}, got {av.__version__}")
    if not sys.version_info[:2] == (3, 12):
        failures.append(f"expected Python 3.12, got {platform.python_version()}")
    if "BSD-3-Clause" not in license_expression:
        failures.append(
            "expected BSD-3-Clause license metadata, "
            f"got {license_expression or '<missing>'}"
        )
    if import_seconds > MAX_IMPORT_SECONDS:
        failures.append(
            f"import latency {import_seconds:.3f}s exceeds {MAX_IMPORT_SECONDS:.3f}s"
        )
    if roundtrip_seconds > MAX_ROUNDTRIP_SECONDS:
        failures.append(
            f"roundtrip latency {roundtrip_seconds:.3f}s exceeds "
            f"{MAX_ROUNDTRIP_SECONDS:.3f}s"
        )
    if installed_bytes > MAX_INSTALLED_BYTES:
        failures.append(
            f"installed footprint {installed_bytes} exceeds {MAX_INSTALLED_BYTES}"
        )
    if media["width"] != 64 or media["height"] != 64:
        failures.append("decoded sample dimensions differ from 64x64")
    if int(media["frames_decoded"]) < 1:
        failures.append("no video frame decoded from synthetic sample")
    if not media["codec"]:
        failures.append("decoded stream did not report a codec")
    if "libavcodec" not in library_versions:
        failures.append("PyAV did not expose libavcodec version metadata")

    result["gate"] = "PASS" if not failures else "FAIL"
    result["failures"] = failures
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run_probe()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
