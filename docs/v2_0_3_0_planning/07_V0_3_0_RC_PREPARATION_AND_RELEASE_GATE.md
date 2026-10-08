# STEP 07 — V2 v0.3.0 Release Candidate Preparation and Public Release Gate

**Date:** 8 October 2026 WIB. **Role:** RC preparation only. **Repo:** `inoriko920-dev/V2-AI-Video-Composer`.  
**Starting main:** `7d9ad7eda513daccea13a00c44d3d79bf76d9106` (W06-E PR #61 PASS).  
**Existing published stable:** `v0.2.2` -> `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef` (never move).  
**v0.3.0 GitHub Release:** NOT PUBLISHED. No tag, release or publicly distributed final binary is authorized by this RC phase.

## 1. Why a dedicated RC

W06-A..E implementation of autosave, snapshot provenance, Qt dialogs, Save/Restore transactions and failure-injection acceptance was merged, but the build and distribution identity on main remained `0.2.2`. Before labeling a download `v0.3.0`, a separate release-candidate branch must align runtime metadata, source/build manifest, executable-embedded documents, Windows release acceptance and exact-source hash evidence. Passing technical CI on a 0.2.2-labeled build is not itself a 0.3.0 release.

## 2. Deliverables and frozen decisions

- New RC branch: `release/v0.3.0-rc-preparation`. Version in `pyproject.toml` and `src/aavc/__init__.py` set to `0.3.0`; existing v0.2.2 tag/release untouched.
- `RELEASE_NOTES_0.3.0.md`, `V2_FINAL_RELEASE_MANIFEST_0.3.0.md`, updated bundled user guide and backup/maintenance guidance. Clearly say `NOT PUBLISHED`.
- `aavc.spec` and `scripts/verify_portable.ps1` require the correct v0.3.0 notes.
- Existing `scripts/build_v2_0_2_2_candidate.ps1` and `v2-0.2.2-rc-final.yml` preserved as historical data. New `scripts/build_v2_0_3_0_candidate.ps1` creates portable ZIP and exact-source ZIP using `git archive HEAD`; rehashes SHA-256, asserts immutable previous stable tag, refuses pre-existing v0.3.0 tag, writes `BUILD_INFO` publication state `NOT_PUBLISHED`.
- Windows 11 x64 release candidate workflow `v2-0.3.0-rc.yml` has **contents:read** only and uploads an expiring artifact, not a GitHub Release. `v2-user-acceptance.yml` now qualifies v0.3.0 identity with an unpublished candidate.
- `scripts/verify_v2_0_3_0_portable_paths.ps1`: five synthetic path variants ASCII, spaces, apostrophe, Unicode and nested depth. No real user data.
- Protect legacy UI freeze: original 42 reference screens, approved DLG-01/02/03, advanced schema v4 `advanced-v1`, 21 native effects, external FFmpeg reference 9.0.2 and Gemini credential model remain unchanged.

## 3. Critical safety gates

| Gate | Evidence required | Fail-closed behavior |
|---|---|---|
| Source and dependency identity | Runtime, installed Python metadata, pyproject all 0.3.0; requirements.lock, python 3.12.10, PySide6 6.11.2 | Block candidate |
| Immutable history | `v0.2.2` tag exact SHA and no `v0.3.0` tag | Abort without overwrite |
| Test-first contract | Six version/candidate/read-only-publisher checks, genuinely RED before build metadata changed, then GREEN | Block PR |
| Quality and security | secrets scan, compileall, pinned Ruff, strict mypy, full nonvisual pytest, CodeQL, backend | Block PR |
| Windows runtime | PyInstaller onedir, executable smoke, UI screenshot, FFmpeg external-only, 21-effect render suite | Block candidate |
| Path matrix | EXE smoke with ASCII, spaces, apostrophe, Unicode, deep folder | Reject incomplete evidence |
| Release bundle | portable ZIP + exact-source ZIP, `BUILD_INFO`, `SHA256SUMS`, notes, manifest, guide, maintenance, backup | Don't publish |
| Recompute checksums | Each ZIP SHA-256 calculated and reverified from the same final source SHA | Block RC |
| PR completion | Final-head CI, CodeQL, backend and Windows release-candidate workflow all PASS; merge to main; tree audit | No PASS before merge |
| Public release | separate explicit user authorization, new guarded publisher with isolated write permission | RC does not publish |

## 4. Test-first and acceptance evidence

The STEP07 release metadata contract was committed first, while runtime was still `0.2.2`; recorded RED in Actions run `37764379227`. After candidate scripts/version/docs/workflow are present, green tests and Windows release candidate checks must be verified by their **final-head run IDs**, not by stale earlier runs. The first candidate workflow run exposing the PowerShell absent-tag problem was corrected by using `git tag --list` (zero exit code for absence), avoiding a false CI failure. **Actual final-head tests and SHA hashes must be appended only after their real results are known.**

## 5. Public release workflow is a separate future gate

This RC workflow must never create or update GitHub Releases. After source is merged and frozen, future publication shall rebuild from the exact release-source commit and reverify package/runtime version 0.3.0, all tests, real FFmpeg, portable UI, extracted path checks, forbidden files, credentials, SHA256SUMS, `BUILD_INFO.release_commit`, and absence of a previous v0.3.0 release. Only the publisher job may use `contents:write`. The final `v0.3.0` tag must point to the exact final source. After publication, verify published assets, tag SHA and independent hashes before recording closure.

## 6. Known limitations / handoff

Autosave is best-effort for manually saved local projects. Uncooperative external editors, malware and sudden hardware power loss cannot be guaranteed safe by a SHA digest or in-process lock. Source ZIP is a snapshot without Git history; for account loss, preserve a Git Bundle of **this repo** separately. FFmpeg/ffprobe are intentionally not redistributed. Do not assert a stable v0.3.0 download exists while only an expiring CI artifact has been uploaded.

**Stop point:** Finish RC source/PR and verification only. Do not publish a stable tag, GitHub Release, or user-facing download without separate explicit permission.
