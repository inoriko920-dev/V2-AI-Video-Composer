from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from aavc.domain.project.models import AssetBinding, Scene

_ASSET_FILE = re.compile(r"^(A\d{3})\.png$", re.I)


def bind_assets(scenes: tuple[Scene, ...], directory: str | Path) -> tuple[AssetBinding, ...]:
    root = Path(directory)
    candidates: dict[str, list[Path]] = defaultdict(list)
    if root.exists():
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
        elif paths[0].stat().st_size < 16:
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
