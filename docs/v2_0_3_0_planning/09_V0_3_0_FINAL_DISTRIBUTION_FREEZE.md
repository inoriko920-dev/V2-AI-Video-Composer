# STEP 09 — v0.3.0 Final Distribution Documentation and Requalification

**Date:** 8 October 2026 WIB
**Application:** V2-AI-Video-Composer only
**Previous exact-main RC source:** `5c29d162982e5bbcff2c9263c265ba84c84bf886`
**Immutable previously published stable v0.2.2:** `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`
**Authority:** Latest user `lanjutkan` grants finalizing distribution documents and testing only, NOT a public tag/release.

## Problem and deliverables

Previous exact-main RC Windows run `37767700585` passed and ZIPs were independently checked. However, packaged release notes, manifest, user guide, maintenance and backup documents contained permanent labels such as `RELEASE CANDIDATE / NOT PUBLISHED`, inappropriate for a future stable download.

STEP09 changes ONLY version-0.3.0 release-facing text and validation metadata:

- `RELEASE_NOTES_0.3.0.md`: publication-neutral title, features and best-effort local recovery cautions.
- `V2_FINAL_RELEASE_MANIFEST_0.3.0.md`: publication-neutral distribution content manifest; exact source SHA determined from BUILD_INFO, not guessed.
- User guide, maintenance and backup guide: neutral current v0.3.0 information, retain true historical v0.2.1 notes without describing it as the current release.
- `scripts/build_v2_0_3_0_candidate.ps1`, dedicated read-only Windows workflow and tests: build-time field `publication_status=READY_FOR_PUBLICATION` **does not mean a GitHub Release exists**. Public status must be checked from the Releases API.
- Regression tests `test_v2_0_3_0_final_distribution_contract.py` enforce absence of stale candidate labels inside packaged user documents; RC contract tests updated.
- No product feature/Qt UI/schema/AI provider/FFmpeg behavior, approved screenshots, original repo or historical release is changed.

## Gates and exact-source policy

1. On final PR head, CI/Ruff/mypy/pytest, CodeQL, backend and Windows acceptance must PASS.
2. Dedicated Windows 0.3.0 candidate run must PASS: pinned dependencies, source secret scan, verified FFmpeg 9.0.2 external-only, portable EXE/UI launch, five path variants, ZIP CRC, correct SHA256SUMS, full BUILD_INFO source identity.
3. Merge only all green and review diff for distribution-only scope. Verify main and previous `v0.2.2` tag exactly unchanged.
4. **After merge, freeze the NEW merge commit SHA.** Earlier RC ZIP checksums from `5c29d162...` are obsolete because source and bundled documents have changed. Run another exact-source Windows build from the *new main SHA*, then download and independently verify both nested ZIP CRC/SHA256 and BUILD_INFO.release_commit.
5. Only a **separate explicit user authorization to publish v0.3.0** may permit a one-time guarded publisher with tag and GitHub Release write permission. It must reject an existing v0.3.0 tag/release and never rewrite previous tags/assets.
6. After publication (not authorized here), download all publicly published assets, recompute hashes, verify v0.3.0 tag points to precisely the approved source commit, and document any partial failure transparently.

## Acceptance ledger

- Static distribution tests: pending.
- Final PR head CI / CodeQL / backend: pending.
- Windows portable and 0.3.0 RC: pending.
- Main merge and exact-main requalification: pending.
- Stable v0.3.0 tag and GitHub Release: **HOLD — not authorized**.
- Prior v0.2.2 published release: **must remain immutable**.

This document defines what to verify; it does not claim that any pending acceptance check has passed.
