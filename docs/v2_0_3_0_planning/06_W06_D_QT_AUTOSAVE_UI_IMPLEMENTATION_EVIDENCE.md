# STEP 06 / W06-D — Approved Qt UI, Autosave Timer and Recovery Integration

**Repository:** `inoriko920-dev/V2-AI-Video-Composer` ONLY. **Date:** 8 October 2026 WIB.  
**Prior baseline main:** `36e8d2d2db2799ad71d541f7fd353f6eb7d153fa` (W06-C, PR #59).  
**Stable tag:** `v0.2.2` -> `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef` (immutable).  
**Gate:** W06-D candidate, PASS only after full final-head PR CI, CodeQL, backend and Windows user acceptance and main merge.

## User authorization and immutable design constraints

A **new user instruction "lanjutkan"** after W06-C PASS authorized **W06-D only**. STEP03-R's three approved dialog reference PNGs and final image-filled DOCX were already reviewed, approved and merged via PR #54. The old 13-image requirement is superseded. The white-blue 42-screen UI shell, navigation, preview, timeline and right-side AI panel must remain **unchanged**.

## Changes in this wave

1. **`src/aavc/presentation/dialogs/recovery_choice.py`**: exactly three user-approved scenarios. `RecoveryChoiceDialog` handles DLG-01 normal verified and DLG-02 uncertain. Conflict requires a second *state in the same modal component*; default Cancel is safe. DLG-03 uses existing native QMessageBox styling and **never provides Restore** for an invalid snapshot. Other minor errors reuse existing message/status UI; no fourth mockup or redesigned editor.
2. **`src/aavc/presentation/windows/recovery_main_window.py`**: adds a thin leaf subclass of the existing `BackgroundWorkMainWindow` so all other UI inheritance, routes, menus, toolbar, preview and timeline stay intact. Owns one Qt parented periodic scheduler timer, one application-thread `RecoveryCoordinator`, one `RecoveryTransactions`, one `ProvenanceStore`, and a single-worker `ThreadPoolExecutor`. No new ProjectSession/history.
3. **`src/aavc/bootstrap/startup.py`**: runtime factory uses `create_recovery_main_window` instead of the old background factory. The `--foundation-smoke` CLI branch still short-circuits before loading Qt and the published version remains `0.2.2`.
4. **`src/aavc/presentation/windows/guarded_main_window.py`**: changes only the existing unsaved-change dialog's Save callback from `super().save_project()` to `self.save_project()` so it routes through the new guarded/manual Save transaction. Its original QMessageBox text, buttons, default Save/Discard/Cancel, precedence and geometry are untouched.
5. **`tests/unit/test_v2_0_3_0_w06_d_recovery_ui.py`**: synthetic, Qt offscreen tests for exact labels, safe default Cancel, second confirmation, invalid-candidate saved-only, old dirty guard precedence, Open cancellation zero-mutation, verified Restore creates old-disk byte backup and opens fresh session, async autosave still dirty, Save retires verified snapshot, Save As collision fail-closed and timer lifetime/shutdown. Pinned PySide6 must match `pyproject.toml`, `6.11.2`.
6. This implementation-evidence file plus planning handoff and `AGENTS.md` top status. **No permanent new workflow.**

## Scheduler and thread guarantees

- Qt timer runs at 250 ms and polls the pure W06-A coordinator on the GUI thread. Due times retain the preapproved **20 s debounce / 120 s cap / 60 s status poll / 30–120–300 s retry** policy; timer frequency does not mean more frequent disk writes.
- On an eligible dirty, already-saved ProjectSession, coordinator emits a detached immutable SnapshotRequest. Worker writes snapshot+descriptor only via existing W06-B ProvenanceStore, under the W06-C shared transaction lock. Qt widgets are never accessed from worker thread.
- Results are collected by a Qt timer callback on the GUI thread; the coordinator's complete() is called there, not in the worker. Active epoch, baseline hash, path and dirty flags are rechecked before the worker writes; a stale request after manual Save/Save As cannot restore a sidecar against the new baseline.
- Concurrent manual Save, Open, Create, Save As or explicit Restore first requires the active worker to finish. A 10-second bounded wait on explicit user action **fails closed** (no operation occurs) if the worker is still running. This may temporarily delay an explicit action on slow disks; it is not silently canceled or deemed successful.
- Timer is paused while any recovery modal or synchronous Save/Create/Open operation is in progress. `aboutToQuit` shuts down the timer, fences the epoch and cancels *queued* worker requests; regular guarded Close is blocked while an in-progress snapshot worker remains active.
- Autosave success never calls `ProjectSession.save`, changes `is_dirty`, clears title `*`, or writes an Undo entry. Status uses **existing QStatusBar** only. No Qt repaint/selection/playback ticks produce project revisions.

## Decision flow and errors

1. Existing unsaved-session `QMessageBox` **must run before** any target project candidate inspection. Save executes the safe W06-C transaction. User Cancel stops the Open.
2. `probe_open` checks the selected file without mutating current project or file. No snapshot -> open the saved file; VERIFIED -> DLG-01; UNCERTAIN -> DLG-02 with second click; INVALID -> native DLG-03 offering only saved version or Cancel.
3. Cancel/Esc leaves previous session, disk, autosave and Undo/Redo untouched.
4. `Restore` and `Use saved` call the W06-C transaction service, which checks the candidate again before changing disk. Failed revalidation shows `Data proyek berubah. Periksa ulang.`.
5. A `RecoveryCommitPartial` error **must not** say old disk was never changed. Use the existing native warning style; preserve pre-recovery backup and forensic snapshot.
6. UI restore completion refreshes selected scene, title, validation badge and editor route through existing methods. No second history stack or silent auto-Restore.

## Genuine RED → GREEN evidence

- UI test file first committed as `c540f806fae0d6e9682e67a03d7af2e01dcb81a2`, **before either new Qt module existed**.
- One-time GitHub Actions workflow checked out that historical test-only commit (full-depth checkout) and verified an import-time missing `aavc.presentation.dialogs.recovery_choice` failure: genuine **RED**, not merely missing libEGL.
- Later same one-time workflow returned to final branch head with pinned Qt `6.11.2` and required Linux EGL libraries: focused **GREEN** `14 passed` in GitHub Actions run `37754531463`. Initial environment/fixture failures were corrected by pinning the repository Qt version and valid serializer fixture; baseline application serializer was not weakened.
- Temporary proof workflow deleted before PR. PR-head full CI, CodeQL, Windows portable screenshot parity and smoke, backend spike must pass before W06-D becomes PASS.

## Boundaries, follow-up, and known limits

- This wave wires **a best-effort crash recovery path for previously saved projects only**, not unsaved never-Save projects, cloud backup, live render jobs or an unconditional zero-loss guarantee.
- Python in-process lock and SHA comparison are not OS-level atomic CAS against all external processes. Power loss / abrupt termination between two sidecar writes produces an UNCERTAIN candidate, intentionally never silently restored.
- Qt offscreen tests are synthetic; they are not a substitute for manual user acceptance of UI reference images (already approved) and real Windows portable acceptance. Confirm baseline STEP09 screenshots aren't changed by the new leaf subclass.
- Worker thread shutdown is safe for regular guarded Close; forced kill cannot promise a finished write. Native Qt recovery overlays are scoped; **no new interface design or approved-image changes** in this wave.
- Status messages report snapshot success only for completed valid write of captured revision, not a promise that a subsequent newer edit is protected.
- W06-E (final cross-wave regression, failure-injection acceptance, packaging, release readiness) **must not begin in this turn** and requires a separate user instruction after W06-D PASS.

## Gate

W06-D is **HOLD** until the final PR head passes CI/Ruff/mypy/pytest, CodeQL, backend and Windows user acceptance (including portable EXE smoke and native shell screenshot). Diff must remain W06-D code/test/status/evidence, original reference images unchanged; merge to `main` and verify branch head/source files as well as stable tag immutability. Any failure -> fix W06-D only, rerun all required checks, never merge red tests.

**NEXT after confirmed W06-D PASS:** separate **W06-E** acceptance/release preparation, **not** an automatic push/release.
