from __future__ import annotations

import re
from dataclasses import dataclass

_SECRET_PATTERNS = (
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bsk-[0-9A-Za-z_-]{12,}\b"),
    re.compile(r"(?i)\bBearer\s+[0-9A-Za-z._~+/-]{8,}={0,2}"),
    re.compile(r"(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+"),
)


@dataclass(frozen=True, slots=True)
class ProviderContext:
    command: str
    project_summary: str
    scene_summary: str

    def as_prompt(self) -> str:
        parts = [f"PERINTAH:\n{self.command}"]
        if self.project_summary:
            parts.append(f"KONTEKS PROYEK:\n{self.project_summary}")
        if self.scene_summary:
            parts.append(f"KONTEKS SCENE:\n{self.scene_summary}")
        return "\n\n".join(parts)


class ContextBuilder:
    """Minimize and redact context before it crosses the provider boundary."""

    def __init__(
        self,
        *,
        max_command_chars: int = 8_000,
        max_project_chars: int = 6_000,
        max_scene_chars: int = 6_000,
    ) -> None:
        self._max_command_chars = max_command_chars
        self._max_project_chars = max_project_chars
        self._max_scene_chars = max_scene_chars

    def build(
        self,
        *,
        command: str,
        project_summary: str = "",
        scene_summary: str = "",
    ) -> ProviderContext:
        return ProviderContext(
            command=_sanitize(command, self._max_command_chars),
            project_summary=_sanitize(project_summary, self._max_project_chars),
            scene_summary=_sanitize(scene_summary, self._max_scene_chars),
        )


def redact_sensitive_text(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        if "api" in pattern.pattern.lower():
            redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _sanitize(text: str, limit: int) -> str:
    if limit < 1:
        return ""
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    redacted = redact_sensitive_text(normalized)
    if len(redacted) <= limit:
        return redacted
    return redacted[: max(0, limit - 14)].rstrip() + "\n[TRUNCATED]"
