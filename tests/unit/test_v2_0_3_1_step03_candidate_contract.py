"""STEP03 (candidate only): protect source provenance, builder and permissions.

Tests deliberately fail until a new version-specific builder/workflow exists.
Release publishing is explicitly outside this step.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_step03_01_builder_is_new_exact_source_and_nonpublishing() -> None:
    builder = source("scripts/build_v2_0_3_1_candidate.ps1")
    for required in (
        "release_candidate_0_3_1",
        "AI-Automatic-Video-Composer-0.3.1-win64.zip",
        "AI-Automatic-Video-Composer-0.3.1-source.zip",
        "RELEASE_NOTES_0.3.1.md",
        "V2_FINAL_RELEASE_MANIFEST_0.3.1.md",
        "version=0.3.1",
        "publication_status=READY_FOR_PUBLICATION",
        "release_commit=",
        "git archive",
        "SHA256SUMS.txt",
        "Get-FileHash",
        "verify_artifact_security",
        "refs/tags/v0.3.0^{commit}",
        "refs/tags/v0.2.2^{commit}",
        "d5a085fe239763e469ad30e91f526179fe8b2595",
        "eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef",
        "git status --porcelain",
    ):
        assert required in builder
    assert re.search(r"(?mi)^\s*(gh release create|git push --tags|git tag -f)\b", builder) is None


def test_step03_02_builder_fail_closed_on_reused_tag_and_output() -> None:
    builder = source("scripts/build_v2_0_3_1_candidate.ps1")
    assert 'git tag --list "v0.3.1"' in builder
    assert "refuse overwrite" in builder.lower()
    assert "v0.3.1" in builder
    assert "Git working tree" in builder
    assert "release_candidate_0_3_0" not in builder
    assert 'version=0.3.0' not in builder


def test_step03_03_read_only_candidate_workflow_never_publishes() -> None:
    workflow = source(".github/workflows/v2-0.3.1-rc.yml")
    assert "contents: read" in workflow
    assert "contents: write" not in workflow
    assert "actions/upload-artifact@" in workflow
    assert "build_v2_0_3_1_candidate.ps1" in workflow
    assert "verify_v2_0_3_1_portable_paths.ps1" in workflow
    assert "FFMPEG_REFERENCE" in workflow
    assert "windows-latest" in workflow
    assert "release_candidate_0_3_1" in workflow
    assert "NOT_PUBLISHED" in workflow
    assert "v0.3.0" in workflow
    assert "v0.2.2" in workflow
    assert re.search(r"(?mi)^\s*(gh release create|git push --tags|git tag -f)\b", workflow) is None


def test_step03_04_five_paths_are_tested_on_031_without_rewriting_old() -> None:
    matrix = source("scripts/verify_v2_0_3_1_portable_paths.ps1")
    for case in ("ASCII", "SPACES", "APOSTROPHE", "UNICODE", "DEEP"):
        assert case in matrix
    assert "SPECIAL_PATH_MATRIX=5/5_PASS" in matrix
    assert "v031_path_matrix" in matrix
    old = source("scripts/verify_v2_0_3_0_portable_paths.ps1")
    assert "v030_path_matrix" in old


def test_step03_05_candidate_manifest_clearly_distinguishes_artifact_from_release() -> None:
    manifest = source("V2_FINAL_RELEASE_MANIFEST_0.3.1.md")
    assert "NOT_PUBLISHED" in manifest
    assert "Actions artifact" in manifest
    assert "no public" in manifest.lower()
    assert "not a full" in manifest.lower()
    assert "source.zip" in manifest
