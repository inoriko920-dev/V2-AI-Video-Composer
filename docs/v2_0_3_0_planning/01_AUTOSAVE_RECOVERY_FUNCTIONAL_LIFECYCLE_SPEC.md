# STEP 01 — Functional Autosave and Recovery Lifecycle Contract (V2 v0.3.0)

**Status: PLANNING ONLY / FUNCTIONAL SPECIFICATION. Implementation NOT authorized.**

**Date:** 8 October 2026, WIB. **Product:** V2 AI Video Composer. **Canonical STEP00 merged main:** 2b5fae0368dd421b3d5e44b1e1e4fc83561f3e03. **Published stable baseline:** v0.2.2 at eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef (immutable).

**Owner:** ASTRA planning. **Next only after STEP01 closure:** STEP02 architecture/scheduler implementation-boundary plan. **Hard STOP later:** STEP03 when UI image prompts are completed until final reviewed images and one reference DOCX are committed.

This specification describes the behavior that a future SOL implementation must satisfy. It creates no timers, dialogs, repositories, migrations, tests, version bumps, branches of the legacy repo or release assets.

## 01. Product objective and non-goals

**Objective:** Reduce loss of edited, previously saved AAVC projects following unexpected termination. On the next Open, offer controlled recovery without ever modifying a project, its autosave, another active session, or Undo/Redo as a side effect of merely inspecting an autosave. Respect the existing Save/Discard/Cancel unsaved-session guard first.

**Non-goals:** automatic cloud backup, fully crash-proof unsaved documents without a first Save path, background video export persistence, multi-version recovery browser, cross-device synchronization, new project schema, new render backend, changed Gemini credentials, replacing original reference UI. Existing v0.2.2 recovery engine remains the only low-level snapshot implementation. No external dependency is allowed before STEP05.

**Source review:** src/aavc/persistence/recovery.py implements RecoveryManager (write/load/restore/clear) and exclusive numbered pre-recovery backups; src/aavc/application/services/project_session.py owns current/path/is_dirty and canonical history; src/aavc/presentation/windows/guarded_main_window.py already mediates unsaved Save/Discard/Cancel before Open/New/Close; src/aavc/presentation/windows/main_window.py owns project UI actions; bootstrap/startup.py uses Qt and FoundationServices. This is not an assertion that automatic autosave is already implemented.

## 02. Functional vocabulary and source of truth

| Term | Exact meaning |
|---|---|
| Durable project | An existing, validated .aavcproj path whose bytes are a persisted ProjectState |
| Active session | One ProjectSession with current state, saved baseline, path and Undo/Redo stack |
| Dirty state | ProjectSession.is_dirty comparing current content to saved baseline; autosave MUST NOT mark it clean |
| Recovery snapshot | Existing RecoveryManager .aavcproj.autosave file, not the real project |
| Snapshot provenance | An untrusted yet integrity-checked metadata record that binds autosave digest, original project path identity and saved baseline digest; STEP02 decides storage format |
| Generation | Monotonic in-process state revision/epoch for edits and active project identity; needed to ignore stale callbacks and stale prompts |
| Valid candidate | Snapshot decodes to an allowed ProjectState, matches requested project identity/provenance policy and differs semantically from the disk state |
| Uncertain/conflicted candidate | Valid snapshot whose originating saved baseline does not match current disk or whose provenance is absent/invalid |
| Redundant snapshot | Parsed snapshot semantically identical to the disk project, so opening it adds no unsaved content |
| Manual Save | Explicit user persistence of current ProjectState, unlike an autosave snapshot |
| Recovery restoration | Explicit action that replaces disk project after validating candidate and preserving a pre-recovery backup |
| Recoverable error | A problem that cannot silently discard saved or candidate user data; user is told what is preserved |

## 03. Scheduling policy — user-visible functional decisions

**Scheduled snapshot eligibility (ALL required):** the app owns a loaded ProjectSession; its project has a durable writable path; session.is_dirty is true; current state is valid and a canonical command/transaction has completed; the intended path/identity/generation still match the snapshot request; no snapshot write is already pending; the current app is not closing or switching; no modal recovery decision is unresolved.

