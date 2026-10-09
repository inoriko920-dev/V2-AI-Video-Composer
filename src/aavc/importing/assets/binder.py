from __future__ import annotations

import re
import struct
import zlib
from collections import defaultdict
from pathlib import Path

from aavc.domain.project.models import AssetBinding, Scene

_ASSET_FILE = re.compile(r"^(A\d{3})\.png$", re.I)


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunks_are_valid(path: Path) -> bool:
    """Check the complete PNG chunk structure and CRC without loading media to RAM.

    This is a structural preflight, not a decoder. FFmpeg still validates and
    decodes image pixels during render.
    """

    try:
        with path.open("rb") as stream:
            if stream.read(8) != _PNG_SIGNATURE:
                return False

            first_chunk = True
            has_image_data = False
            while True:
                header = stream.read(8)
                if len(header) != 8:
                    return False
                chunk_size = int.from_bytes(header[:4], "big")
                chunk_type = header[4:]
                if chunk_size > 0x7FFFFFFF or not all(
                    65 <= byte <= 90 or 97 <= byte <= 122
                    for byte in chunk_type
                ):
                    return False
                if first_chunk and (
                    chunk_type != b"IHDR" or chunk_size != 13
                ):
                    return False

                crc = zlib.crc32(chunk_type)
                remaining = chunk_size
                if first_chunk:
                    ihdr = stream.read(13)
                    if len(ihdr) != 13:
                        return False
                    width, height, _, _, compression, filtering, interlace = (
                        struct.unpack(">IIBBBBB", ihdr)
                    )
                    if (
                        width == 0
                        or height == 0
                        or compression != 0
                        or filtering != 0
                        or interlace not in (0, 1)
                    ):
                        return False
                    crc = zlib.crc32(ihdr, crc)
                else:
                    while remaining:
                        block = stream.read(min(remaining, 65536))
                        if not block:
                            return False
                        crc = zlib.crc32(block, crc)
                        remaining -= len(block)

                stored_crc = stream.read(4)
                if len(stored_crc) != 4 or crc != int.from_bytes(
                    stored_crc, "big"
                ):
                    return False

                if chunk_type == b"IDAT" and chunk_size:
                    has_image_data = True
                if chunk_type == b"IEND":
                    return (
                        chunk_size == 0
                        and has_image_data
                        and stream.read(1) == b""
                    )
                first_chunk = False
    except OSError:
        # Deleted/unreadable assets must not be classified as READY.
        return False


def bind_assets(scenes: tuple[Scene, ...], directory: str | Path) -> tuple[AssetBinding, ...]:
    root = Path(directory)
    candidates: dict[str, list[Path]] = defaultdict(list)
    if root.is_dir():
        for path in root.iterdir():
            if path.is_file():
                match = _ASSET_FILE.match(path.name)
                if match:
                    candidates[match.group(1).upper()].append(path)

    quote_by_id = {
        asset_id: quote
        for scene in scenes
        for asset_id, quote in zip(scene.asset_ids, scene.source_quotes, strict=True)
    }
    bindings: list[AssetBinding] = []
    for asset_id in quote_by_id:
        paths = candidates.get(asset_id, [])
        if not paths:
            status = "MISSING"
            chosen = None
        elif len(paths) > 1:
            status = "DUPLICATE"
            chosen = str(paths[0].resolve())
        elif not _png_chunks_are_valid(paths[0]):
            status = "CORRUPT"
            chosen = str(paths[0].resolve())
        else:
            status = "READY"
            chosen = str(paths[0].resolve())
        bindings.append(
            AssetBinding(
                asset_id=asset_id,
                source_quote=quote_by_id[asset_id],
                path=chosen,
                status=status,  # type: ignore[arg-type]
            )
        )
    return tuple(bindings)
