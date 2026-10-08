# STEP 00 — V2 0.3.0 Product Gap Audit & Recovery Lifecycle Scope

**Status: STEP 00 PLANNING — PROPOSED / NO APPLICATION CODING.**  
**Audit date:** 2026-10-08 (WIB).  
**Repository:** \`inoriko920-dev/V2-AI-Video-Composer\`.  
**Audited post-release main:** \`186844bdab3a8665488204fd75b9309f1fad5d5b\`.  
**Immutable published stable baseline:** \`v0.2.2\` at \`eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef\`.  
**Proposed new feature line:** **v0.3.0** (a minor version because recovery becomes a new user-visible capability). The release/version has NOT been created, tagged or bumped.

## 1. Mission and hard boundary

The next product priority is completing **GAP-03A: real project autosave scheduling and interactive recovery** using the existing, already-tested persistence engine. This is a product capability proposal, **not** evidence of a broken v0.2.2 release. This planning cycle keeps published \`v0.2.2\` and prior tags, historical source, release assets and the legacy repository immutable.

STEP 00 is a bounded audit/scope decision. It MUST NOT implement code, modify Qt UI, create release tags, bump \`pyproject.toml\`, upgrade dependencies, or silently change project schemas. Subsequent ASTRA planning controls SOL implementation, one STEP at a time with explicit acceptance.

## 2. Verified current repository and release state

- Post-release \`main\` SHA \`186844bdab3a8665488204fd75b9309f1fad5d5b\` (PR #47 documentation closure merged).
- Published stable \`v0.2.2\` points to \`eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef\`, not to mutable main.
- Final release workflow \`37727140284\` PASS: CodeQL, full Windows candidate build, **795 technical tests**, five extracted-portable folder cases, packaged EXE, FFmpeg/ffprobe 9.0.2 checks, built-artifact secret scan, SHA-256 and guarded release publication.
- Published Windows ZIP SHA-256: \`80232a96deedff0ee382c42e377999a8f9c5434e075b99c415a41a2e538d07e7\`.
- Published source ZIP SHA-256: \`ec03dfe339fbc71a4bf199784de9e0a4ff5cb0d69b38399c179c1bc178f30183\`. **Source ZIP is not a full Git history disaster-recovery bundle.**
- No open GitHub issues or open PRs were returned at STEP 00 audit. Do not infer the absence of product gaps from the absence of issue tickets.
- v0.2.2 maintains schema v4, \`animation_keyframe_contract=advanced-v1\`, 21 native effects, Gemini credentials model, external FFmpeg final renderer and frozen professional white/blue Qt design.

## 3. Search-before-create results and code-level evidence

**A-01 — The recovery persistence engine already exists.**
\`src/aavc/persistence/recovery.py\` defines \`RecoveryManager\` with \`recovery_path_for\`, \`write_snapshot\`, \`has_snapshot\`, \`load_snapshot\`, \`restore_snapshot\`, and \`clear_snapshot\`. Its v0.2.2 recovery restore validates input before touching the project, preserves non-clobbering numbered \`.pre-recovery[.N].bak\` backups, uses an atomic replacement path and cleans temporary outputs after failure. **Reuse it**; do not fork a new serializer, storage engine or project format.

**A-02 — ProjectSession owns the persistence/dirty baseline.**
\`src/aavc/application/services/project_session.py\` owns \`current\`, \`path\`, \`is_dirty\`, \`start/create/open/save\`, \`execute\`, \`undo\` and \`redo\`. \`save\` advances the saved baseline only after successful persistence. It does not currently schedule snapshots or expose a recovery transaction controller. Build on this canonical session/history boundary.

**A-03 — UI project actions exist but are not recovery-aware.**
\`src/aavc/presentation/windows/main_window.py\` exposes create/open/save and various project edits. The active window is composed through \`src/aavc/bootstrap/startup.py\` and the inherited Qt window hierarchy; this startup path currently uses \`QTimer\` for screenshots, not a real autosave scheduler. A new recovery decision must respect the current unsaved-project guard and controller routing.

**A-04 — Existing tests prove engine safety, not user-facing automatic recovery.**
\`tests/unit/test_step11_persistence_recovery.py\`, \`tests/unit/test_project_session.py\`, and \`tests/unit/test_v2_0_2_2_persistence_recovery_safety.py\` cover snapshot round-trips, corrupt/future-schema rejection, atomicity, session dirty/history and Save/Save As safety. The prior \`docs/v2_0_2_2_planning/03_SCHEMA_V4_PERSISTENCE_RECOVERY_STRESS_PLAN.md\` explicitly deferred **PRS-23**, **PRS-24**, **PRS-25** and **GAP-03A** runtime wiring. None of those can be claimed complete based on engine unit tests alone.

**A-05 — Foundation architecture already supports integration.**
\`src/aavc/bootstrap/composition_root.py\` builds \`FoundationServices\` containing a \`ProjectSession\` and job manager. A future recovery coordinator belongs in the application/service boundary, with infrastructure filesystem access through the existing persistence component and only thin dialogs/timers in presentation. Do not invoke persistence directly from domain classes.

## 4. Alternative evaluation — adopt, adapt, or start over?

| Option | Assessment | Decision at STEP 00 |
|---|---|---|
| Reuse existing RecoveryManager, ProjectSession, Qt lifecycle | Already owned, tested, schema compatible and consistent with repository architecture | **Preferred starting point** |
| Adopt an external auto-recovery repository or new framework | Would add integration and license/dependency risks; not necessary unless a verified missing capability is discovered | **Do not adopt at STEP 00** |
| Rewrite project serialization or introduce a second recovery store | Would risk v3/v4 backwards compatibility, existing backups and atomic semantics | **Prohibited absent new architecture gate** |
| Build new UI from scratch | Conflicts with frozen 42 UI references and established white/blue Qt style | **Prohibited** |

This is an in-place feature extension to the existing mature V2 codebase, not a request to fork or replace the entire application. An external component needs a later license/provenance and adapter review before consideration.

## 5. Proposed v0.3.0 user-visible scope

**S-01 — Autosave on eligible dirty projects.** After a project has a durable file path and unsaved edits, save a valid recovery snapshot without marking the project as manually saved. No snapshots for an unchanged project; a user-visible explanation for a project that has no saved path must be planned.

**S-02 — Timed scheduling, throttling and reentrancy.** Plan an explicit debounce/interval policy to avoid writing on every keystroke and prohibit overlapping writes. Qt timer lifetime belongs to the running application, not a domain model. Define what happens on project switch, Save As, close and cancellation.

**S-03 — Open-time Restore / Discard / Cancel.** Upon choosing a project with a valid, eligible recovery snapshot, give a deterministic user decision. Restore must preserve the pre-recovery project and keep the correct session/history semantics; Discard must not destroy the main project; Cancel must keep the previous active session untouched.

**S-04 — Corrupt/future-schema/stale autosave safety.** Invalid or incompatible snapshots must not be automatically loaded or overwrite projects. An old snapshot must not reappear as “newer” simply because of unreliable wall clock metadata. Define a safe freshness/content identity policy before implementation.

**S-05 — Correct Save and Save As lifecycle.** A successful manual Save resolves or retires any stale recovery snapshot according to a documented policy, only after success. Save As must not leave hidden snapshot bindings pointing to the old project or overwrite another project's autosave.

**S-06 — No unsaved-work loss.** The existing unsaved-project guard is mandatory before switching to a project with a snapshot. Cancel must leave path, dirty flag, current project, Undo/Redo and disk bytes unchanged.

**S-07 — Non-intrusive recovery feedback.** Communicate autosave status and recovery errors clearly in Bahasa Indonesia, without falsely marking project “Tersimpan” or displaying secret file data.

**S-08 — Backwards compatibility.** Legacy v3 and advanced-v1 schema-v4 snapshots must preserve their genuine schema; a snapshot/save operation must not silently activate v4 or rewrite native motion assignments. Gemini key material must remain outside project/autosave payloads.

## 6. UX/image-prompt hard stop

Recovery introduces at least one **new user-facing decision dialog**. Therefore, unlike v0.2.2, this cycle **requires a UI reference gate**. The future UI planning STEP must:
1. inspect the inherited white/blue UI and all relevant frozen references;
2. draft precise image-generation prompts for Restore / Discard / Cancel, autosave status, error and save transition states, using the user's existing safe-zone/layout rules where applicable;
3. **STOP immediately after all UI image prompts are prepared**; do not implement code, generate a replacement Qt UI or proceed merely on an unqualified “lanjutkan”;
4. continue only after all visual references have been generated, reviewed/revised, and assembled into **one final UI reference DOCX**;
5. ensure all planning DOCXs and the final UI reference DOCX are committed to this V2 repo as source-of-truth before implementation authorization.

This STEP 00 **does not create UI prompts or UI images**. The hard stop belongs to the future UI-prompt STEP.

## 7. High-risk decision inventory (unresolved until later planning)

| ID | Risk / required decision | Planned resolution |
|---|---|---|
| R-01 | Whether autosave writes while a command/Undo/Redo is incomplete | application-session scheduling contract |
| R-02 | Snapshot freshness and stale prompts after manual save | deterministic snapshot/session policy, not timestamps alone |
| R-03 | Restore atomicity, backups and failure injection | reuse RecoveryManager and regression tests |
| R-04 | Cancel during unsaved-project switch | state-machine design and offscreen UI regression |
| R-05 | Missing/corrupt/future-schema project or snapshot | fail-closed error/decision UX; never silent fallback |
| R-06 | First unsaved project without a path and Save As transitions | explicit path policy before coding |
| R-07 | Windows long path, Unicode path, permissions, disk full, file lock | Windows technical acceptance and fault matrix |
| R-08 | UI parity and reentrant modal/timer callbacks | canonical Qt lifecycle/UI prompt gate |
| R-09 | Automatic background work and shutdown races | serialized execution, cancellation and process exit contracts |
| R-10 | Raw Gemini credentials or provider state entering snapshots/logs | redaction/serialization security tests |
| R-11 | v3/v4 advanced-animation contract mutation | regression suite and future-schema guard |
| R-12 | Background/autosave impact on large real projects | performance budget, 10/100/500 scene *command construction* separation |

No timing interval, recovery precedence or Save As deletion policy is frozen by STEP 00. Those must be derived and authorized later; do not invent defaults in code.

## 8. Minimum acceptance cases to plan and write failing-before tests

- **RCV-01:** a dirty saved project produces a valid snapshot without changing \`is_dirty\` or its manual save baseline.
- **RCV-02:** clean, unset-path and idle sessions create no unsolicited disk writes.
- **RCV-03:** multiple edits produce at most the authorized scheduled snapshot writes; no overlapping callbacks.
- **RCV-04:** manual Save succeeds => stale snapshot is no longer falsely offered.
- **RCV-05:** failed manual Save leaves the original project and eligible snapshot intact.
- **RCV-06:** Save As rebinding does not overwrite the previous/another project's snapshots.
- **RCV-07:** open with valid eligible snapshot => exactly Restore / Discard / Cancel, with no mutation before choice.
- **RCV-08:** Restore follows canonical numbered pre-recovery backup and atomic target replace; current/Undo/Redo session initialized consistently.
- **RCV-09:** Discard keeps the saved disk project intact and retires the correct snapshot only after an authorized choice.
- **RCV-10:** Cancel after a dirty previous session preserves previous state, path, history and all disk bytes.
- **RCV-11:** malformed, future-schema or permission-denied snapshots are never auto-restored.
- **RCV-12:** v3 -> v4 / v4 -> v3 snapshot travel never silently promotes schema or loses dormant advanced tracks.
- **RCV-13:** Unicode/apostrophe/deep Windows paths, disk-full and locked-file injection preserve bytes.
- **RCV-14:** no raw API keys in snapshots, logs, dialogs or test artifacts.
- **RCV-15:** shutdown, project switch and repeated dialog opening do not leak callbacks, timers, threads or corrupt snapshots.
- **RCV-16:** full Qt offscreen flow, actual portable EXE and reproducible Windows test evidence are green.

These IDs are proposed test planning inputs, not claims of tests that already exist. Each required fix must first show a failing-before test demonstrating the missing behavior.

## 9. Explicitly out of scope for v0.3.0 unless reauthorized

- A general Filmora-like UI redesign, new docking system or replacement of the 42 frozen screens.
- Changing the 21 native effect definitions, render profile or external FFmpeg final render defaults.
- Schema v5 or unreviewed v3/v4 migrations.
- Automatic cloud backup/sync and multi-device history.
- A second project/history/persistence store, sidecar encryption redesign, or additional permanent provider integration.
- Shipping FFmpeg executables in the public Windows ZIP.
- Mass dependency upgrades, Python runtime security-line retargeting, bundled interpreter redesign or historical tag rewrite.
- Speculative “AI automatically fixes corrupt project files” behavior.
- Claiming real 500-scene render completion based only on command-construction benchmark.

## 10. Proposed factory STEP sequence

| STEP | Deliverable | Gate |
|---|---|---|
| **00 — this turn** | Post-release audit, selected product scope, risk/acceptance inventory, comprehensive DOCX, planning status and handoff | No application code; document-source gate |
| **01** | Functional recovery lifecycle rules, decision state machine, Save/Save As behavior and acceptance matrix, detailed DOCX | Decisions documented, no contradictions |
| **02** | Architecture/module wiring map, scheduler contract, error model, security/compatibility plan and detailed DOCX | Architecture/adapter review PASS |
| **03 — UI PROMPT HARD STOP** | Prompts for each new recovery dialog/state; then **STOP** awaiting final user-approved images and one UI reference DOCX | No coding until final visual gate |
| **04** | Deterministic test/failure injection, Windows portable and regression plan, detailed DOCX | Test-first coverage planned |
| **05** | Final implementation authorization, precise file/wave change map, all planning + UI DOCXs committed to repo | Only authorized coding gate |
| **06** | SOL implementation one wave per user turn; tests, commit, Windows acceptance, concise status | Every authorized wave PASS |
| **07** | Frozen RC, final Windows/CodeQL/security, exact-source checksums and immutable new release gate | Published only after complete PASS |

The sequence is a proposal in STEP 00. Later ASTRA planning may refine boundaries; it may not silently skip the UI gate or move to implementation prematurely.

## 11. Baseline repository invariants and release guarantees

- Maintain \`presentation -> application -> domain\`; infrastructure owns filesystem/process/provider adapters.
- Canonical \`ProjectSession\` and \`ProjectHistory\` remain the only project transaction/Undo source.
- Schema max v4 and \`animation_keyframe_contract=advanced-v1\`; migration/future-schema guards enforced.
- Preserve current 21 effects, Qt frozen UI, Gemini credential isolation, subtitle/render contracts and external FFmpeg.
- All changed tests/waves run Windows compile, Ruff, strict mypy, pytest, Qt offscreen screenshot capture, CodeQL and actual packaged EXE where relevant.
- Require exact-source Git history backup and SHA256 provenance before future release publication.
- Published stable v0.2.2 and v0.2.1 tag targets must stay unmodified. A new version must use a *new* release tag after independent planning/authorization.

## 12. STEP 00 gate and handoff

**STEP 00 considered PASS only when its Markdown source, detailed DOCX, planning status and handoff are available and verified in the V2 repository**; no app code/UI/release mutations. If DOCX is only attached to chat or an Actions artifact and has not been committed to the repository, the *repository source-of-truth gate is still HOLD* and coding remains forbidden.

**Exact NEXT:** STEP 01 — functional recovery lifecycle and decision-state specification, **only on the next explicit “lanjutkan” after STEP 00 gate is PASS**. Do not combine STEP 01 with this turn.

**Implementation authority:** NOT GRANTED; all new v0.3.0 runtime code, version bumps, animation changes, UI modifications, package/release writes are blocked until STEP 05 and final UI reference completion.