**Chosen functional cadence for future implementation:** one-shot debounce of 20 seconds after the most recent committed meaningful edit, with a maximum 120 seconds since the first unsnapshotted eligible dirty state (continuous user activity must not postpone snapshots forever). While dirty and changed since the last successful snapshot, poll no more frequently than every 60 seconds for an eligible write. Exact timer construction, clock injection, executor location and fairness details are deferred to STEP02, but these thresholds form the initial user-visible contract and must be tested with fake time.

**Behavior:** each committed command, Undo and Redo updates a revision marker; paint/hover/playback ticks and transient UI selection without project state changes do not. Multiple rapid edits coalesce. At most one write is in flight. A write handles an immutable project snapshot captured at an accepted revision and may not update saved baseline, clean the title asterisk or push an Undo transaction. If a newer edit arrives during a write, the newer edit remains dirty and is scheduled separately. Timer callback errors are reported non-fatally and never overwrite the .aavcproj file.

**No saved path:** if a ProjectSession was started in memory without a saved path, the autosave system does not guess an output filename or write into arbitrary temporary folders; manual Save/Save As is required to establish a durable destination. A single non-intrusive notice may explain that recovery protection will begin after first Save. Existing Create flow already persists before activating a new session.

**Pause/exit policy:** pause new scheduled writes while any recovery prompt is open, during a synchronous project-switch transaction or shutdown handoff. Do not start a risky last-moment implicit Save at process exit. If an eligible snapshot is already in flight on close, allow bounded completion or safely preserve last committed candidate while honoring existing background-work and unsaved guards. STEP02 must define precise Qt lifecycle mechanics and worker shutdown deadlines.

**Failure/backoff:** a failed snapshot leaves original real project and any last valid autosave intact wherever possible. Do not set a last-success revision. Retry is bounded: first retry after 30 seconds, next after 120 seconds, then no more often than every 5 minutes while an error persists; successful write resets error counter. Never spam modal dialogs on every timer tick; status/error details remain available in localized UI feedback.

## 04. State machine — session and scheduler

| State | Entry conditions | Permitted transition | Forbidden side effect |
|---|---|---|---|
| NO_PROJECT | Session.current absent | OPEN_GUARD / CREATE | No autosave writes |
| CLEAN | Valid path and is_dirty false | DIRTY_PENDING after real edit | No redundant snapshot write |
| NO_PATH_DIRTY | Dirty but path missing | CLEAN after successful Save; otherwise wait | No fabricated path |
| DIRTY_PENDING | Completed real edit and valid path | WRITING after debounce/cap; CLEAN after Save | Must not mark clean |
| WRITING | One snapshot operation active | DIRTY_PENDING if new revision; DIRTY_PROTECTED when success; ERROR_RETRY when fail | No overlapping writes |
| DIRTY_PROTECTED | Snapshot matches most recently captured revision, but session remains dirty | DIRTY_PENDING on new edit; CLEAN on manual Save | No Undo/Redo history entry |
| ERROR_RETRY | Transient disk/validation error | DIRTY_PENDING when retry eligible | No silent real-project replacement |
| SWITCH_GUARD | New/Open/Close requested | REMAIN on Cancel; DESTINATION_PROBE after current guard succeeds | Never drop previous unsaved project before guard |
| RECOVERY_DECISION | Eligible target candidate is inspected | RESTORE / DISCARD / CANCEL | No disk or session mutation before choice |
| RECOVERY_CONFLICT | Candidate has uncertain metadata/external file change | Explicit conflict acknowledgement or CANCEL | No one-click silent overwrite |
| RESTORING | User approved valid candidate, preflight revalidated | CLEAN_NEW_SESSION on durable success; REMAIN_ERROR on failure | No undo-stack reuse or partial target overwrite |
| CLOSING | Close allowed by background and dirty guards | TERMINATED after safe write finish/abort | No new timer or modal race |

A state is a **functional coordinator state**, not an alternative to ProjectSession for project content or another history stack. State progression is monotonic by revision/epoch. Late responses from old sessions MUST be dropped.

## 05. Guard ordering for Open, Create, Close and Cancel

