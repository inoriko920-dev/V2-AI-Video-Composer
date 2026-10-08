# STEP 02 — V2 0.3.0 Recovery Architecture, Atomicity and Scheduler Plan

**Status: ASTRA PLANNING / implementation NOT authorized.**
**Date/time reference:** 8 October 2026 WIB. **Audited main:** `fc587f82ce61c2f5438cc32c6f315c232e80c091`. **Stable protected tag:** `v0.2.2` at `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.
**Earlier contracts:** STEP00 `00_PRODUCT_GAP_AUDIT_AND_RECOVERY_SCOPE.md` and STEP01 `01_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.md` are authoritative. This STEP02 refines **how** without silently revising user-facing STEP01 decisions.
**Next:** STEP03 **UI IMAGE PROMPT HARD STOP** on a new explicit user request, not during this turn. Published releases and legacy repository are strictly immutable.

## 01. Architecture outcome and non-negotiable constraints

The proposed v0.3.0 GAP-03A implementation connects one existing `ProjectSession` to one existing `RecoveryManager` through **one application-level recovery coordinator** and one Qt scheduling adapter. Snapshot writes are serialized with user-triggered Save/Save As/Open/Restore/Discard and with close/switch fences. No second serializer, duplicate project-state/history engine, schema v5 or silent API key persistence is allowed.

**Evidence from audited code**:
- `src/aavc/persistence/recovery.py` contains RecoveryManager.write_snapshot/load_snapshot/restore_snapshot/clear_snapshot and non-clobbering pre-recovery backup creation.
- `src/aavc/persistence/serializer.py` handles unique temporary siblings, schema/future-format validation, atomic replace; all user project writes must continue through this canonical serializer.
- `src/aavc/application/services/project_session.py` owns path/current, saved baseline, is_dirty, execute, undo, redo, create/open/save. Successful normal save alone advances the saved baseline.
- `src/aavc/presentation/windows/guarded_main_window.py` defines unsaved Save/Discard/Cancel and close/background guards. Its guard **must run before** checking a target recovery file; do not bypass.
- `src/aavc/bootstrap/composition_root.py` builds FoundationServices, the natural single lifecycle owner injection location.
- `src/aavc/bootstrap/startup.py` owns QApplication startup and app teardown.
- `src/aavc/presentation/windows/background_work_window.py` already owns render/AI QTimer polling and background jobs; recovery scheduling must not repurpose or race that UI loop.

**Frozen boundaries:** Python runtime package remains 0.2.2 until authorized later; schema max v4 and advanced-v1 unchanged; 21 native effects and Gemini provider contract preserved; external FFmpeg not redistributed; 42 previously approved white-blue UI screens retained; v0.3.0 recovery-specific visuals go through independent STEP03 prompt/image/DOCX review.

## 02. Component topology and ownership (proposed, not created)

| Component | Architectural layer | Single responsibility | Explicit prohibition |
|---|---|---|---|
| ProjectSession | application | Canonical project, saved baseline, dirty flag, Undo/Redo; emits committed-revision notifications | No Qt imports, no hidden autosave-as-normal-save |
| RecoveryCoordinator | application, NEW at later authorized STEP06 | Eligibility, epoch/revision, scheduling deadlines, open preflight, decision token, serialization locks, statuses | No competing history or mutable second ProjectState |
| RecoveryManager | persistence, EXISTING | Snapshot byte IO, schema-safe read/write/restore/clear, numbered backups | No Qt dialogs, no automatic clock decisions |
| SnapshotProvenanceStore | persistence adapter, NEW if later approved | Tiny validated sidecar descriptor bound to snapshot/project digests; race-safe atomic sidecar write; quarantine | No secret or full project body; no unsupported schema migration |
| MonotonicClock + Scheduler | application port + Qt adapter | Convert 20s debounce, 120s cap and bounded retry to scheduled ticks; injectable fake clock | No direct file writes in Qt timer |
| SnapshotIOExecutor | application job adapter | Single serial writer, capacity 1 and cancellation/generation-safe results | Never parallelize Save and snapshot for same path |
| RecoveryChoiceDialog | presentation, ONLY after STEP03 approved UI | Restore/Discard/Cancel + conflict extra confirmation; localized states | No business logic or file deletes in view |
| GuardedMainWindow bridge | presentation | Preserve existing dirty guard; orchestrate target preflight then session commit and visual refresh | Never replace current session on tentative Open |
| FoundationServices / startup | bootstrap | Compose exactly one coordinator, start/stop worker/timer on app lifecycle | No orphan worker after QApplication exits |

**Layer rule:** Qt presentation -> application coordinator -> persistence ports/RecoveryManager. Domain remains Qt- and filesystem-independent. Worker callbacks report immutable completion records only; only main UI thread touches QObject/widgets. Core semantics should be testable without importing PySide6.

## 03. Proposed precise integration / change map (PLANNING, no source changes)

| Existing or candidate path | Intended future change | Test gate |
|---|---|---|
| src/aavc/application/services/project_session.py | Narrow read-only revision/session-token observation and commit hooks for execute/execute_many/undo/redo/save/open/create | Session dirty/history tests; no mutation from background snapshots |
| src/aavc/application/services/recovery_coordinator.py (NEW) | Orchestrate state machine, capture immutable candidate, ownership/provenance, locks and statuses | Fake-clock unit + race/failure integration |
| src/aavc/application/ports/recovery_schedule.py (NEW or existing ports subpackage) | Clock, scheduling and snapshot writer interface, typed errors | Port contract tests and no Qt import |
| src/aavc/persistence/recovery.py | Reuse APIs; extend only if necessary for safe ownership, quarantine or revalidation while keeping existing tests green | Repeated backup and race tests |
| src/aavc/persistence/snapshot_provenance.py (NEW, conditional) | Strict sidecar serialization, bounded parser, SHA-256, same-folder atomic replace, unknown fields safely handled | Corrupt, symlink/rename and interrupted write |
| src/aavc/bootstrap/composition_root.py | Compose single coordinator and adapters with project session and manager | Startup single-owner, shutdown |
| src/aavc/bootstrap/startup.py | Own Qt scheduler lifetime, flush/teardown policy | Headless Qt close smoke |
| src/aavc/presentation/windows/guarded_main_window.py | Extend **existing** Open/New/Close unsaved guard with recovery preflight bridge; preserve original guard order | Qt offscreen modal/Cancel tests |
| src/aavc/presentation/windows/main_window.py | Error/status and post-commit refresh, only through approved UI | Existing 42 UI screenshot parity |
| src/aavc/presentation/dialogs/recovery_choice.py (NEW after UI gate) | Real Qt choices and conflict state according to final approved UI DOCX | A11y/keyboard/screenshot states |
| tests/unit/test_v2_0_3_0_recovery_coordinator.py (NEW) | Fake-clock and revision/generation acceptance RCV-01..24 | Deterministic repeated tests |
| tests/integration/test_v2_0_3_0_recovery_runtime.py (NEW) | Crash windows, disk corruption, path races, Save As, file locking | Windows/CI verified |
| tests/qt/test_v2_0_3_0_recovery_dialog.py (NEW or existing Qt suite) | Modal state/unsaved precedence/Cancel, preview integrity | Offscreen UI screenshots |

No paths in this table constitute coding authorization; STEP05 must independently verify actual module layouts, licensing, freeze references, and precise approved file changes before SOL can touch them.

## 04. Scheduler algorithm and monotonic state model

**STEP01 cadence is retained:** debounce 20 seconds from the most recent committed meaningful state edit; hard upper bound 120 seconds from the first unsnapshotted eligible dirty state; 60-second periodic check of unsnapshotted dirty state; error retry steps 30s, 120s, then >=300s. This is a **functional target**, not an implemented claim.

**Inputs:** monotonic `now`, canonical project path identity, `session_epoch`, `state_revision`, persisted-baseline fingerprint, `dirty_since`, `last_edit_at`, `last_snapshot_revision`, `next_retry_at`, pending writer and modal/switch/shutdown flags. The in-process epoch changes on Open, Create, successful Save As rebind and destruction; state revision changes only when canonical current value actually changes after execute/undo/redo.

**Due rule:** schedule only if `has_path && is_dirty && revision != last_successfully_snapshotted_revision && no_inflight && !modal && !switching && !closing`. Earliest normal due time is `min(last_edit_at+20s, first_unsnapshotted_dirty_at+120s)`; when no new edits but still unsnapshotted, 60s housekeeping checks can trigger any already-due work. After failures, `max(normal_due, next_retry_at)` applies. No periodic write occurs when current ProjectState is semantically equal to already persisted or last successful candidate. No external file path is invented.

**Maximum deadline semantics:** 120s is a best-effort *eligibility scheduling upper bound*, not a real-time IO finish guarantee. Read-only filesystem, modal recovery, shutdown and a busy writer can defer safely; user-facing status must not promise guaranteed protection. Fake-clock assertions use tolerance for UI event-loop scheduling but no sleep-based flakiness.

**Immutable capture:** capture a validated immutable ProjectState plus owning epoch/revision and expected saved-disk baseline under the coordinator lock before passing it to serial worker. If the project cannot be frozen or is invalid, do not schedule an IO write. At most one IO operation per target path at a time and globally one snapshot writer per app instance.

**Late callback:** completion token carries epoch, path, input revision and digest. If stale, do not set the current session's last-success revision or status. A completed disk write for an old path is never silently rebound to a new project. A new pending dirty revision will receive its own due deadline.

## 05. File-level data contract and provenance sidecar decision

**Decision:** keep the existing `<project>.aavcproj.autosave` exactly as valid ProjectState JSON. Add a **small sibling JSON provenance descriptor** at `<project>.aavcproj.autosave.meta.json` (new feature only; proposed metadata format version 1). Do not add fields to the `.aavcproj` or autosave ProjectState schema.

**Proposed descriptor fields:** `format_version=1`; `project_path_identity` = canonical, normalized path binding (do not log raw paths); `saved_baseline_sha256` of actual disk bytes as seen during capture; `snapshot_sha256` of saved autosave bytes; `schema_version` (3 or 4); optional non-secret `animation_contract` marker; `write_generation` (opaque per-run operation ID only, not an authorization token). Maximum descriptor size 16 KiB; keys must be type-checked; no arbitrary extra payload or credentials. The descriptor is *untrusted user-writable metadata*: hashes detect accidental mismatch/changes but **do not authenticate adversarial tampering**.

**Canonical path binding:** use `Path.resolve(strict=False)` and platform-aware case normalization only after checking file existence and symlink policy. Store a **hash of canonical path bytes** rather than display the raw absolute path in metadata/logs, but note that a path hash does not prevent an attacker who controls both files from forging identity; STEP04 must test symlink/rename/Windows junction aliasing.

**Digest requirements:** use SHA-256 over actual file bytes, not a pretty-printed JSON serialization or mtime. Disk baseline read and validation must come from the same guarded identity boundary (stat/read/stat or handle-based identity proof as appropriate). Avoid TOCTOU by checking content digest **again immediately before every destructive commit**.

**Writes are a two-file protocol; never claim one atomic transaction across both files.** The serializer atomically replaces snapshot first. The metadata descriptor is written to unique same-directory temporary file, fsynced as supported, and atomically replaced *after* snapshot success. A crash between these writes produces a snapshot without matching metadata -> `RECOVERABLE_UNCERTAIN`, not a silently verified candidate. If metadata is stale while snapshot newer, validate actual snapshot first, then classify uncertain.

**Legacy v0.2.2 metadata-free .autosave** is still eligible for safe explicit recovery but is **never considered verified solely because its JSON is valid**: open conflict-aware UI with Cancel default. Invalid or missing descriptor never causes automatic deletion.

**No raw Gemini keys, tokens, voice contents, full ProjectState or credentials in metadata, logs or error messages.** Credentials should not already be part of project serialization; STEP04 must prove via fixture scans.

## 06. Serialized mutation boundary and operation order

**One lock/queue per application session:** a coordinator service serializes all operations touching the same project or its associated recovery files. An IO job acquires the path-specific logical lease **before reading source bytes** and holds it until the final snapshot, sidecar, cleanup or Save operation is complete; the UI itself must not block for long work. A Save must wait for or fence an in-flight snapshot before writing the real project.

**Snapshot write sequence:** (1) verify epoch/revision and dirty; (2) acquire single-writer/path lease; (3) read+validate current on-disk baseline and compute digest; (4) compare saved-baseline claim and ownership; if disk externally changed -> abort snapshot and report conflict rather than treat it as new baseline; (5) write through RecoveryManager.write_snapshot with existing atomic tempfile behavior; (6) hash produced snapshot bytes; (7) safely atomically publish matching descriptor; (8) report complete revision/digest; (9) release lease. If an error happens, do not mark success, preserve project and as much prior valid snapshot as possible.

**Manual Save:** (1) guard/snapshot fence and drain overlapping write; (2) canonical ProjectSession.save() attempts project atomic persistence and advances saved baseline only after success; (3) after success, invalidate/retire obsolete recovery candidate safely; (4) update coordinator path epoch and clean scheduling state. A cleanup failure cannot revert successful Save, cannot resurrect stale candidate as verified, and must report status. Before attempting normal Save, confirm disk has not been externally modified since the session's authoritative save/open baseline; STEP02 proposes a stricter compare-and-swap protection over current v0.2.2 behavior, subject to STEP05 acceptance and integration testing.

**Save As:** candidate path preflight checks whether a project or autosave/descriptor already exists. Preserve data under the target path: if target recovery data cannot safely be classified as belonging to the current target identity, **abort with explicit conflict**, never delete/replace target autosave. Only successful canonical Save As rebinding changes active path/epoch. Old path autosave/backups are left intact unless explicit later disposition is separately authorized; no hidden background task may target the old location afterward.

**Open candidate:** current unsaved-project guard from GuardedMainWindow first, then isolated disk+autosave+metadata load without updating ProjectSession. Existing session remains untouched while any recovery dialog is shown. Every choice carries an opaque decision token binding exact source/disk digests; final commit re-evaluates both digests, not just file timestamps.

**Shutdown:** stop issuing new timer events, invalidate epochs, drain/terminate current path IO under bounded policy; preserve durable previous snapshot if a new one cannot complete. A close Cancel resumes original timer/session. No implicit manual Save on Exit.

## 07. Recovery decision transaction and backup mechanics

**Restore:** confirmed recovery from a validated snapshot under the disk baseline verified/uncertain policy. Re-read disk and snapshot; verify decision token byte digests, schema/advanced contract and project ownership status; if any source changed, return `RACE_CHANGED` and re-open decision/Cancel. On approval, RecoveryManager.restore_snapshot validates first, then creates a unique `.pre-recovery.bak` / numbered backup, then replaces original atomically from a same-directory temp. After write, open validated restored state in a *new* canonical ProjectSession history. If post-replace state initialization fails, do **not** pretend old bytes remain: preserve numbered pre-recovery backup, keep prior live session in memory, report partial-commit recovery with explicit backup path. STEP04 includes fault injection for this rare boundary.

**Discard:** commit disk version safely without erasing user data before success. Proposed fail-closed transaction uses a unique quarantine rename of *exactly the candidate autosave and descriptor* after an identity recheck, opens the disk version as a new session, then finalizes retirement. If replacing the active session fails, restore quarantined candidate names where safely possible; if rollback also fails, expose quarantine recovery path rather than claim success. Never delete a different candidate that replaced files after dialog opened. The exact filesystem transaction helper API must be approved in STEP05.

**Cancel or dialog Escape:** zero changes to previous ProjectSession, path, dirty flag, undo/redo, selection or project/autosave/metadata bytes. Stale pending callbacks for the intended new path are invalidated.

**Missing/corrupt target or autosave:** never create a project from a lone autosave automatically; never overwrite unreadable saved content. Warn and either open intact saved project through an explicitly acknowledged safe pathway or remain on old session. Future/unknown schema snapshots remain preserved untouched.

**Duplicate Open:** reopening the already active canonical path without an explicit reload is idempotent and must not relaunch a recovery modal; dialogs cannot be reentrant.

**Backup independence:** restoring a snapshot may legitimately traverse v3 and v4, but it never downgrades the normal Save contract. Numbered pre-recovery backups must preserve each previous disk version byte-for-byte; never truncate existing backup names.

**Forensic limits:** the normal source ZIP is not a Git history backup and .pre-recovery backups are local files only. UI shall not claim cloud backup or permanent undo history.

## 08. Error codes, observability and security

| Error ID | Trigger | User-visible recovery action | Safety invariant |
|---|---|---|---|
| AUTOSAVE_NOT_ELIGIBLE | No durable path, clean project, busy modal | Non-modal status; prompt manual Save if needed | No IO |
| AUTOSAVE_WRITE_FAILED | Disk full/permissions/lock | Non-modal warning + bounded retry | Main file not touched; previous valid snapshot preserved if feasible |
| BASELINE_CHANGED | External process modified saved .aavcproj | Warn, pause automatic writes; ask user to reload/resolve | No automatic overwrite |
| AUTOSAVE_META_UNCERTAIN | Missing/corrupt/old descriptor | Warn on Open; conflict-aware explicit decision | Never silent Restore |
| AUTOSAVE_INVALID_SCHEMA | Corrupt/future model or missing advanced-v1 marker | Fail closed; retain candidate | No accidental migration/downgrade |
| RECOVERY_RACE_CHANGED | Source digest changed during decision | Cancel/stage fresh preflight | Never apply stale approval |
| RESTORE_BACKUP_FAILED | Cannot create exclusive pre-recovery backup | Error; offer retry/Cancel | Target project unchanged |
| RESTORE_COMMIT_PARTIAL | Disk replaced but post-open session commit fails | Error + location of numbered backup (sanitized) | Do not claim complete Restore |
| DISCARD_QUARANTINE_FAILED | Unable to stage/retire selected candidate | Error and no misleading Discard status | Preserve candidate bytes |
| SAVE_AS_RECOVERY_COLLISION | Destination owns other snapshot/sidecar | Abort/choose new path | No collateral deletion |
| TIMER_EPOCH_STALE | Old project/period callback arrived | Silent benign ignore | No new-path write or status update |
| AUTOSAVE_SERIALIZATION_UNSAFE | Candidate fails serializer/schema check | Non-modal error; manual Save available | No invalid snapshot publication |

No raw exception tracebacks, OS user directories, project private text or Gemini keys enter telemetry; logs include only sanitized error ID and correlation-safe operation metadata. A sidecar digest is not encryption or proof against malicious tampering; this is a file-integrity feature, not an anti-adversary authenticity scheme. Avoid sensitive project contents in GitHub test artifacts.

## 09. Sequence trace and failure windows

| Scenario | Operations in time order | Required resulting state |
|---|---|---|
| Normal dirty edit | execute => revision N => 20s debounce => snapshot -> metadata | Project unchanged, dirty remains true, valid candidate bound to baseline |
| Continuous editing | revisions N..M in <120s intervals | At most one serialized writer; hard 120s eligibility cap with newest immutable captured state |
| Undo to saved | Undo yields same ProjectState as saved baseline | Cancel pending due; no unnecessary new snapshot |
| Snapshot crash before sidecar | atomic autosave replaced, old metadata persists | Hash mismatch -> uncertain; no auto-Restore |
| Crash after sidecar | both hashes match, saved baseline unchanged | Verified candidate offered on next Open |
| Manual Save while snapshot IO | acquire fence, wait for worker, canonical Save, invalidate snapshot | Never stale candidate later offered as verified |
| Save failure | repository error before baseline advance | Is_dirty and prior candidate preserved; warn |
| Save As path collision | target project or sidecar belongs elsewhere | Abort; leave both paths and backups unchanged |
| User cancels unsaved guard | Open B from dirty A => Cancel | A session/history/bytes unchanged; no B recovery prompt |
| User discards target recovery | Quarantine candidate, open disk, retire quarantine | Original disk unchanged; candidate no longer offered |
| User cancels target recovery | Cancel dialog | Previous live session and all original files unchanged |
| External modification after prompt | Disk/snapshot hash differs at user confirm | RACE_CHANGED, no Restore/Discard committed |
| Restore invalid data | Load/validation fails | Disk and prior backup unchanged; candidate retained |
| Restore backup fails | Exclusive-copy failure | Disk unchanged; cleanup owned temporaries |
| Restore final replace fails | Atomic replace failure | Disk unchanged; backup/candidate preserved |
| Restore succeeds but UI refresh fails | Durable disk commit, session/UI not updated | Explicit partial success; numbered backup retained; no success notice |
| Close with busy render | Existing GuardedMainWindow busy rule | Close denied until safe background state; timers fenced |
| Crash on Unicode/deep path | Snapshot/provenance parent folder special chars | Reopen safely, digest verify, no path alias collision |

## 10. Acceptance evidence and validation design for STEP04

- **Fake-clock unit tests:** exact 20s debounce, 120s bounded eligibility, 60s periodic dirty poll, retries 30s/120s/300s, no writes while clean/unpersisted/modal/closing, no overlapping writes, new edit during IO, previous epoch result ignored.
- **Snapshot metadata tests:** 16 KiB descriptor cap, format version, absent legacy metadata, corrupted/oversized/unknown version, schema v3/v4 identity, digest mismatch, baseline external modification, path aliases/Windows case-insensitivity.
- **Concurrency/stale tests:** real cooperative worker; forced overlap of Save, Save As, background callback and recovery dialog; stale decision token rejected after disk changed; snapshot IO fenced from manual Save; no reentrant modal.
- **Fault injection:** write/read/rename/fsync, permission and file lock, interrupted process after snapshot before metadata, before/after Save, and after restore replace before session adopt; inspect original bytes, candidate and numbered backups.
- **Qt offscreen:** existing dirty GuardedMainWindow before target recovery, keyboard defaults and Escape Cancel, focus restoration, title dirty marker remains correct, 42-screen screenshot parity, dialog image reference before implementation.
- **Windows acceptance:** Windows 11 portable PyInstaller EXE, PATH/app-local external FFmpeg smoke, Unicode/spaces/apostrophe/deep paths, portable ZIP credential scan, no bundled FFmpeg, exact source SHA and checksum verification.
- **Security:** synthetic Gemini-token canaries must never enter autosave meta, output logs, built ZIP or screenshots; do not use real user keys.
- **No ungrounded claims:** existing v0.2.2 795 tests passing is baseline, not proof this proposed behavior exists. All new acceptance tests must fail before feature implementation and pass after SOL work. 500-scene command-generation test is not real 500-scene render.

Proposed minimum additions include `RCV-01..24` from STEP01 plus metadata atomicity, dangling-descriptor crash, Save-fence and post-restore partial-commit tests; precise case IDs and assertions belong to STEP04.

## 11. Architecture reviews and conditional implementation-wave map

| Future gate/wave | Scope (conditional) | Required proof before promotion |
|---|---|---|
| STEP03 UI IMAGE PROMPTS | Recovery choice, conflict, autosave status/failure, Save As collision visual references | **HARD STOP** after prompt package; approved images and ONE consolidated UI reference DOCX committed |
| STEP04 testing plan | Fake-clock, provenance/atomicity, fault injection, Windows 24+ cases | Detailed DOCX, test-first matrix PASS |
| STEP05 authorization | Exact module/files, security/lifecycle gates and all planning/UI DOCX completeness | DoR PASS; no runtime code before this |
| W06-A | Pure coordinator scheduling and fake-clock tests | No Qt deps, no extra history, epoch safety |
| W06-B | RecoveryManager/provenance adapter and crash consistency tests | Byte integrity, legacy uncertain, no raw secrets |
| W06-C | Save/Open/Save As/Restore/Discard transactional integration | Preserved dirty/backup/history, old guard precedence |
| W06-D | Approved Qt UI binding, offscreen dialogs, timers and app teardown | Final UI parity + safe cancellation |
| W06-E | Windows portable regression, external FFmpeg, deep path and security evidence | Full Windows and CodeQL PASS |
| STEP07 | Exact-source RC/final stable release verification | New v0.3.0 tag ONLY after release gates PASS; older tag immutable |

W06 labels are suggestions to be independently reviewed in STEP05. No implementation has started and no version tag has been created.

## 12. Blocking questions resolved vs carried forward

**Resolved at STEP02 architecture level**: one owner/coordinator, single serial IO channel, untrusted provenance descriptor without project schema changes, digest+baseline validation, no automatic Restore, legacy sidecars uncertain, Save fence precedence, epoch-based timer cancellation, conservative Save As collision behavior, explicit backup and partial-restore error classes.

**Must remain explicit in STEP03/04/05**:
1. Qt pixel layout, accessibility/focus/keyboard behavior and exact Indonesian UI wording require STEP03 approved image/reference DOCX.
2. Snapshot-quarantine and Save cleanup filesystem helper precise API plus rollback on permissions/read-only must be covered by STEP04 test-first evidence.
3. Security review must decide whether canonical path hashing leaks sensitive path identity in a user-copyable descriptor; alternatively store opaque stable per-project identifier without schema mutation.
4. Windows managed folders/network/cloud-synced paths must be tested as **limitations**, not silently declared supported.
5. Cross-process concurrent editing is not solved by single-process in-memory lock; compare-and-swap disk hashes are required, and optional OS advisory/file locks need explicit portability analysis.
6. Forced power loss durable-directory fsync is platform-dependent; claiming power-loss guarantee requires native Windows durability testing and evidence.
7. A changed project with no first saved file path is outside current autosave support; do not promise unsaved-first-document protection.
8. Fail-closed quarantine/rollback and post-replace live-session failure semantics require validation before release.

Any adjustment to STEP01's 20/120/60-second user contract needs a documented decision, not an unreviewed source code tweak.

## 13. Gate, mandatory DOCX and next-step handoff

STEP02 is **COMPLETE/PASS only after**:
1. this Markdown source at `docs/v2_0_3_0_planning/02_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.md`;
2. actual detailed, readable, rendered/visually checked DOCX `docs/v2_0_3_0_planning/docx/02_V2_0.3.0_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.docx`;
3. deterministic DOCX generator and status/handoff update committed to same V2 repo;
4. temporary branch-only DOCX workflow retired before merge; all PR-changed files documentation/planning only;
5. final PR-head CI, CodeQL, Windows acceptance and backend checks PASS; merged PR main commit independently verified;
6. `v0.2.2` tag still resolves to `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.

**STOP after STEP02**. STEP03 is NEXT only on the user's next explicit instruction. At STEP03, write prompts for the recovery-specific UI images and then **HARD STOP even if the user says "lanjutkan"**. Resume planning/implementation only after all images are generated, inspected/revised, and one approved final UI reference DOCX is committed. All STEP00–05 planning DOCXs must precede STEP06 SOL coding. All new UI versioning/implementation/release operations are forbidden in this turn.