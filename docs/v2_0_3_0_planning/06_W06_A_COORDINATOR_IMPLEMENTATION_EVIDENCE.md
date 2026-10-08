# STEP06 / W06-A — Implementation Evidence and SOL Handoff

**Repository:** `inoriko920-dev/V2-AI-Video-Composer` only. **Date:** 8 October 2026 WIB.  
**Previous green main:** `9d2d01833811190edeb9591646f59baa8508bb70` (STEP05 PR #56 merged).  
**Stable immutable tag:** `v0.2.2` -> `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.  
**Status:** W06-A isolated implementation candidate. **Do not call PASS until PR-head CI/CodeQL/Windows/backend are green and PR merged into main.**

## In-scope changes

- `src/aavc/application/services/recovery_coordinator.py`: pure application coordinator with injected monotonic clock, semantic state observation, session epoch, revision, 20/120/60 timing, retries 30/120/300, a single in-flight request, deep-copied request state and stale-completion rejection.
- `tests/unit/test_v2_0_3_0_w06_a_recovery_scheduler.py`: 18 deterministic fake-clock/ProjectSession tests. No wall-clock sleeps, real user files, Qt or external processes.
- No `RecoveryManager` edits, no snapshot IO worker, no `.autosave` or `.meta.json` file creation, no Qt hookup or dialogs, no schema/FFmpeg/provider changes, no dependency or version bump.

## Genuine test-first trace

1. **RED**, commit `08aa552ddd75498cbd9a14704b67728555221ec0`, one-shot GitHub Actions run `37748470074`: the tests could not import nonexistent `aavc.application.services.recovery_coordinator`, `ModuleNotFoundError`; collection failed as intended. No application source existed.
2. First implementation commit `3420da8f346b062abf85012349782b7ef801893d`; follow-up run `37748606171`: **16 passed, 2 failed**. Failures were expectation defects in the new test file: a 13th meaningful edit was expected as revision 12, and another test omitted `tick` at the moment of an observed committed edit. Both test assertions were corrected without weakening 20-second timing or serial-write invariants.
3. Corrected tests commit `f755e54b8830907d7f8c79e19c9d3b72e2cbb40e`; GitHub Actions run `37748722597`: **18 passed in 0.20 s**. All timing is driven by FakeClock on Python 3.12.

## API and invariant summary

- `RecoveryCoordinator(clock=callable)`: future adapter explicitly invokes `tick(ProjectSession)` after canonical edits or periodic poll. `tick` returns `SnapshotRequest | None` and never writes a byte.
- Request captures owner epoch, revision, path, deep-copied project state and first-dirty clock reading.
- `complete(request, success=bool)` accepts **only** the exact in-flight request instance and same current epoch/path; stales return False and cannot mark any newer project as protected.
- `reset_session()` fences same-path reload and changes; `close()` invalidates future dispatch; `set_paused()` is available to modal/switching adapters.
- `next_poll_at`, `next_due_at`, `next_retry_at` support injected Qt scheduler in W06-D. 120-second cap is an eligibility deadline only, not a guaranteed write-finish deadline.
- Inflight writer slot remains owned until authentic completion even after session change: avoids overlapping jobs. W06-B/C must add **real filesystem queue/lease and disk-side fencing**. Logical callback rejection alone does not prevent a stale physical writer from touching old/new disk files.
- `ProjectState` is dataclass-frozen but nested metadata is a dict; request is deep-copied from the active session to isolate subsequent edits. Future writer may not mutate its request or live session, and must validate the captured state before persistence.

## Wave acceptance mapping

| Requirement | W06-A proof | Remaining work |
|---|---|---|
| SCH-01..03 | Fake-clock debounce, latest edit and 120s cap | Bind Qt timer in W06-D |
| SCH-04..05 | Non-forcing 60s poll and 30/120/300 retry | Connect real writer outcomes in W06-B |
| SCH-06..08 | Clean/unsaved/no-op/Undo cancel and semantic revision | Canonical command notification bridge W06-C/D |
| SCH-09..12 | Global in-flight token; stale epoch, close, path switch | Physical path lease/fence W06-B/C |
| RCV-01..03 | No mutation by scheduling; dirty/history preserved | **Valid disk autosave** specifically deferred to W06-B |
| RCV-15,21,22 | Pause, stale callback, no-op suppression and session fences | UI reentrancy and actual Save/write interleaving W06-C/D |

## Gate and rollback

Before merging: inspect PR changed paths, Python compile, Ruff, strict mypy, all project tests, CodeQL, Windows portable end-to-end acceptance, backend spike. A **green W06-A** does not mean v0.3.0 automatic crash recovery is shipping; no session/Qt binding or disk writer is present yet.

If any test regresses, block PR or revert W06-A PR without rewriting published release tags. Once PR is merged and main verified, W06-B is NEXT only on a *new* explicit user command. **No W06-B work in this turn.**