**Open(other) and Create(new):**
1. File/path selection or Create preflight may occur without changing session. User cancel at any picker = no change.
2. Before switching the active project, invoke the existing GuardedMainWindow unsaved-change Save/Discard/Cancel decision. If Cancel -> stop; if Save -> continuation only if successful and session truly clean; if Discard -> user explicitly accepts abandoning in-memory current changes. No recovery-specific dialog may appear first.
3. On target Open, load/validate the saved target and inspect its snapshot/provenance in an isolated preflight. Do not replace active ProjectSession yet.
4. Missing snapshot -> normal open target transaction. Equal/redundant snapshot -> normal open with no recovery prompt; consider deferred harmless cleanup.
5. Valid candidate differing from disk with matching trusted identity/baseline -> recovery choice. Uncertain or conflicted -> conflict-aware choice, never silent Restore.
6. Cancel during target decision -> previous session remains identical (current value, saved baseline, path, dirty state, can_undo, can_redo, selected scene and disk bytes). A previously confirmed Discard in step 2 does not itself mutate the previous session until the target commit.
7. Only after final target decision passes, switch session and refresh UI. On error, keep previous session and report recoverable failure.

**Close:** existing background busy guard runs before unsaved Save/Discard/Cancel. If Cancel, stop and keep timer/session. If Save fails, stop. If user chose Discard, close may proceed while leaving a valid existing autosave as recoverable crash evidence unless a subsequent cleanup policy explicitly and safely retires it. Never treat an automatic snapshot as a user-approved normal Save.

**Same project reopened:** do not repeatedly trigger the snapshot choice when the requested target is exactly the already active canonical path without an explicit reload command; STEP02 must define idempotent handling of duplicate menu/callback events.

**Two projects with same display title:** their canonical resolved paths and contents—not visible title—identify snapshot ownership.

## 06. Recovery candidate eligibility and deterministic freshness

**Preflight inputs:** canonical target path; validated disk ProjectState + stable digest over authoritative bytes; existing snapshot parsed via RecoveryManager + digest; provenance identity and digests where present; supported v3/v4 model validation. Do not depend on file modification times to establish candidate freshness.

**Decision categories (functional contract):**
- **NO_SNAPSHOT** — .autosave absent: open disk version; no prompt.
- **INVALID_SNAPSHOT** — autosave unreadable, malformed, future schema or incompatible advanced-v1 contract: never restore automatically, never delete automatically. Warn and keep the disk project; destructive cleanup requires explicit separate consent. If safety cannot be determined, stop target Open without changing previous session.
- **REDUNDANT** — snapshot and disk deserialize to identical ProjectState (and compatible integrity): open normally, do not suggest recovering lost work; defer cleanup until a safe transition.
- **RECOVERABLE_VERIFIED** — snapshot valid and differs; ownership/provenance digests match target and its current disk baseline; prompt Restore / Discard / Cancel.
- **RECOVERABLE_UNCERTAIN** — valid differing snapshot but provenance is absent/invalid, or target disk digest differs from the recorded baseline: warn of conflict; require an additional explicit acknowledgement for destructive Restore; Cancel is safe default.
- **MISSING_TARGET** — disk project is missing/unreadable: do not construct or replace it implicitly from snapshot in this scope; report and preserve any snapshot.
- **RACE_CHANGED** — source disk or snapshot bytes changed between inspection and user selection: abandon stale decision, re-read and re-evaluate (or cancel); do not apply the stale choice.

**Freshness policy:** compare authoritative project and snapshot bytes/content and a snapshot-to-base identity record, not wall clock alone. STEP02 will specify canonical hashing, sidecar format, transaction ordering, and how to handle crash windows between writing snapshot/provenance or saving/clearing autosave. Required behavioral minimum: uncertainty becomes visible conflict rather than a hidden Restore, and an old autosave must never silently overwrite a more recent manual Save.

**Legacy snapshots from v0.2.2:** existing plain .autosave remains readable. Absence of new provenance cannot be treated as verified; handle as RECOVERABLE_UNCERTAIN rather than dropping potentially valuable data. No schema-v5 migration.

