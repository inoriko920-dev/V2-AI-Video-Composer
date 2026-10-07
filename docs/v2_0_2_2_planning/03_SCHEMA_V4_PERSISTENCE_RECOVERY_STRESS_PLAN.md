# STEP 03 — V2 0.2.2 Schema-v4 Persistence / Recovery Stress Plan

Status: **PASS / PLANNING ONLY**

Audited main: `4ca68ab5d9b670ff74a3253d4498b6f1e2dfd0c9`  
Frozen stable release: `v0.2.1` @ `eb94efebf142ba8203dfc3ae3c5fa861222a0926`

## Purpose

STEP 03 defines release-blocking stress/regression coverage for persistence and recovery around schema v3/v4. It does not change runtime code.

The plan covers:
- first v3 -> v4 overwrite backup;
- non-clobbering `.pre-schema-v4.bak` semantics;
- repeated Save and Save As;
- autosave snapshots across v3/v4 and Undo/Redo;
- explicit recovery across schema boundaries;
- schema downgrade prevention;
- future-schema and advanced-contract mismatch rejection;
- atomic temporary-file cleanup;
- failure injection / crash-like interruptions;
- session path, dirty baseline and history preservation on failures.

## Current implementation evidence

### Serializer / normal save

`save_project()` currently:
- serializes and validates the candidate before replacing the destination;
- writes to a unique sibling `.aavc-save-<uuid>.tmp`;
- reads the existing destination schema when possible;
- blocks overwrite when existing schema is newer than the candidate unless downgrade is explicitly allowed;
- creates a migration backup when existing schema < candidate schema;
- does not overwrite an existing migration backup;
- atomically replaces the destination from the temporary file;
- removes its temporary file in `finally`.

The first v3 -> v4 overwrite therefore uses:
`<project>.aavcproj.pre-schema-v4.bak`.

### ProjectSession

`ProjectSession` currently:
- mutates active path/saved baseline only after repository save succeeds;
- preserves the current live session when Open fails;
- preserves dirty state after failed Save/Save As;
- makes Save As the new active path only after successful persistence.

### RecoveryManager

`RecoveryManager` currently:
- uses `<project>.aavcproj.autosave`;
- writes snapshots through `save_project(... create_schema_backup=False, allow_schema_downgrade=True)`;
- validates a snapshot before touching the project during restore;
- uses a unique sibling `.aavc-restore-<uuid>.tmp` for restore;
- copies the pre-restore project to `<project>.aavcproj.pre-recovery.bak`;
- atomically replaces the project with the validated recovery snapshot;
- can clear a snapshot.

Existing tests already prove several happy paths and some failure paths, including future-schema rejection, invalid recovery fail-closed behavior, schema-v4 no-downgrade, non-clobbering schema migration backup, and autosave v4 -> v3 following Undo.

## Confirmed / test-first gaps discovered by STEP 03

### GAP-03A — recovery service is not wired into the production runtime

A full source scan finds `RecoveryManager` usage only in `src/aavc/persistence/recovery.py` and tests. `FoundationServices`, startup, `ProjectSession`, and current presentation windows do not instantiate or call it.

Therefore the codebase has a recovery engine, but the real application path does not currently prove:
- periodic/on-change autosave creation;
- snapshot cleanup after a successful normal save;
- detection of a recovery snapshot when opening a project;
- user choice to restore or discard a snapshot;
- live-session behavior after restore.

Decision: treat this as a **confirmed static integration gap**. Do not implement it in STEP 03. Later implementation must be test-first and must not redesign the main UI.

### GAP-03B — valid repeated recovery can overwrite `.pre-recovery.bak`

`restore_snapshot()` uses `shutil.copy2(project, backup)` whenever the project exists. Unlike `.pre-schema-v4.bak`, it does not guard against an existing recovery backup.

A second successful restore can therefore replace the first pre-recovery backup.

Decision: add a regression test that defines required preservation semantics before changing code. Preferred safety policy is non-clobbering preservation of the earliest pre-recovery state or deterministic numbered backups; exact implementation is deferred to STEP 05/06.

### GAP-03C — malformed existing destination has no readable schema guard

`_existing_schema_version()` returns `None` for unreadable/corrupt JSON. A subsequent `save_project()` can then replace that destination without creating a schema backup because the old schema is unknown.

This is an edge-case data-loss risk, especially for Save As onto an existing damaged project file or external modification between Open and Save.

Decision: test-first. Expected v0.2.2 behavior is fail closed for an existing unreadable project destination unless a separately designed explicit replacement action is authorized.

## Stress model

STEP 03 separates four persistence channels:

1. **Normal Save** — preserve schema safety and current active path.
2. **Save As** — change active path only after success and protect the destination independently of the source path.
3. **Autosave Snapshot** — may follow current in-memory schema in either direction and must not create migration-backup clutter.
4. **Explicit Recovery Restore** — may intentionally cross schema boundaries after snapshot validation, while preserving a pre-restore copy of the disk project.

