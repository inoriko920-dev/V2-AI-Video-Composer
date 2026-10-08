"""Fail-closed security scan of the BUILT portable directory.

The repository source scan is separate: this scanner searches the actual files
which will be distributed. It prints file paths and secret pattern classes,
never matched secret values.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.check_no_secrets import SECRET_PATTERNS

CHUNK_SIZE = 1024 * 1024
OVERLAP = 512
BAD_DIR_NAMES = frozenset({"cache", "logs", "user_data", "runtime_data", "__pycache__"})
BAD_SUFFIXES = (".key", ".pem", ".autosave", ".recovery", ".p12", ".pfx")
BAD_EXACT_NAMES = frozenset({"ffmpeg.exe", "ffprobe.exe"})


def forbidden_path(relative: Path) -> bool:
    names = tuple(part.lower() for part in relative.parts)
    if any(name in BAD_DIR_NAMES for name in names[:-1]):
        return True
    final = names[-1]
    return (
        final in BAD_EXACT_NAMES
        or final == ".env"
        or final.startswith(".env.")
        or any(final.endswith(suffix) or f"{suffix}." in final for suffix in BAD_SUFFIXES)
    )


def secret_categories(path: Path) -> set[str]:
    """Scan binary and text content in chunks without exposing matching values."""
    found: set[str] = set()
    with path.open("rb") as source:
        overlap = b""
        while True:
            chunk = source.read(CHUNK_SIZE)
            if not chunk:
                break
            # Latin-1 retains every byte (including tokens inside binary data).
            text = (overlap + chunk).decode("latin-1")
            for kind, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    found.add(kind)
            overlap = (overlap + chunk)[-OVERLAP:]
    return found


def scan_artifact(root: Path) -> list[tuple[str, str]]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Portable directory is missing or is a symlink")
    findings: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            findings.append((relative.as_posix(), "unexpected-symlink"))
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            findings.append((relative.as_posix(), "unsupported-entry"))
            continue
        if forbidden_path(relative):
            findings.append((relative.as_posix(), "forbidden-runtime-path"))
        for kind in sorted(secret_categories(path)):
            findings.append((relative.as_posix(), kind))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan portable build, not repository sources")
    parser.add_argument("root", type=Path, help="built portable directory")
    args = parser.parse_args(argv)
    try:
        findings = scan_artifact(args.root)
    except (OSError, ValueError) as error:
        print(f"ARTIFACT_SECRET_SCAN_FAILED: {type(error).__name__}", file=sys.stderr)
        return 1
    if findings:
        print("ARTIFACT_SECRET_SCAN_FAILED:", file=sys.stderr)
        for path, category in findings:
            print(f"- {path} [{category}]", file=sys.stderr)
        print("Secret values are never printed.", file=sys.stderr)
        return 1
    print("ARTIFACT_SECRET_SCAN_PASS: no forbidden files or supported credential patterns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