**Security:** provenance must never hold raw project content, Gemini API keys, voice audio bytes or user secret values. Any project path displayed in an error should be minimized to avoid exposing sensitive folders in logs.

## 07. Recovery choice semantics (Restore / Discard / Cancel)

| Choice | Preconditions | Disk effect | Session effect | Snapshot effect |
|---|---|---|---|---|
| Restore | Valid candidate, user confirms; if conflicted then extra acknowledgement; revalidate byte digests before write | RecoveryManager validates again, stores non-clobbering pre-recovery backup, atomically replaces original project | Only after successful durable restore, load restored ProjectState as new ProjectSession baseline; new history starts at restored state | Keep candidate until committed state is known stable; cleanup later under safe policy |
| Discard | Valid candidate and user explicitly chooses disk version; candidate identity rechecked | Never modify original .aavcproj | Open disk version and initialize fresh session | Retire *only that candidate* after successful transition, with failure handled explicitly; do not delete unrelated backup |
| Cancel | User declines choice or closes dialog, including Escape | No write, rename or delete | Preserve former session, dirty/path/undo/redo and selected scene | Preserve snapshot and provenance byte-for-byte |

**Restore commit sequence:** freeze candidate identity; verify target bytes unchanged; validate candidate; preserve old target via exclusively created .pre-recovery[.N].bak; write unique same-folder temp and atomic replace; reopen/validate restored project; commit new session only when load succeeds; otherwise surface failure and preserve original through backup with documented recovery path. If implementation cannot guarantee safe no-partial-current-session semantics for every failure point, STEP02 must choose a rollback protocol and tests before coding.

**Conflict acknowledgement:** not a hidden or automatically checked option. Show that the saved project changed since snapshot baseline, identify the potential overwrite, state that a backup is made and provide Cancel as safest default. The exact dialogue is subject to STEP03 UI image approval. The plain known-good case gets exactly three semantic choices.

**Discard failure:** cannot silently claim recovery was discarded if unlink/retirement fails. The engine must not accidentally reopen the same candidate as new after an unsuccessful discard; decide fail-closed and leave previous session pending, or preserve a separately marked disposition with evidence. STEP02 will select the implementation satisfying this requirement.

**No separate edit history:** restored project starts a new history baseline; cannot undo past a process crash across previous process histories. Do not splice stored recovery into an existing active session Undo/Redo transaction.

## 08. Manual Save and Save As interactions

| Operation | Success behavior | Failure behavior |
|---|---|---|
| Manual Save (active path) | First atomically persist current state through ProjectSession.save; only after success retire or invalidate candidate for that path and reset scheduling baseline; title becomes clean; if cleanup fails, warn and avoid falsely presenting stale snapshot as verified new work | Preserve dirty state, current path, history and candidate snapshot; do not clear any recovery data |
| Save As (fresh target) | Validate fresh path and durable source, save through canonical repository; only after success rebind session path; start new scheduling epoch for new path; keep old-path candidate untouched unless its ownership/disposition is explicitly handled; no cross-project snapshot copy | Preserve original path, dirty state, history and old/new snapshot bytes |
| Save As (existing target) | Canonical existing-target v3/v4/corrupt guard applies; existing target's recovery data may belong to another project and must never be deleted, overwritten or rebound automatically; require a later explicit ownership workflow if collision discovered | Abort safely; report recoverable conflict and preserve all inputs |
| Failed snapshot after successful Save | Main project remains clean; show non-fatal cleanup/storage warning and treat leftover candidate as unverified/stale rather than overriding the just-saved disk | Never revert the successful Save |
| Undo after Save | If undo makes project dirty, schedule fresh snapshot; schema version may return to v3 without silent promotion | No downgrade of real disk project through autosave |
| Redo after Save | If redo returns to saved state, stop pending snapshot and do not create one; if redo is different, schedule normally | No history pollution from background snapshots |

**Policy for Save As old snapshot:** preserve pre-existing old-path autosave and pre-recovery backups by default rather than silently erasing them. This may cause a later old-path recovery prompt; its provenance and content must be evaluated as a candidate, not auto-restored. STEP02 must document collision-safe retirement and stale classification without deleting possibly recoverable work.

