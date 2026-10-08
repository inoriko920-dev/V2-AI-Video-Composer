"""STEP04: deterministic negative-path RC integrity checks (no network or EXE).

Every test mutates an isolated fake candidate, never user projects or a release.
"""
from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import pytest
from scripts.verify_v2_0_3_1_rc_bundle import (
    ARCHIVES,
    BundleError,
    audit_bundle,
    inspect_zip,
)

SHA = "d4396f0d5ab2bbd5dd031f1a979d6de354a7f98f"
WIN_FILES = {
    "AI Automatic Video Composer.exe": b"MZ-dummy",
    "tools/ffmpeg/README.md": b"External FFmpeg is installed separately",
    "_internal/RELEASE_NOTES_0.3.1.md": b"RC notes",
}
SOURCE_FILES = {
    "pyproject.toml": b'[project]\nversion = "0.3.1"\n',
    "src/aavc/__init__.py": b'__version__ = "0.3.1"\n',
    "RELEASE_NOTES_0.3.1.md": b"Patch candidate",
    "V2_FINAL_RELEASE_MANIFEST_0.3.1.md": b"Not published",
}


def write_zip(path: Path, payload: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in payload.items():
            archive.writestr(name, data)


def fake_candidate(tmp_path: Path) -> Path:
    (tmp_path / "BUILD_INFO.txt").write_text(
        "version=0.3.1\nchannel=rc\n"
        f"release_commit={SHA}\n"
        "schema_max=4\nffmpeg_distribution=external-only\n"
        "publication_status=READY_FOR_PUBLICATION\n",
        encoding="utf-8",
    )
    write_zip(tmp_path / ARCHIVES[0], WIN_FILES)
    write_zip(tmp_path / ARCHIVES[1], SOURCE_FILES)
    refresh_sums(tmp_path)
    return tmp_path


def refresh_sums(folder: Path) -> None:
    text = "".join(
        f"{hashlib.sha256((folder / name).read_bytes()).hexdigest()}  {name}\n"
        for name in ARCHIVES
    )
    (folder / "SHA256SUMS.txt").write_text(text, encoding="utf-8")


def test_qa_01_valid_control_candidate_and_expected_source(tmp_path: Path) -> None:
    bundle = fake_candidate(tmp_path)
    evidence = audit_bundle(bundle, expected_sha=SHA)
    assert evidence["source_commit"] == SHA
    assert evidence["win64_entries"] == 3
    assert evidence["source_entries"] == 4
    assert evidence["status"] == "NOT_PUBLISHED"


@pytest.mark.parametrize(
    ("invalid", "expected"),
    [
        ("../escape.txt", "ZIP path traversal"),
        ("/rooted.txt", "unsafe ZIP entry path"),
        ("C:/windows.txt", "ZIP path traversal"),
        ("..\\escape.txt", "unsafe ZIP entry path"),
        (".env", "forbidden file"),
        ("user.key", "forbidden file"),
        ("ffmpeg.exe", "forbidden file"),
        ("media/ffprobe.exe", "forbidden file"),
        ("project.aavcproj.autosave", "forbidden file"),
        ("logs/session.log", "packaged user/runtime directory"),
    ],
)
def test_qa_02_reject_unsafe_zip_entries(invalid: str, expected: str) -> None:
    entries = dict(WIN_FILES)
    entries[invalid] = b"unsafe"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)
    with (
        zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive,
        pytest.raises(BundleError, match=expected),
    ):
        inspect_zip(archive, "win64")


def test_qa_03_reject_windows_case_fold_collision() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in WIN_FILES.items():
            archive.writestr(name, data)
        archive.writestr("Scene/One.png", b"A")
        archive.writestr("scene/ONE.PNG", b"B")
    with (
        zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive,
        pytest.raises(BundleError, match="case-insensitive"),
    ):
        inspect_zip(archive, "win64")


def test_qa_04_reject_missing_executable(tmp_path: Path) -> None:
    folder = fake_candidate(tmp_path)
    new = dict(WIN_FILES)
    del new["AI Automatic Video Composer.exe"]
    write_zip(folder / ARCHIVES[0], new)
    refresh_sums(folder)
    with pytest.raises(BundleError, match="missing mandatory"):
        audit_bundle(folder, expected_sha=SHA)


def test_qa_05_reject_crc_or_sha_tampering(tmp_path: Path) -> None:
    folder = fake_candidate(tmp_path)
    archive = folder / ARCHIVES[0]
    with archive.open("ab") as out:
        out.write(b"extra bytes change digest")
    with pytest.raises(BundleError, match="SHA-256 mismatch"):
        audit_bundle(folder, expected_sha=SHA)


def test_qa_06_reject_forged_source_commit(tmp_path: Path) -> None:
    folder = fake_candidate(tmp_path)
    with pytest.raises(BundleError, match="source commit mismatch"):
        audit_bundle(folder, expected_sha="0" * 40)


def test_qa_07_reject_wrong_publication_state(tmp_path: Path) -> None:
    folder = fake_candidate(tmp_path)
    info = folder / "BUILD_INFO.txt"
    info.write_text(
        info.read_text(encoding="utf-8").replace(
            "publication_status=READY_FOR_PUBLICATION", "publication_status=PUBLISHED"
        ),
        encoding="utf-8",
    )
    with pytest.raises(BundleError, match="readiness status"):
        audit_bundle(folder)


def test_qa_08_reject_duplicate_checksum_lines(tmp_path: Path) -> None:
    folder = fake_candidate(tmp_path)
    sums = folder / "SHA256SUMS.txt"
    sums.write_text(
        sums.read_text(encoding="utf-8") * 2, encoding="utf-8"
    )
    with pytest.raises(BundleError, match="duplicate checksum"):
        audit_bundle(folder)


def test_qa_09_reject_stale_source_identity(tmp_path: Path) -> None:
    folder = fake_candidate(tmp_path)
    bad = dict(SOURCE_FILES)
    bad["src/aavc/__init__.py"] = b'__version__ = "0.3.0"\n'
    write_zip(folder / ARCHIVES[1], bad)
    refresh_sums(folder)
    with pytest.raises(BundleError, match="source ZIP identity"):
        audit_bundle(folder)


def test_qa_10_reject_zip_symlink() -> None:
    import stat

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in WIN_FILES.items():
            archive.writestr(name, data)
        link = zipfile.ZipInfo("link-to-private-data")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, "../private.txt")
    with (
        zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive,
        pytest.raises(BundleError, match="symbolic link"),
    ):
        inspect_zip(archive, "win64")


def test_qa_11_reject_unlisted_archive(tmp_path: Path) -> None:
    folder = fake_candidate(tmp_path)
    sums = folder / "SHA256SUMS.txt"
    lines = sums.read_text(encoding="utf-8").splitlines()
    sums.write_text(lines[0] + "\n", encoding="utf-8")
    with pytest.raises(BundleError, match="checksum inventory"):
        audit_bundle(folder)
