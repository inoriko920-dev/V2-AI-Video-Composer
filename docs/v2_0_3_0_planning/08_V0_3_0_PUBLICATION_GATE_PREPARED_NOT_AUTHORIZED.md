# v0.3.0 — PUBLICATION GATE (PREPARED; NOT AUTHORIZED)

**Repository**: `inoriko920-dev/V2-AI-Video-Composer` only  
**Date**: 8 October 2026 WIB  
**Current frozen tested source**: `5c29d162982e5bbcff2c9263c265ba84c84bf886`  
**Stable historical tag `v0.2.2`**: `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`  
**Current public release v0.3.0**: NONE — DO NOT CREATE YET  
**User authorization**: generic `lanjutkan` authorizes further preparation, NOT publishing.

## 1. Evidence already PASS (candidate only)

- PR #62 merged; final `main` SHA above; CI and CodeQL successful for that exact SHA.
- GitHub Actions frozen-source Windows verification **run 37767700585** SUCCESS. It explicitly checked out the frozen `main` SHA, used Python 3.12.10 and PySide6 6.11.2, performed full nonvisual tests, Ruff, strict mypy, portable build and EXE launch, five-path matrix (ASCII, spaces, apostrophe, Unicode and nested), external-only FFmpeg 9.0.2 and verified SHA-256 files.
- Nonpublished workflow artifact **11547255962**, `AAVC-0.3.0-FROZEN-MAIN-NOT-PUBLISHED`, 65,952,841 bytes. Envelope digest `sha256:84ab740c7b9693159b6a63996bcab96f1732307d3f49482171b029eaf5b254c2` is different from the two nested ZIP hashes.
- Nested Windows portable ZIP `AI-Automatic-Video-Composer-0.3.0-win64.zip`, **62,263,000 bytes**, SHA-256 `17ac952daa0656808f5733bb080926c1564d3dd8d1f2ed8ef863578d324fc2f5`.
- Nested exact-source ZIP `AI-Automatic-Video-Composer-0.3.0-source.zip`, **3,886,773 bytes**, SHA-256 `d26e753fac039a7595a0593062efdd3bcd55aa8ba249463041474d369c317971`.
- CRC checked on all archives. Windows EXE present; `ffmpeg.exe` and `ffprobe.exe` absent by design. `BUILD_INFO.release_commit` matches exact frozen source; `publication_status=NOT_PUBLISHED`.
- Previous stable `v0.2.2` and its 11 published assets unchanged.

## 2. PUBLICATION BLOCKER: embedded notes are still release-candidate notes

The frozen source `RELEASE_NOTES_0.3.0.md` begins `Release Candidate Notes` and says `NOT PUBLISHED`. The portable executable bundles this file. Publishing these exact bytes as a **stable final release** would leave contradictory release-status instructions inside the distribution. The publication gate therefore remains **HOLD**; do not simply rename the verified candidate to a stable release.

**Before stable publication**, choose a separate version-freeze/requalification step:

1. Prepare final end-user `RELEASE_NOTES_0.3.0.md` and related manifest without candidate-only status claims, preserving accurate autosave limitations.
2. Prepare stable packaging metadata while retaining the integrity rule that no artifact may be falsely marked published before an actual publication.
3. Merge text/packaging corrections via dedicated PR, then freeze its **new, exact** merge SHA.
4. Repeat CI, CodeQL, Windows 11 x64 full acceptance, FFmpeg 9.0.2 external-mode smoke, ZIP/source archive creation and full SHA-256 verification on the new SHA.
5. Regenerate final publication manifest/hash list. **Do not reuse** the two RC SHA-256 values above if any source/distribution content changes.

The user must separately authorize **publishing v0.3.0 publicly** before creating any new release/tag. Generic `lanjutkan` alone is not that authorization.

## 3. Proposed secure publisher design (never run without approval)

Keep a **read-only verification job** and a separate **publish-only job**; grant `contents:write` only to the latter, and require an environment with human approval if supported.

Publisher must reject absent/mismatched inputs and perform checks in this exact order:

1. Repository full name exactly `inoriko920-dev/V2-AI-Video-Composer`; target version `0.3.0`; source SHA must be an **explicit, full 40-character immutable commit**, not a moving `main` ref.
2. Inspect `refs/tags/v0.2.2` and ensure SHA exactly `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`; reject any attempted force update.
3. Check `refs/tags/v0.3.0` and `releases/tags/v0.3.0`: **both must be absent**. If either exists, stop and report manual reconciliation; never overwrite or create a duplicate release.
4. Verify installed/runtime/package version 0.3.0, schema max 4, animation contract advanced-v1, dependency pins, and every expected frozen UI/dialog reference file.
5. Get **the exact Windows candidate artifact built from the intended source SHA** and verify successful Actions run, artifact digest, download contents, nested ZIP CRC, both SHA-256 lines, and `BUILD_INFO.release_commit` equals the SHA. Reject expired artifacts, incomplete asset sets and path traversal entries.
6. Ensure ZIP portable contains the expected EXE and `tools/ffmpeg/README.md`, but **does not bundle** FFmpeg/ffprobe executable, tokens, credentials, caches, private snapshots or testing fixtures.
7. Only after explicit release-approval signal: create an annotated `v0.3.0` tag targeting **that same exact approved source SHA**, without force and without tag reuse.
8. Create GitHub Release with verified Windows ZIP/source ZIP, checksum file, release notes, user guide, backup guide, manifest and build info. Release type should be stable only after stable-doc corrections; otherwise use an explicitly labeled prerelease and obtain permission for that.
9. Download *published* assets from the GitHub Release API, independently recompute SHA-256 and sizes and check the release tag target, asset list, `draft=false`, `prerelease=false` (when stable). If any mismatch, clearly report **PARTIAL PUBLICATION** rather than assuming rollback. Do not retag.
10. Write post-publication closure documentation on a **new documentation branch**, without retroactively altering the tagged source.

## 4. No-publish dry-run acceptance table

| Check | Current disposition |
|---|---|
| Historical stable v0.2.2 intact | PASS |
| Frozen final-source SHA known | PASS |
| Windows 11 portable EXE / UI / 5 paths | PASS (candidate) |
| Candidate archive CRC and SHA-256 | PASS |
| Current source `0.3.0` runtime/package identity | PASS |
| v0.3.0 public release/tag absent | PASS |
| Final release notes free of RC-only labeling | **HOLD** |
| Final-version rebuilt/requalified after release-notes cleanup | **HOLD** |
| Explicit user authorization to publish | **HOLD** |
| Exact final-source public asset hashes checked after publication | NOT STARTED |

## 5. What NOT to do

- Do not modify, delete, overwrite, force-push, retag or reupload `v0.2.2` or any earlier release.
- Do not alter frozen original 42 screenshots, three approved recovery dialog PNGs/DOCX, original non-V2 repository, Gemini credentials or FFmpeg distribution.
- Do not confuse `git archive HEAD` **source snapshot** with a full Git history backup.
- Do not equate passing Actions workflows or having candidate ZIPs with an already-published GitHub Release.
- Do not silently introduce a fourth recovery modal or change approved UI merely to prepare a release.
- Do not make a live `contents:write` workflow that runs on ordinary push/PR events.

**STOP:** No public tag/release/public asset mutation is permitted at this time. This publication preparation document is intentionally on a separate branch so the already-tested `main` SHA stays unchanged.