**Crash window:** Save may be durable while snapshot metadata cleanup has not finished; this condition MUST resolve to REDUNDANT or RECOVERABLE_UNCERTAIN, not automatic Restore. No reliance on timestamps, mtime ordering or unchecked sidecar truth.

**No autosave-as-Save:** autosave may never call ProjectSession.save() or update _saved_state; only RecoveryManager snapshot service may write the .autosave path. Ordinary manual Save remains the only operation that clears the dirty marker.

## 09. Error handling, permissions and user messaging contract

| Error class | Behavior | Data preservation |
|---|---|---|
| SNAPSHOT_IO_FAILED | Non-modal status, bounded retry; manual Save still available | Disk project and previous valid snapshot unchanged where possible |
| SNAPSHOT_INVALID | Never auto-restore; user sees caution and safe path | Corrupt snapshot retained for forensic manual action |
| RECOVERY_CONFLICT | Explicit secondary confirmation before risky restore | Preserves saved original via versioned backup if restored |
| PROJECT_DESTINATION_UNREADABLE | Block normal Save/Save As; no force overwrite option in this scope | Destination byte-for-byte unchanged |
| SCHEMA_DOWNGRADE_BLOCKED | No normal Save over newer destination; autosave may track actual in-memory schema | Destination, project history and snapshot policy intact |
| RECOVERY_BACKUP_FAILED | Abort recovery before original replace | Snapshot and original disk unchanged |
| RECOVERY_REPLACE_FAILED | Abort and preserve original plus retryable candidate | No partial replacement; temp removed |
| SNAPSHOT_RETIRE_FAILED | Warn and do not falsely claim Discard or successful cleanup | Retain candidate for later explicit resolution |
| PROJECT_SWITCH_CANCELLED | Close/open/create action stops; current session untouched | No filesystem edits from recovery decision |
| RACE_CHANGED | Re-evaluate snapshot/disk; never apply stale approval | No wrong-generation writes |

User-facing messages must be in Bahasa Indonesia, concise, nonblaming and distinguish **"Tersimpan"** (manual) from **"Cadangan otomatis dibuat"** (snapshot). Errors should not expose raw secrets or full Gemini key material. Silent retry must not create repeated modal dialogs; log telemetry includes only sanitized error code, operation and anonymized context.

## 10. Determinism, concurrency and callback invariants

- A project identity token and in-process revision are captured with every scheduled autosave; only the matching active project epoch may commit its result. An old generation must not overwrite a new project's sidecar after switching tabs/paths.
- If a write and manual Save happen concurrently, canonical Save wins for user-visible clean state. Snapshot write needs invalidation/fence or ordering that prevents a late snapshot from becoming a false new candidate after Save.
- If any timer callback fires while the open/recovery modal is active, it must not mutate candidate bytes currently being inspected or redirect the current session.
- Reentrancy: repeated clicks or timer ticks during one recovery dialog cannot create additional dialogs or run Restore twice. Only one interactive recovery transaction per target is active.
- Running background render/AI tasks retain their existing close guard priority; autosave must not block or hijack user background cancellation.
- Qt-thread safety: the presentation timer may initiate a coordinator request; filesystems/serialization remain behind application/infrastructure ports; no domain import of Qt.
- Snapshot creation must never render videos, call Gemini, execute FFmpeg or scan users' unrelated files; scope is project-state persistence only.
- On disk full, permissions error, read-only folders, network share interruptions and AV file locks, report safely; no fallback to unrequested path and no raw traceback popup.
- Automatic snapshot duration/performance budgets and exact worker behavior require STEP02 measurement plan and STEP04 Windows stress tests.

## 11. Data fidelity and compatibility

