"""STEP07 v0.3.0 release-candidate contract (test-first, no publication).

Historical release workflows/tags must remain immutable. Build outputs are
non-published and exact-source, not a GitHub Release or a full git-history backup.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_rc_01_package_runtime_and_release_notes_are_v030() -> None:
    assert 'version = "0.3.0"' in read("pyproject.toml")
    assert '__version__ = "0.3.0"' in read("src/aavc/__init__.py")
    assert (ROOT / "RELEASE_NOTES_0.3.0.md").is_file()
    assert "RELEASE_NOTES_0.3.0.md" in read("aavc.spec")
    assert "RELEASE_NOTES_0.3.0.md" in read("scripts/verify_portable.ps1")
    assert "RELEASE_NOTES_0.2.2.md" not in read("aavc.spec")


def test_rc_02_candidate_builder_preserves_exact_source_and_sha() -> None:
    candidate = read("scripts/build_v2_0_3_0_candidate.ps1")
    for token in (
        "AI-Automatic-Video-Composer-0.3.0-win64.zip",
        "AI-Automatic-Video-Composer-0.3.0-source.zip",
        "git archive",
        "release_commit=",
        "publication_status=READY_FOR_PUBLICATION",
        "Get-FileHash",
        "SHA256SUMS.txt",
        "verify_artifact_security",
    ):
        assert token in candidate
    assert "version=0.3.0" in candidate
    assert "schema_max=4" in candidate
    assert "advanced-v1" in candidate
    assert "9.0.2" in candidate
    assert re.search(r"(?m)^\s*if\s*\([^)]*v0\.2\.2", candidate) is None


def test_rc_03_candidate_workflow_is_read_only_and_never_publishes() -> None:
    workflow = read(".github/workflows/v2-0.3.0-rc.yml")
    assert "contents: read" in workflow
    assert "contents: write" not in workflow
    assert "actions/upload-artifact@" in workflow
    assert "build_v2_0_3_0_candidate.ps1" in workflow
    assert "v0.2.2" in workflow  # immutable preceding release
    assert "eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef" in workflow
    assert "FFMPEG_REFERENCE" in workflow
    assert "Verify portable" in workflow
    assert not re.search(r"(?m)^\s*(gh release create|git push --tags|git tag -f)\b", workflow)


def test_rc_04_active_windows_acceptance_uses_new_version() -> None:
    workflow = read(".github/workflows/v2-user-acceptance.yml")
    assert '"0.3.0"' in workflow
    assert "build_v2_0_3_0_candidate.ps1 -Channel rc" in workflow
    assert "release_candidate_0_3_0" in workflow
    assert "FFMPEG_REFERENCE" in workflow
    assert "0.2.2 package and runtime identity" not in workflow


def test_rc_05_historical_release_assets_and_workflows_remain_available() -> None:
    assert (ROOT / "RELEASE_NOTES_0.2.2.md").is_file()
    assert (ROOT / "scripts/build_v2_0_2_2_candidate.ps1").is_file()
    assert (ROOT / ".github/workflows/v2-0.2.2-rc-final.yml").is_file()
    assert (ROOT / "V2_FINAL_RELEASE_MANIFEST_0.2.2.md").is_file()
    assert (ROOT / "V2_FINAL_RELEASE_MANIFEST_0.3.0.md").is_file()


def test_rc_06_manifest_enforces_nonpublishing_and_valid_scope() -> None:
    manifest = read("V2_FINAL_RELEASE_MANIFEST_0.3.0.md")
    assert "READY_FOR_PUBLICATION" in manifest
    assert "v0.2.2" in manifest
    assert "v0.3.0" in manifest
    assert "Windows 11" in manifest
    assert "SHA-256" in manifest
    assert "autosave" in manifest.lower()
    assert "FFmpeg" in manifest
