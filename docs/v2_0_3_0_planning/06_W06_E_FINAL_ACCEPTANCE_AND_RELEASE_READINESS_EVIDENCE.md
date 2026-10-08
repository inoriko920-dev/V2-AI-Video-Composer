# STEP 06 / W06-E — Cross-Wave Acceptance, Recovery Idempotency and Release Readiness

**Repository:** `inoriko920-dev/V2-AI-Video-Composer` ONLY. **Date:** 8 October 2026 WIB.
**Pre-wave main SHA:** `7fd4acbf38061d8a0afb56a54caa86e89213bd9f` (W06-D PR #60 merged).
**Immutable published stable tag:** `v0.2.2` -> `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.
**Gate:** HOLD until W06-E final-head CI/CodeQL/backend/Windows portable acceptance success and merged-main check. No release authorized or published in this wave.

## Scope and real findings

W06-A scheduler, W06-B provenance, W06-C Save/Open/Restore transactions and W06-D Qt dialogs/timer were already in main. This wave tests the combined path; it neither redesigns 42 frozen editor screens nor changes the 3 approved recovery PNGs/DOCX.

Two W06-E failures found using synthetic test-first cases:

1. **Repeated Restore dialog (real product defect).** W06-C Restore intentionally keeps `.autosave` and its original sidecar for forensic safety. After the project on disk becomes byte-for-byte equal to the retained valid snapshot, its prior provenance baseline no longer matches and inspector reasonably calls it UNCERTAIN. W06-D showed the conflict warning again when reopening a *completely identical* project. This could invite users to Restore the same bytes repeatedly.
2. **Cross-thread UI/session access (concurrency flaw).** W06-D snapshot worker still queried canonical `ProjectSession` and `RecoveryCoordinator` fields from its background IO thread. This is unnecessary and risks accessing mutable Qt-session-owned state concurrently.

## Test-first proof, change and safety rationale

- Before implementation, **GitHub Actions run `37762298469` RED: 7 failed**, specifically absence of `RecoveryPreflight.equivalent_snapshot` and background worker reading live session/coordinator fields. No failure was caused by missing Qt/EGL or a missing fixture.
- Added `RecoveryPreflight.equivalent_snapshot` only when **both valid decoded saved project and decoded snapshot are verified to have exactly matching SHA-256 bytes**. This predicate is false on ABSENT, INVALID, changed bytes or a corrupt candidate; it doesn't assert that sidecar provenance was verified.
- Added `RecoveryTransactions.open_identical_saved(plan)`: under the existing W06-B shared file lease, revalidates the full preflight token (disk hash, snapshot hash, sidecar hash, current session). Loads saved project through the one canonical `ProjectSession`, advancing only its real saved baseline, **without deleting, quarantining or modifying any snapshot or metadata files**. A race during preflight denies the operation.
- Existing `RecoveryMainWindow.open_project` checks this equivalent-valid-data predicate *after the legacy unsaved guard* and uses the read-only-candidate Open action. It skips the redundant DLG-01/02 modal only for identical bytes, not for any different candidate or invalid snapshot.
- Background worker now uses only immutable `SnapshotRequest.project_state`, path and saved baseline SHA captured on Qt thread; the W06-B ProvenanceStore lock and on-disk digest checks enforce the write. Main thread remains responsible for eligibility, epoch, session, dirty guard and completion; Save/Open/Restore waits on the one physical writer slot. The worker does not touch Qt, session or coordinator.
- Added `tests/integration/test_v2_0_3_0_w06_e_final_acceptance.py`: 10 parameterized case executions for v3/v4, Unicode/apostrophe path, verified/uncertain/corrupt candidate, stale hash races, worker source boundary, actual Qt repeat-open without modal, crash gap with metadata preserved, and no secrets/raw path in sidecar.
- After minimum implementation, **GitHub Actions run `37762488770` GREEN: 10 passed** on Python 3.12 + pinned PySide6 6.11.2. No sleep-based timing, no user project assets, no real API secrets.
- This scope doesn't promise a general cryptographic signature, atomic OS compare-and-swap vs arbitrary external processes, or 100% durability across sudden power loss.

## Cross-wave acceptance matrix / coverage mapping

| Family | Owner | Verification evidence |
|---|---|---|
| RCV-01..24 | W06-A through W06-E | W06-A 18 focused cases; W06-B 27 focused cases; W06-C 32 transaction cases; W06-D 14 Qt cases; W06-E final reopen/idempotency tests |
| SCH-01..12 | W06-A / W06-D | Clock-injected coordinator tests plus Qt timer/serial worker cases |
| AT-01..20 | W06-B / W06-C / W06-E | File hash baseline, crash split, quarantines, rollback, one winner for competing Restore, partial commit, external change, sidecar inconsistency |
| UI-01..12 | W06-D / W06-E | Approved three dialog designs, cancel/default/focus, old guard first, Qt startup/capture, repeat-open no prompt |
| COMP-01..10 | W06-E / full pre-existing Windows acceptance | Synthetic v3/v4, Unicode path, stale data, secret-free descriptor, public dependency pins, portable EXE, ffmpeg external-only and stable v0.2.2 identity via existing acceptance workflow |

The mapping identifies test evidence and does NOT assert every planned matrix case has been individually run under an identical case ID. Whole-suite green and runner evidence must be checked before the final completion claim. The actual Windows acceptance workflow captures screenshot/EXE smoke and FFmpeg 9.0.2 PATH/external-only checks; keep the produced candidate **non-published**.

## Acceptance / release gate

1. Final W06-E PR must contain only W06-E service/window fixes, tests and status/evidence updates. Temporary Linux proof workflow is removed.
2. GitHub Actions on the **same final PR head**: CI (secret scan, compile, pinned Ruff, strict mypy, old and new pytest, STEP09 captures), CodeQL, backend, Windows automated user acceptance (FFmpeg external, EXE, screenshot, portable smoke, candidate packaging) all **SUCCESS**.
3. Verify release metadata `pyproject.toml` still `0.2.2`; confirm `v0.2.2` tag immutable, no v0.3.0 tag/release/new download published; the original non-V2 project untouched.
4. Merge W06-E PR into `main`; re-read Git tree and verify new source/test/evidence and the three approved UI PNGs still present.
5. Stop and report verified result. **Actual v0.3.0 public release, bumping version, publishing binaries, or modifying tags requires separately authorized release work.** Once merged, W06-E can be called engineering implementation PASS/ready for release review, not "released".

## Known limitations to communicate

This is a **best-effort local crash-recovery system for saved projects**. Manual user guard, matching SHA-256 token, unique backup and preservation of unresolved snapshots protect common failures. It does not recover a never-saved new project automatically. File-system ownership, noncooperating processes, malicious hard links and catastrophic abrupt power loss remain outside the guaranteed durability envelope. No credentials, private files or real scene footage were used in regression tests.