- Existing .aavcproj serialization and schema max v4 remain unchanged in v0.3.0 unless later STEP05 explicitly reauthorizes migration.
- Snapshots may naturally contain schema v3 or schema v4 depending on the actual in-memory ProjectState (e.g. Undo across advanced activation). Do not introduce new v4 tracks or promote schema just because a timer fired.
- In advanced v4, preserve animation_keyframe_contract=advanced-v1 exactly. Dormant advanced tracks remain dormant unless explicit user animation activation occurs.
- Recovery restores a project file state, not Windows Credential Manager, provider authorization or transient Qt/editor selection state; no API secret is persisted.
- Existing 21 native effects, render path and Gemini model remain unaffected. No unrelated UI redesign. A future new recovery dialog must use the frozen white-blue visual language and current real Qt widgets.
- Unicode, spaces, apostrophes, deep paths and user-owned temp filenames must not cause wrong-file writes or deletion; explicit Windows acceptance required.
- V2 only: legacy AI-Automatic-Video-Composer repository and all published v0.2.2/v0.2.1 tags/assets are immutable.

## 12. Functional acceptance matrix mapped to STEP00 cases

| Case | Expected outcome | Evidence required in STEP04/06 |
|---|---|---|
| RCV-01 | Dirty saved project writes snapshot; remains dirty; undo unchanged | Fake-clock session/snapshot test |
| RCV-02 | Clean/no-path sessions never write unsolicited files | File-access sentinel test |
| RCV-03 | 20s debounce, 120s max lag, 60s dirty polling, single writer | Fake clock and callback overlap test |
| RCV-04 | Successful Save invalidates obsolete recovery without false post-Save offer | Crash-window matrix |
| RCV-05 | Failed Save keeps disk, dirty and autosave unchanged | Fault injection |
| RCV-06 | Save As rebinding safe, no old/other snapshot loss | Identity/collision matrix |
| RCV-07 | Valid differing candidate prompts three choices, nothing mutated beforehand | Qt offscreen decision test |
| RCV-08 | Restore creates numbered backup, atomic disk replace, fresh session | Byte-hash and history assertions |
| RCV-09 | Discard retires only selected candidate after safe commitment | Inject failed delete and collision |
| RCV-10 | Cancel preserves current project/path/dirty/undo/redo and disk bytes | Pre/post immutable fingerprint |
| RCV-11 | Corrupt/future/permissions failure never auto-restores | Invalid model/fault matrix |
| RCV-12 | v3/v4 travel and dormant advanced tracks unchanged | Schema regression suite |
| RCV-13 | Windows special paths, locked files, disk full safe | Windows packaged EXE integration |
| RCV-14 | No raw Gemini API keys in snapshots/metadata/logs | Credential scan |
| RCV-15 | Repeated modal, close and switch cannot race/corrupt | Reentrancy and teardown tests |
| RCV-16 | Real Qt + portable EXE + full acceptance gates green | Actions CI, CodeQL, Windows |

**Additional necessary cases beyond STEP00:** RCV-17 snapshot/disk change between dialog and confirm must re-evaluate; RCV-18 legacy metadata-free snapshot categorized as uncertain; RCV-19 successful Save interrupted before cleanup cannot auto-restore stale candidate; RCV-20 external edits to target disk while candidate exists cannot be silently overwritten; RCV-21 duplicate/no-op edit must not create redundant autosave; RCV-22 candidate invalidated while a save is in flight must not be resurrected by late callback; RCV-23 unsaved guard must run BEFORE snapshot dialog; RCV-24 no old snapshot is deleted by Save As to a fresh or occupied target.

Tests listed here are FUTURE tests, not tests that have already passed. STEP04 must write a complete failure-injection matrix and STEP06 must first show failing-before evidence. No coding is authorized by this document.

## 13. Decision examples for review

**Example A — normal crash recovery.** User saved Project A, edits a scene, leaves app abruptly. Eligible dirty state gets autosave and provenance matching A's on-disk baseline. Next session chooses Open A. With no prior dirty project, preflight detects candidate and offers Restore / Discard / Cancel. Restore stores A.pre-recovery.bak, writes recovered project atomically and opens a fresh clean session from recovered disk.

**Example B — Cancel after dirty project.** User edits Project B and chooses Open A. First GuardedMainWindow prompts Save/Discard/Cancel for B. User presses Cancel: neither A nor B nor either autosave is inspected destructively; B's path, history and dirty marker remain unchanged.

**Example C — Save succeeded but cleanup failed.** A's saved bytes are newer than previously captured autosave. Next Open sees baseline digest mismatch and must not offer an unqualified normal Restore. The candidate is retained and classified uncertain/conflicted with safe Cancel default.

