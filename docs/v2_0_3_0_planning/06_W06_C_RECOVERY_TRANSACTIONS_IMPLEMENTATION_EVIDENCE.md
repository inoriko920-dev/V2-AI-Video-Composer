# STEP06 / W06-C — Transaction Integration, Recovery Safety & Evidence

**Project:** V2-AI-Video-Composer only. **Date:** 8 October 2026 WIB.  
**Prior main:** `3714e2f46a2ef4a8cfd4bf7c39457548a1bf256c` (W06-B PR #58 merged).  
**Stable tag remains immutable:** `v0.2.2` -> `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.

## User authorization and scope

The new standalone user instruction **"lanjutkan"** after W06-B PASS authorized **W06-C only**. New changes implement a synchronous, UI-neutral transaction service around the single canonical ProjectSession and existing W06-A scheduler / W06-B ProvenanceStore. This is not a released or UI-attached v0.3.0 autosave feature.

Changed production files:
1. `src/aavc/application/services/recovery_transactions.py` (new): Save, Save As, read-only Open preflight, Cancel no-op, use-saved/Discard, Restore with numbered non-clobber backup, and explicit `persist_due_snapshot` for queued W06-A SnapshotRequests.
2. `src/aavc/application/services/project_session.py`: read-only SHA-256 fingerprint `saved_disk_sha256` maintained after initial project start, create, open and normal manual Save; existing Undo/Redo semantics retained.
3. `src/aavc/persistence/snapshot_provenance.py`: exposes narrow shared `locked_transaction()` context manager backed by the existing process-global RLock, allowing Save and Restore to serialize with snapshot writes. Existing file format and metadata validator unchanged.
4. `tests/integration/test_v2_0_3_0_w06_c_recovery_transactions.py`: 32 synthetic test cases including parameterized cases, rollback and deterministic fault hooks. Never touches user projects or credentials.

## Safety contracts now covered

- **Manual Save:** compares current real project SHA-256 to the last saved/open baseline before overwrite; stages only a VERIFIED owned snapshot into quarantine first. On persistence failure, rolls quarantine back and leaves dirty state, path, history and original disk unchanged. On success, advances the *real* ProjectSession baseline and fences stale scheduler callbacks. If cleanup after successful Save fails, reports `SAVE_CLEANUP_PARTIAL` rather than pretending Save was undone.
- **Uncertain recovery:** deliberately never deletes or overwrites an untrusted snapshot/meta pair. A successful manual Save leaves it intact but cannot classify it as VERIFIED against the new disk baseline.
- **Save As:** refuses pre-existing targets or sidecars/snapshots, rechecks collision immediately before save, and rebinding occurs only after successful ProjectSession persistence. Does not delete recovery files at previous location.
- **Open probe:** enforces old-session dirty guard first; read-only preflight checks real disk bytes, parses valid schema and takes a candidate token. Cancel/Escape is a complete no-op; UI dialog is a separate W06-D implementation.
- **Use saved / Discard:** after explicit user selection, rechecks disk/snapshot/metadata hashes, quarantines only the selected candidate, opens the durable disk into a fresh canonical session, and then retires the quarantined pair. Failed pre-adoption restores original quarantine; a rollback collision reports `DISCARD_ROLLBACK_PARTIAL` and cannot overwrite competing files.
- **Restore:** valid snapshot may restore after explicit user choice. UNCERTAIN requires an additional conflict-confirmation flag. Creates an exclusive numbered pre-recovery backup of the exact old disk bytes; prepares a same-directory temporary copy with fsync; rechecks all preflight digests immediately before atomic replacement. Old backup is never overwritten. If disk replace succeeds but new ProjectSession adoption fails, raises `RESTORE_COMMIT_PARTIAL` including backup-path attribute, never asserts that on-disk project stayed unchanged.
- **W06-A/W06-B bridge:** `persist_due_snapshot` validates exact in-flight request identity, epoch, dirty state, active path and saved byte baseline under the same process lock. Reports completion back to W06-A; successful capture cannot mark manual Save or erase Undo; stale callback after Save cannot publish verified newer snapshot.
- **No UI / release mutation:** no QTimer, PySide6 recovery dialogs, editor redraw, 42-screen frozen reference changes, 3 approved recovery PNG changes, schema/FFmpeg/provider/version bump, or new release.

## RED → GREEN evidence and traceability

- First test-first commit `d9282877a84da7e3a08762926f4c753c2247087d`; RED workflow commit `1d8ff2a00cd04274534b955e31ab5c20941da5df` and GitHub Actions run `37751809493` **failed collection**, because the new `recovery_transactions` module did not yet exist.
- First implementation `7d92d4c5ba2ae872d0fcc5fc5ae1bdd53c9e2de7`; Actions `37752038375` **21 passed**.
- Fault injection enhancements and preflight hardening Actions `37752271541` **29 passed**.
- Final 3 concurrency/partial-commit checks Actions `37752401663` **32 passed in 0.45s** on Linux, with isolated temporary directories and no wall-clock sleeps.
- Coverage maps RCV-01/04/05/06/07/08/09/10/11/17/19/20/23/24 and AT-10..19 where relevant. Existing W06-A (18) and W06-B (27) test suites must stay green under final-head PR CI. No claim of full UI acceptance (UI-01..12), COMP-01..10, or comprehensive Windows crash/physical power-loss durability.

## Verified boundaries / limitations before W06-D

1. Transaction service is **not yet called by the running editor**. W06-D must route all canonical GUI Save/Open/Save As/Recover/Discard actions through this surface while preserving current Save/Discard/Cancel guard, one QTimer scheduler and user-approved modal UI.
2. `locked_transaction` is in-process only; external processes do not acquire this lock. Rechecking digests immediately before replace reduces TOCTOU but is not an OS-level atomic compare-and-swap across processes. Do not promise protection from malicious concurrent native writers or loss of power.
3. The new W06-C Restore deliberately does not automatically delete a source snapshot after disk replacement. W06-D must decide how redundant content is suppressed/presented; it must never silently trash candidates.
4. Transaction injection hooks are tests-only seams; they must not be invoked by untrusted user scripts or used as a plugin execution surface.
5. File-writing contracts still use the original serializer and support current v3 / advanced-v1 v4; no implicit schema downgrade or migration is authorized.
6. If a post-adoption cleanup cannot complete, preserve the quarantined forensic files and display a localized partial-commit warning in W06-D; do not claim everything was rolled back.

## Merge / next wave gate

**W06-C is HOLD until the final-head PR has PASS for full CI, pinned Ruff, strict mypy, CodeQL, backend spike and Windows portable user acceptance; the diff contains only W06-C files/status docs; branch merges cleanly; main source and stable v0.2.2 tag verified unchanged.**

After confirmed W06-C PASS, **STOP**. W06-D UI/QTimer wiring requires **a separate subsequent user "lanjutkan"**. Do not implement dialog or start release W06-E in this turn.