These channels must never silently inherit each other's downgrade/backup rules.

## Planned regression matrix

### PRS-01 — first v3 -> v4 normal overwrite creates exact backup
- create `.pre-schema-v4.bak` before replacement;
- preserve exact original v3 bytes;
- persist v4 + advanced-v1 + advanced tracks;
- no save temp remains.

### PRS-02 — repeated v4 Save never clobbers first schema backup
The first migration backup remains byte-identical through later v4 saves.

### PRS-03 — failed v3 -> v4 serialization creates no backup or partial destination
Invalid candidate must leave destination, backup, temp state and session saved baseline untouched.

### PRS-04 — backup-copy failure fails closed
Injected migration-backup copy failure must leave the project byte-identical and temp cleaned.

### PRS-05 — atomic replace failure preserves old project
Injected final replace failure may leave a completed backup, but must not expose a partial/new project.

### PRS-06 — v4 normal Save cannot downgrade to v3 after Undo
Disk v4 + in-memory v3 normal Save must raise `SCHEMA_DOWNGRADE_BLOCKED`, preserve disk bytes and keep session dirty.

### PRS-07 — v3 Save As to fresh path is allowed
A fresh destination may receive the current v3 state because there is no newer destination schema to protect.

### PRS-08 — v4 Save As to fresh path does not create migration backup
Fresh target writes v4 directly; no `.pre-schema-v4.bak` is expected.

### PRS-09 — v4 Save As over existing v3 target protects target bytes
Backup must contain the target's prior bytes, not source-project bytes. Active session path moves only after success.

### PRS-10 — v3 Save As over existing v4 target is blocked
Target v4 bytes, original active path, dirty state and history must remain unchanged.

### PRS-11 — failed Save As never changes active path
Any persistence-stage failure retains the old active path.

### PRS-12 — repeated Save / Undo / Redo tracks saved baseline exactly
Exercise Save v3 -> advanced edit -> Save v4 -> Undo v3 -> blocked Save -> Redo v4 -> Save and assert exact dirty/history/schema/disk checkpoints.

### PRS-13 — autosave v3 -> v4 creates no schema migration backup
Autosave can become v4 without creating project or autosave migration backup clutter.

### PRS-14 — autosave v4 -> v3 after Undo is allowed
Recovery snapshots deliberately allow schema downgrade and must remain backup-clutter free.

### PRS-15 — autosave atomic-write failure preserves previous snapshot
Prior valid autosave stays byte-identical; real project is untouched.

### PRS-16 — corrupt/future/mismatched autosave fails closed
Reject malformed JSON, invalid structure, future schema, missing/invalid v4 marker and illegal v3 advanced marker before mutation.

### PRS-17 — explicit recovery v3 project <- v4 autosave
Preserve exact v3 pre-recovery copy, restore v4 atomically, reopen as valid advanced-v1.

### PRS-18 — explicit recovery v4 project <- v3 autosave
Explicit recovery may cross downward to validated v3 while preserving the pre-restore v4 copy.

### PRS-19 — repeated valid recovery must preserve backup history
Two successful restores must not silently destroy the only earlier pre-recovery state. This is expected to expose GAP-03B before implementation.

### PRS-20 — restore backup-copy failure preserves project and snapshot
No restore temp; project and snapshot remain retryable.

### PRS-21 — restore temp-copy failure preserves project and backup
Snapshot remains available for retry.

### PRS-22 — restore replace failure preserves readable disk project
Project, backup and snapshot remain valid; temp cleanup occurs.

### PRS-23 — successful normal Save clears/invalidates stale autosave according to runtime policy
Once GAP-03A is wired, an older recovery snapshot must not be offered as newer state after successful Save. Use deterministic state/freshness logic, not wall-clock-only assumptions.

### PRS-24 — opening project with recovery snapshot is deterministic
- no snapshot => normal Open;
- invalid snapshot => fail/ignore safely with user notice;
- valid differing snapshot => explicit Restore / Discard / Cancel;
- Cancel preserves previous live session;
- Discard removes snapshot only after explicit choice;
- Restore validates and loads restored state.

### PRS-25 — recovery prompt never bypasses unsaved-current-project guard
Resolve the current dirty-project guard before applying target-project recovery decisions.

### PRS-26 — corrupt existing destination cannot be silently overwritten
Save As over malformed existing `.aavcproj` should fail closed and preserve existing bytes unless a separately planned explicit replacement path exists. Expected failing-before gap.

### PRS-27 — future-schema disk project cannot be replaced by normal Save
If disk changes externally to schema 5, normal Save must fail closed rather than treating it as an unknown safe target.

### PRS-28 — schema/marker mismatch never becomes live session
Open/Recovery rejection leaves current session project, path, dirty state, Undo and Redo unchanged.

