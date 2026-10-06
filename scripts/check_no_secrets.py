from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_FILE_BYTES = 2_000_000

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{30,255}\b")),
    ("github-fine-grained-token", re.compile(r"\bgithub_pat_[0-9A-Za-z_]{20,255}\b")),
    ("openai-or-openrouter-key", re.compile(r"\bsk-(?:or-v1-)?[0-9A-Za-z_-]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    kind: str


def scan_text(text: str, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for kind, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(Finding(path=path, line=line, kind=kind))
    return findings


def tracked_files(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [Path(os.fsdecode(raw)) for raw in completed.stdout.split(b"\0") if raw]


def scan_repository(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for relative_path in tracked_files(root):
        path = root / relative_path
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) > MAX_FILE_BYTES or b"\0" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(text, relative_path))
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = scan_repository(root)
    if findings:
        print("Potential committed secrets detected:", file=sys.stderr)
        for finding in findings:
            print(
                f"- {finding.path}:{finding.line} [{finding.kind}]",
                file=sys.stderr,
            )
        print("Secret values are intentionally not echoed.", file=sys.stderr)
        return 1
    print("Secret scan passed: no supported credential patterns found in tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
