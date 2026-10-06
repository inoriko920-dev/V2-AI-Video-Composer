from __future__ import annotations

import json
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from .redaction import redact_text, redact_value


def write_diagnostics_bundle(
    destination: str | Path,
    *,
    summary: Mapping[str, object],
    logs: Sequence[str],
    explicit_secrets: Sequence[str] = (),
) -> Path:
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_summary = redact_value(dict(summary), explicit_secrets)
    safe_logs = "\n".join(redact_text(line, explicit_secrets) for line in logs)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "summary.json",
            json.dumps(safe_summary, ensure_ascii=False, indent=2, sort_keys=True),
        )
        archive.writestr("logs.txt", safe_logs)
    return target
