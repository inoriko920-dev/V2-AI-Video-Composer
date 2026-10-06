from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str


def windows_command_units(argv: Sequence[str]) -> int:
    """Return CreateProcessW UTF-16 command units including the NUL terminator."""

    rendered = subprocess.list2cmdline(list(argv))
    return len(rendered.encode("utf-16-le")) // 2 + 1


class ProcessRunner:
    """The only repository owner allowed to execute child processes."""

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        completed = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=timeout_seconds,
        )
        return ProcessResult(completed.returncode, completed.stdout, completed.stderr)
