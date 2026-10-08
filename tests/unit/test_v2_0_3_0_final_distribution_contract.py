"""v0.3.0 final distributable text and nonpublishing integrity contracts.

The release content must remain publication-neutral until a separate release
approval; build-time status READY_FOR_PUBLICATION never claims PUBLISHED.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_final_01_embedded_release_notes_are_neutral_and_safe() -> None:
    text = doc("RELEASE_NOTES_0.3.0.md")
    assert text.startswith("# AI Automatic Video Composer v0.3.0 — Release Notes")
    assert "Windows 11" in text
    assert "autosave" in text.lower()
    assert "not a guarantee" in text.lower()
    assert "FFmpeg" in text
    for banned in ("Release Candidate Notes", "RELEASE CANDIDATE",
                   "NOT PUBLISHED", "This RC is", "Do not publish from this branch"):
        assert banned not in text


def test_final_02_manifest_is_distribution_neutral() -> None:
    text = doc("V2_FINAL_RELEASE_MANIFEST_0.3.0.md")
    assert text.startswith("# V2 v0.3.0 — Distribution Manifest")
    assert "release_commit" in text
    assert "SHA-256" in text
    assert "READY_FOR_PUBLICATION" in text
    assert "v0.2.2" in text
    assert "Windows 11" in text
    assert "autosave" in text.lower()
    assert r"\n\n" not in text
    assert "NOT PUBLISHED / RC PREPARATION" not in text
    assert "Non-Published Release Candidate Manifest" not in text


def test_final_03_bundled_help_has_no_stale_rc_status() -> None:
    documents = (
        ("docs/USER_GUIDE.md", "Pemulihan dan autosave lokal"),
        ("MAINTENANCE.md", "0.3.0"),
        ("BACKUP_AND_RECOVERY.md", "autosave"),
    )
    for path, expected in documents:
        contents = doc(path)
        assert expected.lower() in contents[:1800].lower()
        head = contents[:1400]
        for banned in ("BELUM DIPUBLIKASIKAN", "BELUM dirilis publik",
                       "belum dipublikasikan", "kandidat v0.3.0",
                       "kandidat 0.3.0"):
            assert banned not in head, path


def test_final_04_builder_is_ready_not_published_and_has_sha_guards() -> None:
    script = doc("scripts/build_v2_0_3_0_candidate.ps1")
    assert "publication_status=READY_FOR_PUBLICATION" in script
    assert "publication_status=PUBLISHED" not in script
    assert "git archive" in script
    assert "Get-FileHash" in script
    assert "eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef" in script
    assert "git tag --list" in script


def test_final_05_windows_workflows_verify_nonpublished_candidate() -> None:
    rc = doc(".github/workflows/v2-0.3.0-rc.yml")
    assert "release/v0.3.0-final-documentation-freeze" in rc
    assert "contents: read" in rc
    assert "contents: write" not in rc
    assert "publication_status=READY_FOR_PUBLICATION" in rc
    assert "build_v2_0_3_0_candidate.ps1 -Channel rc" in rc
    for expression in ("gh release create", "git push --tags", "git tag -f"):
        assert not re.search(r"(?m)^\s*" + re.escape(expression), rc)
    # Frozen historical RC keeps its version; active source may advance.
    assert "version=0.3.0" in doc("scripts/build_v2_0_3_0_candidate.ps1")
