"""Independent fail-closed v0.3.1 RC bundle auditor (never publishes files).

Rechecks actual nested ZIP bytes and SHA256SUMS, not just builder log strings.
Can run outside Windows and has no third-party dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

VERSION = "0.3.1"
PREFIX = "AI-Automatic-Video-Composer-0.3.1"
ARCHIVES = (f"{PREFIX}-win64.zip", f"{PREFIX}-source.zip")
EXPECTED_WIN = ("AI Automatic Video Composer.exe", "tools/ffmpeg/README.md", "_internal/RELEASE_NOTES_0.3.1.md")
EXPECTED_SRC = ("pyproject.toml", "src/aavc/__init__.py", "RELEASE_NOTES_0.3.1.md", "V2_FINAL_RELEASE_MANIFEST_0.3.1.md")
BLOCKED_DIRS = frozenset(("cache", "logs", "runtime_data", "user_data", "__pycache__"))
BLOCKED_EXT = (".key", ".pem", ".autosave", ".recovery", ".p12", ".pfx")


class BundleError(ValueError):
    """Refuse a malformed, mismatched, unsafe or non-candidate RC archive."""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for piece in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def inspect_zip(archive: zipfile.ZipFile, kind: str) -> int:
    entries = archive.infolist()
    if not entries:
        raise BundleError("empty ZIP")
    names: set[str] = set()
    for entry in entries:
        name = entry.filename
        if not name or name.startswith("/") or "\\" in name or any(ord(c) < 32 for c in name):
            raise BundleError("unsafe ZIP entry path")
        parts = PurePosixPath(name).parts
        if ".." in parts or "." in parts or re.match(r"^[A-Za-z]:", name):
            raise BundleError("ZIP path traversal")
        normalized = name.casefold().rstrip("/")
        if normalized in names:
            raise BundleError("case-insensitive ZIP entry collision")
        names.add(normalized)
        if ((entry.external_attr >> 16) & 0o170000) == stat.S_IFLNK:
            raise BundleError("ZIP symbolic link")
        if kind == "win64":
            if BLOCKED_DIRS.intersection(p.casefold() for p in parts[:-1]):
                raise BundleError("packaged user/runtime directory")
            if not entry.is_dir():
                final = parts[-1].casefold()
                if (
                    final in {"ffmpeg.exe", "ffprobe.exe", ".env"}
                    or final.startswith(".env.")
                    or final.endswith(BLOCKED_EXT)
                ):
                    raise BundleError("forbidden file in portable ZIP")
    required = EXPECTED_WIN if kind == "win64" else EXPECTED_SRC
    if not all(p.casefold() in names for p in required):
        raise BundleError(f"{kind} ZIP missing mandatory file")
    if kind == "source":
        pyproject = archive.read("pyproject.toml").decode("utf-8")
        runtime = archive.read("src/aavc/__init__.py").decode("utf-8")
        if 'version = "0.3.1"' not in pyproject or '__version__ = "0.3.1"' not in runtime:
            raise BundleError("source ZIP identity does not match 0.3.1")
    bad = archive.testzip()
    if bad:
        raise BundleError("ZIP CRC failure")
    return len(entries)


def read_build_info(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        if "=" not in line:
            raise BundleError("malformed BUILD_INFO")
        k, v = line.split("=", 1)
        if k in data:
            raise BundleError("duplicate BUILD_INFO field")
        data[k] = v
    if data.get("version") != VERSION or data.get("channel") != "rc":
        raise BundleError("wrong candidate identity/channel")
    if data.get("publication_status") != "READY_FOR_PUBLICATION":
        raise BundleError("missing technical candidate readiness status")
    if data.get("ffmpeg_distribution") != "external-only" or data.get("schema_max") != "4":
        raise BundleError("unexpected packaging schema/FFmpeg contract")
    if not re.fullmatch(r"[0-9a-f]{40}", data.get("release_commit", "")):
        raise BundleError("invalid release_commit")
    return data


def audit_bundle(folder: Path, *, expected_sha: str | None = None) -> dict[str, str | int]:
    if not folder.is_dir() or folder.is_symlink():
        raise BundleError("candidate folder not available")
    data = read_build_info(folder / "BUILD_INFO.txt")
    if expected_sha is not None and data["release_commit"] != expected_sha:
        raise BundleError("source commit mismatch")
    listed: dict[str, str] = {}
    for line in (folder / "SHA256SUMS.txt").read_text(encoding="utf-8-sig").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+\.zip)", line)
        if match is None:
            raise BundleError("invalid SHA256SUMS format")
        name = match.group(2)
        if name in listed:
            raise BundleError("duplicate checksum name")
        listed[name] = match.group(1)
    if set(listed) != set(ARCHIVES):
        raise BundleError("unexpected checksum inventory")
    evidence: dict[str, str | int] = {"source_commit": data["release_commit"], "status": "NOT_PUBLISHED"}
    for kind, name in zip(("win64", "source"), ARCHIVES):
        archive_path = folder / name
        if not archive_path.is_file() or archive_path.is_symlink():
            raise BundleError("missing ZIP or unsafe symlink")
        actual = sha256(archive_path)
        if actual != listed[name]:
            raise BundleError("SHA-256 mismatch")
        with zipfile.ZipFile(archive_path) as archive:
            evidence[f"{kind}_entries"] = inspect_zip(archive, kind)
        evidence[f"{kind}_sha256"] = actual
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--expected-sha")
    args = parser.parse_args()
    try:
        result = audit_bundle(args.folder, expected_sha=args.expected_sha)
    except (BundleError, ValueError, OSError, zipfile.BadZipFile, KeyError) as error:
        print(f"V031_INDEPENDENT_BUNDLE_AUDIT_FAIL: {type(error).__name__}")
        return 1
    print("V031_INDEPENDENT_BUNDLE_AUDIT_PASS")
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
