from __future__ import annotations

import re
from collections.abc import Sequence

_API_KEY = re.compile(r"AIza[0-9A-Za-z_-]{20,}")
_BEARER = re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+/=-]{8,}")
_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|token|secret|authorization)\s*[:=]\s*([^\s,;]+)"
)


def redact_text(text: str, explicit_secrets: Sequence[str] = ()) -> str:
    redacted = text
    for secret in explicit_secrets:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    redacted = _API_KEY.sub("[REDACTED]", redacted)
    redacted = _BEARER.sub("Bearer [REDACTED]", redacted)
    redacted = _ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", redacted)
    return redacted


def redact_value(value: object, explicit_secrets: Sequence[str] = ()) -> object:
    if isinstance(value, str):
        return redact_text(value, explicit_secrets)
    if isinstance(value, dict):
        return {
            str(key): redact_value(item, explicit_secrets)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item, explicit_secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item, explicit_secrets) for item in value)
    return value