**Example D — Save As old recovery.** Dirty A has valid A.autosave. User chooses Save As to C. Once C is safely persisted and becomes current session path, old A.autosave is not silently removed; no snapshot may be written to existing C.autosave without identity check. A can later be examined as a recovery candidate with explicit user decision.

**Example E — corrupt autosave.** A is readable, but A.autosave cannot be parsed. App must never alter A or delete autosave without permission. Inform user appropriately and either safely open disk or stop by conservative error policy. STEP02 defines exact non-destructive UI disposition when invalid snapshot is detected.

**Example F — interrupted Restore.** A snapshot is valid and user approves Restore. Backup copy or atomic replace fails. A still contains a valid disk project; prior backups and candidate are preserved and errors are visible. App does not claim "Dipulihkan" prematurely.

**Example G — advanced Undo to v3.** A schema-v4 project has activated advanced motion; user Undo returns state to valid v3 and remains dirty. Autosave snapshot may represent v3, but normal Save over existing v4 disk is still guarded. Restore is explicit and valid v3 snapshot can be recovered while original v4 backup is preserved.

## 14. Formal UI requirements for future STEP03 (NOT prompts yet)

Recovery panel must present enough context to make an informed user decision: project name, what is on disk versus what might be recovered (without implying unverified timestamps), three clearly differentiated actions, the fact that Restore creates a backup, and safe Cancel default. A conflict variant requires extra explicit consent and emphasizes that disk changed. A nonfatal autosave-status indicator and failure warning must not blend with "Project disimpan". Keyboard Enter/Escape and focus handling require acceptance tests. All wording Bahasa Indonesia; existing frozen light white-blue UI design and real Qt widgets preserved.

**Hard gate:** STEP03 creates image prompt(s) only, then MUST STOP even if a bare "lanjutkan" is sent. Work resumes only after all images are made, reviewed/revised and a single final UI reference DOCX is committed. STEP01 neither generates images nor approves layout pixels.

## 15. Implementation boundary references and unresolved STEP02 choices

STEP02 must specify: (i) application coordinator API and state revision tracking; (ii) how to bind RecoveryManager without a parallel persistence engine; (iii) how snapshot provenance is stored transactionally without changing .aavcproj schema; (iv) clock/debounce implementation; (v) retry/backoff and shutdown race contracts; (vi) exact clear-vs-quarantine sidecar policy and crash-window fallback; (vii) capability/error class map; (viii) whether snapshot write may run on worker or synchronous UI and its benchmarking requirement; (ix) restoration session commit/rollback if post-replace load fails; (x) preview of user-facing Qt dialog state transitions at STEP03 without building UI.

STEP05 must authorize exact files/modules, feature waves and precondition tests. The planned thresholds and behavior in STEP01 may be revised only through an explicit documented scope decision with regression implications, never by unrecorded SOL convenience changes.

## 16. STEP01 quality gate, source-of-truth and handoff

Required repository artifacts:
- docs/v2_0_3_0_planning/01_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.md — this detailed canonical Markdown.
- docs/v2_0_3_0_planning/docx/01_V2_0.3.0_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.docx — detailed Word handoff, generated from this source and visually rendered/reviewed.
- V2_0.3.0_PLANNING_STATUS.md and docs/v2_0_3_0_planning/IMPLEMENTATION_READINESS_INDEX.md updated.
- One-shot branch-only DOCX generation workflow removed before PR merge.
- PR changes planning files only, no runtime, schema, dependencies, Qt UI, workflow publisher or tags.
- Final PR-head CI, CodeQL, Windows acceptance and optional backend must PASS. After merge, verify DOCX and unchanged v0.2.2 tag from GitHub.

**Gate PASS only when all conditions above are verified.** Do not claim STEP01 complete from drafted Markdown alone. If a required artifact is missing, report HOLD.

**Exact NEXT:** STEP02 — Recovery coordinator architecture, snapshot provenance/atomicity, scheduling integration and security/compatibility plan — ONLY after new explicit "lanjutkan" on a later turn. Do not write STEP02 in this turn. **Coding and UI creation remain forbidden.**
