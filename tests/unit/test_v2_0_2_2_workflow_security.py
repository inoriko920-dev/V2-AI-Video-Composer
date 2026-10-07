from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def _text(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def _assert_sha_pinned_actions(text: str) -> None:
    offenders: list[str] = []
    for match in re.finditer(r"^\s*-?\s*uses:\s*([^\s#]+)", text, re.MULTILINE):
        ref = match.group(1)
        if "@" not in ref:
            offenders.append(ref)
            continue
        _, version = ref.rsplit("@", 1)
        if not re.fullmatch(r"[0-9a-f]{40}", version):
            offenders.append(ref)
    assert not offenders, f"Unpinned external actions: {offenders}"


def test_backup_workflow_targets_v2_and_stable_v0_2_1() -> None:
    text = _text("backup-single-app.yml")
    assert "APP_NAME: V2-AI-Video-Composer" in text
    assert "REPO_FULL: ${{ github.repository }}" in text
    assert "STABLE_RELEASE: v0.2.1" in text
    assert "gh release view \"$STABLE_RELEASE\"" in text
    assert "gh release download \"$STABLE_RELEASE\"" in text
    assert "INCLUDED_FROM_RELEASE_$STABLE_RELEASE" in text
    assert "AI-Automatic-Video-Composer-COMPLETE-GIT-HISTORY.bundle" not in text
    assert "BUILD/ = build release v0.1.1" not in text
    _assert_sha_pinned_actions(text)


def test_step00_docx_generator_is_manual_read_only_artifact_generation() -> None:
    text = _text("generate-v2-0.2.2-step00-docx.yml")
    assert "workflow_dispatch:" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "git push" not in text
    assert "git commit" not in text
    assert "actions/upload-artifact@" in text
    _assert_sha_pinned_actions(text)


def test_legacy_planning_docx_generator_is_manual_read_only_artifact_generation() -> None:
    text = _text("generate-v2-planning-docx.yml")
    assert "workflow_dispatch:" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "git push" not in text
    assert "git commit" not in text
    assert "actions/upload-artifact@" in text
    _assert_sha_pinned_actions(text)
