"""W06-D packaging contracts, written before packaging remediation."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_w06d_version_identity_and_release_notes() -> None:
    assert 'version = "0.2.2"' in _read("pyproject.toml")
    assert '__version__ = "0.2.2"' in _read("src/aavc/__init__.py")
    assert (ROOT / "RELEASE_NOTES_0.2.2.md").is_file()
    assert "RELEASE_NOTES_0.2.2.md" in _read("aavc.spec")
    assert "RELEASE_NOTES_0.2.2.md" in _read("scripts/verify_portable.ps1")
    assert "RELEASE_NOTES_0.2.1.md" not in _read("aavc.spec")


def test_w06d_packaging_disables_opportunistic_upx() -> None:
    spec = _read("aavc.spec")
    assert "upx=True" not in spec
    assert spec.count("upx=False") >= 2


def test_w06d_artifact_scan_is_mandatory_in_packaging_and_verification() -> None:
    assert (ROOT / "scripts/verify_artifact_security.py").is_file()
    assert "verify_artifact_security.py" in _read("scripts/package.ps1")
    assert "verify_artifact_security.py" in _read("scripts/verify_portable.ps1")


def test_w06d_ffmpeg_reference_is_enforced_not_silently_upgraded() -> None:
    workflow = _read(".github/workflows/v2-user-acceptance.yml")
    assert "--version=9.0.2" in workflow
    assert "verify_ffmpeg_reference.ps1" in workflow
    assert "FFMPEG_REFERENCE" in workflow
    assert (ROOT / "scripts/verify_ffmpeg_reference.ps1").is_file()


def test_w06d_release_workflow_is_new_and_read_only() -> None:
    release = _read(".github/workflows/v2-0.2.2-rc-final.yml")
    assert "workflow_dispatch:" in release
    assert "contents: read" in release
    assert "contents: write" not in release
    assert re.search(r"(?m)^ *release-.*:", release) is None
    assert "v0.2.1" not in release


def test_w06d_new_candidate_manifest_and_hash_script_exist() -> None:
    assert (ROOT / "scripts/build_v2_0_2_2_candidate.ps1").is_file()
    assert (ROOT / "V2_FINAL_RELEASE_MANIFEST_0.2.2.md").is_file()
    candidate = _read("scripts/build_v2_0_2_2_candidate.ps1")
    for token in ("git archive", "SHA256SUMS", "BUILD_INFO", "Get-FileHash"):
        assert token in candidate


def test_w06d_distributable_ffmpeg_exclusion_is_explicit() -> None:
    assert "ffmpeg.exe" in _read("scripts/verify_portable.ps1").lower()
    assert "ffprobe.exe" in _read("scripts/verify_portable.ps1").lower()
    assert "9.0.2" in _read("tools/ffmpeg/README.md")