### PRS-29 — unique temp names do not touch user-owned legacy temp files
Preserve the guarantee that fixed `.tmp` / `.restore.tmp` files are never touched.

### PRS-30 — Unicode/space/apostrophe/deep path persistence smoke
Windows acceptance repeats representative Save/Save As/backup/recovery under supported path variants and verifies schema/checksums.

## Runtime recovery integration contract

If STEP 05 authorizes GAP-03A correction, use the existing `RecoveryManager` rather than a second persistence engine.

Minimum behavior:
1. one runtime owner/composition point;
2. bounded snapshot creation on meaningful state changes and/or modest timer, never paint/UI events;
3. snapshot write failure is non-fatal and never marks normal Save successful;
4. current-project unsaved guard resolves before target recovery handling;
5. valid recovery requires explicit Restore / Discard / Cancel;
6. restore uses the existing validation + atomic restore path;
7. successful normal Save clears or deterministically invalidates obsolete recovery state;
8. failed Save never deletes the only useful recovery snapshot;
9. autosave/recovery never promotes v3 to v4 by itself;
10. no new storage format/database/persistence engine.

No new permanent panel or main-window redesign is required.

## Failure-injection strategy

Use deterministic monkeypatch/fake filesystem boundaries:
- temp write failure;
- `shutil.copy2` migration-backup failure;
- `Path.replace` normal-save failure;
- autosave replace failure with a prior valid snapshot;
- recovery pre-backup copy failure;
- recovery snapshot-to-temp copy failure;
- recovery final replace failure;
- repository failure observed through `ProjectSession`.

Every failure test must verify:
- destination bytes;
- backup bytes;
- autosave bytes;
- temp-file absence;
- session path/current state;
- saved baseline / `is_dirty`;
- Undo/Redo availability.

## Planned test files

Likely new tests after STEP 05 authorization:
- `tests/unit/test_v2_0_2_2_schema_v4_save_stress.py`
- `tests/unit/test_v2_0_2_2_recovery_stress.py`
- `tests/unit/test_v2_0_2_2_persistence_failure_atomicity.py`
- `tests/integration/test_v2_0_2_2_runtime_recovery_lifecycle.py` only if GAP-03A is authorized.

Extend where ownership fits:
- `tests/unit/test_v2_schema_v4_contract.py`;
- `tests/unit/test_project_session.py`;
- `tests/unit/test_save_as.py`;
- `tests/unit/test_step11_persistence_recovery.py`;
- `tests/unit/test_astra_persistence_validation.py`.

Probable application files later authorized only by failing tests:
- `src/aavc/persistence/serializer.py`;
- `src/aavc/persistence/recovery.py`;
- `src/aavc/application/services/project_session.py`;
- runtime composition/UI glue only if GAP-03A is included by STEP 05.

Do not pre-authorize schema v5, a new storage backend, database migration, or project-format redesign.

## Release-blocking acceptance criteria

Persistence/recovery implementation is not complete until:
- all applicable PRS-01 through PRS-30 cases pass;
- existing v1/v2 -> v3 migration tests pass;
- existing v3/v4 contract tests pass;
- existing Save/Save As/session tests pass;
- no normal-save downgrade path exists;
- first v3 -> v4 backup remains non-clobbering;
- future schema / marker mismatch fail closed;
- failure injection exposes no partial project file;
- no tested failure leaves application-owned temp debris;
- Windows path smoke passes;
- no UI redesign or new runtime dependency is introduced.

If runtime recovery integration is deferred by STEP 05, GAP-03A and its runtime-only PRS cases must be explicitly marked deferred; they may not be silently described as implemented.

## Stop conditions

Implementation must STOP rather than broaden the patch if:
- a fix requires schema v5;
- recovery requires a second project format/storage engine;
- preserving atomicity requires abandoning the existing temp/replace model;
- normal Save would need to allow v4 -> v3 overwrite;
- recovery UX requires main-window redesign;
- corrupted/newer destination protection cannot be made deterministic without a broader product decision.

## STEP 03 gate

**PASS**

The schema-v4 persistence/recovery risk surface is now converted into deterministic stress cases. Existing safety mechanisms are preserved, while GAP-03A, GAP-03B and GAP-03C are explicitly test-first and remain unfixed during planning.

No application runtime code has been changed.

## Next exact STEP

**STEP 04 — Windows Packaging / Dependency Maintenance Plan**

STEP 04 must audit:
- Windows portable build and verifier;
- pinned Python dependencies and Actions;
- FFmpeg/ffprobe external/app-local policy;
- artifact reproducibility/checksums;
- package/runtime secret cleanliness;
- safe dependency refreshes from current main;
- packaged-EXE regression gates for v0.2.2.

Do not begin STEP 05 or implementation in the same turn.
