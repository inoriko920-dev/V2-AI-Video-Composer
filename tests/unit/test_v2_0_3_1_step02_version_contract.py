"""STEP02 test-first patch-version contract, with immutable v0.3.0 history.

STEP03's RC ZIP builder/workflow, source archive hashes and publication guards
are deliberately out of scope for this STEP02 test file.
"""
from __future__ import annotations

import re
import tomllib
from importlib.metadata import version
from pathlib import Path

from aavc import __version__

ROOT = Path(__file__).resolve().parents[2]


def content(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_step02_01_installed_and_source_version_are_v031() -> None:
    metadata = tomllib.loads(content("pyproject.toml"))
    assert metadata["project"]["version"] == "0.3.1"
    assert __version__ == "0.3.1"
    assert version("ai-automatic-video-composer") == "0.3.1"


def test_step02_02_candidate_notes_are_bundled_and_verified() -> None:
    expected = "RELEASE_NOTES_0.3.1.md"
    assert (ROOT / expected).is_file()
    assert expected in content("aavc.spec")
    assert expected in content("scripts/verify_portable.ps1")
    assert "RELEASE_NOTES_0.3.0.md" not in content("aavc.spec")
    assert (ROOT / "RELEASE_NOTES_0.3.0.md").is_file()


def test_step02_03_release_notes_are_scope_limited_and_not_published() -> None:
    notes = content("RELEASE_NOTES_0.3.1.md")
    assert notes.startswith("# AI Automatic Video Composer v0.3.1")
    for marker in ("WAV", ".wav", "v0.3.0", "Windows 11", "FFmpeg", "NOT_PUBLISHED"):
        assert marker in notes
    assert "autosave" in notes.lower()
    assert "recovery" in notes.lower()
    assert "not published" in notes.lower()
    assert not re.search(r"(?im)^\s*.*\b(public release is available|already published)\b", notes)


def test_step02_04_candidate_manifest_requires_future_exact_build() -> None:
    manifest = content("V2_FINAL_RELEASE_MANIFEST_0.3.1.md")
    for marker in (
        "version=0.3.1",
        "release_commit",
        "NOT_PUBLISHED",
        "READY_FOR_PUBLICATION",
        "SHA-256",
        "Windows 11",
        "advanced-v1",
        "v0.3.0",
        "v0.2.2",
        "FFmpeg",
    ):
        assert marker in manifest
    assert "no tag" in manifest.lower()
    assert "not a full" in manifest.lower()
    assert (ROOT / "V2_FINAL_RELEASE_MANIFEST_0.3.0.md").is_file()


def test_step02_05_windows_acceptance_checks_active_v031_and_frozen_v030() -> None:
    workflow = content(".github/workflows/v2-user-acceptance.yml")
    assert '"0.3.1"' in workflow
    assert "Confirm v0.3.1 package and runtime identity" in workflow
    assert "Verify immutable public v0.3.0" in workflow
    assert "refs/tags/v0.3.0^{commit}" in workflow
    assert "refs/tags/v0.2.2^{commit}" in workflow
    assert "d5a085fe239763e469ad30e91f526179fe8b2595" in workflow
    assert "eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef" in workflow
    assert "POST_RELEASE_STABLE_IDENTITY_AND_ASSETS_PASS" in workflow
    assert "066312fe6c983c797939fccf5682f5f4867c6ba528a099d18e67f33a8e1c7681" in workflow
    assert "063c3fa88c03972fdcadcf6c3a7d7c7b183df07b146710cd209a59cbb11ca9df" in workflow
    assert "Verify portable foundation" in workflow
    assert "Full technical user acceptance" in workflow
    assert "Build Windows portable" in workflow
    assert "contents: read" in workflow


def test_step02_06_retired_builder_and_frozen_release_docs_stay_intact() -> None:
    legacy_builder = content("scripts/build_v2_0_3_0_candidate.ps1")
    legacy_rc = content(".github/workflows/v2-0.3.0-rc.yml")
    assert "already tagged: RC builder must not overwrite" in legacy_builder
    assert '"v0.3.0"' in legacy_builder
    assert "git archive" in legacy_builder
    assert "contents: read" in legacy_rc
    assert "contents: write" not in legacy_rc
    assert (ROOT / "RELEASE_NOTES_0.3.0.md").is_file()
    assert (ROOT / "V2_FINAL_RELEASE_MANIFEST_0.3.0.md").is_file()
