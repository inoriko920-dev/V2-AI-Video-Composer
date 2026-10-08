# W06-D Implementation Result — Windows Packaging / Dependency Hardening

Status: **COMPLETE / PASS — CANDIDATE ONLY, NOT PUBLISHED**

Repository: inoriko920-dev/V2-AI-Video-Composer
PR: #44
V2 main starting SHA: 15b69deec4b01f4fdbf5350173e94516511cc574
Published stable v0.2.1 tag stays frozen at eb94efebf142ba8203dfc3ae3c5fa861222a0926

## Failing-before proof

- Tests-first commit: ad128352225d140cb651456d4145152b4c169d0f
- CI run 37722279886: 7 expected packaging contract failures, 738 other tests PASS (workflow later cancelled by a newer branch commit).
- Gaps proved: stale version/release notes, UPX enabled, absent artifact content scan, no FFmpeg 9.0.2 enforcement, missing read-only 0.2.2 candidate workflow, absent release candidate build/hash script, missing explicit FFmpeg ZIP exclusion.

## Implementation

1. Version synchronized to 0.2.2 in pyproject.toml, package __init__, PyInstaller data inventory and portable verifier; new RELEASE_NOTES_0.2.2.md and V2_FINAL_RELEASE_MANIFEST_0.2.2.md are candidate documents.
2. aavc.spec disables UPX on EXE and COLLECT: opportunistic UPX use eliminated.
3. scripts/verify_artifact_security.py scans every file in the actual built portable tree (binary or text chunks) for supported credential patterns and forbidden runtime files, reports only category/path, never matched secrets. Its negative tests include embedded credentials crossing read chunks.
4. scripts/package.ps1 and scripts/verify_portable.ps1 both require artifact security scan. Portable verification explicitly blocks shipped ffmpeg.exe/ffprobe.exe.
5. scripts/verify_ffmpeg_reference.ps1 enforces FFmpeg and ffprobe 9.0.2, records paths and SHA-256 fingerprints, runs PATH mode, stages the reviewed reference binary temporarily beside the packaged EXE, proves application resolver prefers app-local, removes staged binaries in finally, and scans the final distributable again.
6. .github/workflows/v2-user-acceptance.yml installs the exact Chocolatey reference version 9.0.2 when absent, checks version before real render tests, verifies version metadata, builds/scans portable, performs app-local/PATH proof and prepares candidate evidence.
7. scripts/build_v2_0_2_2_candidate.ps1 builds exact git-archive source and Windows portable ZIPs, records BUILD_INFO (source SHA, version/channel, schema, advanced contract, Python, PySide6, PyInstaller and FFmpeg reference), checks zip inventory and excluded FFmpeg, generates and independently revalidates SHA256SUMS.
8. .github/workflows/v2-0.2.2-rc-final.yml provides manual RC/final-verification candidate scaffolding with contents: read only. It cannot publish GitHub Releases or create/move tags.
9. tools/ffmpeg/README.md documents the 9.0.2 reference and external-only installation policy.

## Final tested application-code SHA

Commit 062f2b97e3a1f8b49e65d90fd1e3348566536e27

Automated evidence:
- CI 37722775010: **PASS** — 750 passed, 45 deselected; compile, Ruff, mypy, STEP09 capture PASS.
- CodeQL 37722775058: **PASS**.
- Optional Backend Spike 37722775062: **PASS**.
- Windows Automated User Acceptance 37722774954: **PASS** — 795 passed; packaged EXE smoke/UI, FFmpeg PATH+app-local, artifact secret scan, no FFmpeg distribution, exact-source candidate and archive SHA256 PASS.
- Reference version: FFmpeg/ffprobe 9.0.2.
- Candidate generated from exact CI PR merge checkout b19c4e41f1d64af484359f363488496648aba6b0; this PR candidate SHA is NOT the eventual canonical release commit. STEP07 must regenerate candidate from its exact release source.

## Dependency/provenance decision

- No new runtime or dev dependency was adopted. PySide6 6.11.2, PyInstaller 6.22.3, pytest 9.1.1, mypy 2.4.0, Ruff 0.16.8 and all existing lock pins remain unchanged.
- Optional Ruff 0.16.10 adoption deferred; no zero-churn proof was needed for the required packaging remediation. Dependencies do not need a license/provenance CSV edit when they are unchanged.
- Python 3.12.10 security-line evaluation, and setuptools backend isolation alignment remain deferred under STEP 05 authorization.
- Current UI/21 native effects, project schema v4 advanced-v1, final FFmpeg renderer, Gemini provider and credentials model unchanged.
- Original/legacy repository, stable v0.2.1, historical release workflows and published tags/releases untouched.

## Remaining scope

- GAP-03A production autosave / interactive recovery lifecycle remains deferred.
- Candidate ZIP from PR evidence is for validation only; neither a tag nor GitHub Release has been published.
- The new manual candidate workflow must be exercised from a canonical main/RC ref at a later authorized gate, and release/commit identity reverified.
- WPK-26 broader special-path candidate matrix and end-to-end consolidated regression are W06-E / STEP 07 responsibilities where not already covered by existing Windows tests.

## Wave gate and handoff

**STEP 06 / W06-D: PASS / COMPLETE.**
**Exact next: STEP 06 / W06-E — Consolidated Implementation Closure.**

Do not begin W06-E in the same turn. STEP07 release publication is still blocked.
