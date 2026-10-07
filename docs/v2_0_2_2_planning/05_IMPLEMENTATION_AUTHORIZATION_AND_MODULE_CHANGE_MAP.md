# STEP 05 — V2 0.2.2 Implementation Authorization + Module / Change Map

Status: **PASS / IMPLEMENTATION AUTHORIZED FOR STEP 06 ONLY**

Audited main: `89a1c68ddf948828a23d7672023a5c2ebb477693`  
Frozen stable release: `v0.2.1` @ `eb94efebf142ba8203dfc3ae3c5fa861222a0926`

## Purpose

STEP 05 is the final planning/authorization gate for v0.2.2. It consolidates STEP 00–04, freezes the patch scope, decides which discovered gaps are REQUIRED versus DEFERRED, maps exact modules/tests/workflows, and defines the implementation waves and promotion gates.

No application implementation is performed in STEP 05. Coding may begin only in STEP 06 after this document, its DOCX, planning status and readiness index are merged into `main`.

## Product decision

v0.2.2 remains a **maintenance/hardening patch**, not a feature release.

The patch must:
- fix the advanced-editor controller wiring defect discovered in STEP 02;
- harden persistence/recovery file safety from STEP 03;
- correct repository/workflow/backup hygiene from STEP 01;
- harden Windows packaging/release reproducibility from STEP 04;
- preserve schema v4 / `advanced-v1`, the copied white/blue UI, 21 native effects, FFmpeg rendering semantics and Gemini credential model.

It must not:
- introduce schema v5;
- redesign the UI;
- add a permanent keyframe panel/dock;
- add a second persistence engine;
- add a runtime dependency;
- bundle FFmpeg into the public portable ZIP;
- alter published v0.2.0/v0.2.1 tags/releases.

## Authorization matrix

### REQUIRED for v0.2.2

**AUTH-01 — GAP-02A: correct schema context into the Asset Animation dialog**
- Pass the actual `project.schema_version`.
- A v4 project must display Advanced v4, never Legacy v3.
- Test-first.

**AUTH-02 — GAP-02B: route advanced edits through the canonical activation command**
- Controller must use `ApplyAnimationKeyframeEdit`.
- Catch typed `AdvancedAnimationActivationRequired`.
- Reject/cancel => zero mutation.
- Accept => retry with `activate_advanced=True`.
- When unrelated dormant advanced tracks exist, require explicit acknowledgement before retry.
- Existing v4 projects must not prompt again.
- One accepted edit = one history transaction.

**AUTH-03 — GAP-03B: make recovery backups non-clobbering**
- Adopt deterministic numbered pre-recovery backups:
  - first: `.pre-recovery.bak`
  - later: `.pre-recovery.1.bak`, `.pre-recovery.2.bak`, ...
- Never overwrite an existing recovery backup.
- No automatic pruning in v0.2.2.

**AUTH-04 — GAP-03C: fail closed on unreadable existing project destinations**
- If destination exists but its schema cannot be safely read because the file is malformed/unreadable, normal Save/Save As must not overwrite it.
- Raise a typed/recognizable persistence error such as `PROJECT_DESTINATION_UNREADABLE`.
- New/non-existent targets remain allowed.
- Existing valid newer schema remains protected by `SCHEMA_DOWNGRADE_BLOCKED`.

**AUTH-05 — repository/workflow hygiene**
- Close PR #11 and #17 as superseded without merge.
- Do not merge the stale Dependabot branch.
- Correct `backup-single-app.yml` to V2 and current stable line.
- Pin remaining active external GitHub Actions by commit SHA.
- Retire/convert automatic DOCX write-back workflows so planning generators cannot push directly to `main`.
- Preserve historical v0.2.0/v0.2.1 workflows as manual/read-only verification.

**AUTH-06 — packaging hardening**
- Use explicit reference FFmpeg/ffprobe identity for acceptance; v0.2.1 reference is 9.0.2 unless implementation evidence requires a separately reviewed change.
- Prefer `upx=False`; no opportunistic UPX.
- Add built-artifact credential-pattern scan.
- Prove PATH and app-local FFmpeg modes and app-local precedence.
- Final distributable must exclude FFmpeg binaries.
- Update all version-coupled packaging docs/checks to v0.2.2.
- Record BUILD_INFO + SHA-256 + exact source archive.
- Introduce new v0.2.2 RC/final workflow; never repurpose historical publisher workflows.

**AUTH-07 — version/release metadata for the new patch**
- Version becomes `0.2.2` only in the dedicated packaging/release-prep wave.
- Synchronize `pyproject.toml`, `src/aavc/__init__.py`, release notes, manifest, workflow expectations and artifact names.
- Do not move the v0.2.1 tag.

### CONDITIONAL / MAY ADOPT ONLY WITH ZERO-SCOPE-EXPANSION PROOF

**COND-01 — Ruff 0.16.8 -> 0.16.10**
- Dev-only.
- Adopt only if no unrelated source rewrite/churn is required and all gates pass.
- Otherwise defer.

### DEFERRED from v0.2.2

**DEFER-01 — GAP-03A production autosave/recovery UI/runtime integration**
- RecoveryManager engine exists, but wiring autosave timers/on-change snapshots and Restore/Discard/Cancel product flow is a new user-visible runtime capability.
- Defer to a separately planned maintenance/minor cycle.
- Direct RecoveryManager safety fixes remain in scope.

**DEFER-02 — Python 3.12 security-line interpreter bump**
- Keep reproducible 3.12.10 baseline for v0.2.2.
- Evaluate later in an isolated toolchain project.

**DEFER-03 — setuptools build-backend alignment 80.10.2 -> 84.0.0**
- Existing split is not a confirmed defect.
- Do not mix toolchain alignment with correctness fixes.

**DEFER-04 — broad dependency refresh**
- PySide6/pytest/mypy/PyInstaller/hooks/packaging/pip remain unchanged.

**DEFER-05 — bulk deletion of historical release/implementation branches**
- Close stale PRs now.
- Keep historical branches until post-v0.2.2 release closure unless a branch is proven purely transient and safe to remove.
- Full Git Bundle backup already exists and remains independent evidence.

## Required test-first evidence

No required defect may be fixed before its failing-before test/contract evidence exists.

### FB-02A
A controller test captures the `show_asset_motion_dialog(...)` call for a schema-v4 project and expects `project_schema_version=4`. It must fail on the current main before the fix.

### FB-02B
A controller/session test applies a v3 advanced edit and expects:
1. initial `ApplyAnimationKeyframeEdit` attempt;
2. `AdvancedAnimationActivationRequired`;
3. zero mutation before user decision;
4. reject => zero mutation;
5. accept => retry with activation and one transaction.

It must fail on current main because the UI path uses `SetAnimationAssignment`.

### FB-03B
Perform two valid recoveries and assert the first `.pre-recovery.bak` remains unchanged while a new numbered backup is created. It must fail on current main.

### FB-03C
Create a malformed existing `.aavcproj`, attempt Save/Save As, and assert the file remains byte-identical with a persistence error. It must fail on current main.

### FB-04
Static/packaging contract checks must demonstrate the current failures before remediation:
- wrong repo/v0.1.1 in backup workflow;
- unpinned active action refs;
- `upx=True`;
- v0.2.1 release-note coupling;
- absent artifact credential scan;
- acceptance workflow does not enforce the selected FFmpeg reference.

## STEP 06 implementation waves

Only one implementation wave may be completed per user turn.

### W06-A — Repository Hygiene + Workflow Security

Scope:
- close PR #11 and #17 without merge;
- correct V2 backup workflow and verified Git Bundle behavior;
- SHA-pin active external actions;
- retire direct-to-main DOCX write-back workflows;
- do not touch runtime source.

Primary files/objects:
- `.github/workflows/backup-single-app.yml`
- `.github/workflows/generate-v2-0.2.2-step00-docx.yml`
- `.github/workflows/generate-v2-planning-docx.yml`
- PR #11
- PR #17
- stale Dependabot proposal/branch handling
- optional workflow-contract tests/scripts

Promotion gate:
- workflow static checks PASS;
- backup run creates V2 source + full verified Git Bundle + stable V2 build evidence;
- historical release workflows unchanged/read-only;
- CI/CodeQL PASS.

### W06-B — Advanced Editor Lifecycle Wiring

Scope:
- add AED lifecycle/controller regression tests required by AUTH-01/AUTH-02;
- fix schema-version propagation;
- replace direct advanced Apply path with `ApplyAnimationKeyframeEdit` activation flow;
- preserve preset path, lock semantics, working-copy behavior and UI layout.

Primary implementation file:
- `src/aavc/presentation/windows/animation_menu_window.py`

Only if failing tests prove necessary:
- `src/aavc/presentation/dialogs/asset_motion.py`

Test files:
- new `tests/unit/test_v2_0_2_2_asset_motion_dialog_lifecycle.py`
- new `tests/unit/test_v2_0_2_2_animation_menu_advanced_wiring.py`
- possible integration lifecycle file
- existing K7/native editor tests remain regression authorities.

Promotion gate:
- FB-02A/FB-02B fail before fix and pass after;
- AED required subset PASS;
- activation reject = zero mutation;
- accept = one transaction; Undo exact;
- v4 no-repeat prompt;
- 8 STEP09 screenshots unchanged;
- full cheap suite + Windows acceptance + CodeQL PASS.

### W06-C — Persistence / Recovery File Safety

Scope:
- add PRS stress tests for AUTH-03/AUTH-04;
- introduce deterministic non-clobbering numbered recovery backup path;
- fail closed on malformed/unreadable existing project destination;
- preserve current atomic temp/replace model.

Primary implementation files:
- `src/aavc/persistence/recovery.py`
- `src/aavc/persistence/serializer.py`

Only if tests prove necessary:
- `src/aavc/application/services/project_session.py`
- `src/aavc/persistence/project_repository.py`

Tests:
- new schema-v4 save stress tests;
- new recovery stress tests;
- new failure-atomicity tests;
- extend current session/save-as/schema-v4 tests.

Explicitly excluded:
- autosave timer/on-change wiring;
- recovery prompt/UI integration;
- schema changes.

Promotion gate:
- FB-03B/FB-03C fail before fix and pass after;
- PRS applicable non-runtime cases PASS;
- no partial destination;
- no clobbered recovery backup;
- no app-owned temp debris;
- failed save does not advance session baseline/path;
- existing migration/schema tests PASS;
- CI/CodeQL PASS.

### W06-D — Windows Packaging / Dependency Hardening

Scope:
- version bump to 0.2.2;
- package metadata/release-note synchronization;
- `upx=False`;
- built-artifact credential-pattern scan;
- explicit FFmpeg reference verification;
- PATH + app-local FFmpeg acceptance and precedence;
- final ZIP excludes FFmpeg binaries;
- update provenance only for adopted changes;
- Ruff patch only if conditional gate remains zero-churn;
- create v0.2.2 RC/final workflow scaffolding, but do not publish in STEP 06.

Primary files:
- `pyproject.toml`
- `src/aavc/__init__.py`
- `requirements.lock` only if Ruff is adopted
- `aavc.spec`
- `scripts/package.ps1`
- `scripts/verify_portable.ps1`
- secret/artifact scan helper
- `tools/ffmpeg/README.md`
- `LICENSES/dependency_provenance.csv` if needed
- `.github/workflows/package-windows.yml`
- `.github/workflows/v2-user-acceptance.yml`
- new versioned v0.2.2 RC/final workflow
- `RELEASE_NOTES_0.2.2.md`
- `V2_FINAL_RELEASE_MANIFEST_0.2.2.md`

Promotion gate:
- WPK-01..WPK-30 applicable pre-release gates PASS;
- package version identity exactly 0.2.2;
- portable EXE smoke + real UI launch PASS;
- repository + built-artifact secret scans PASS;
- app-local/PATH FFmpeg proofs PASS;
- source and portable candidate SHA-256 PASS;
- no v0.2.1 tag/release mutation;
- no publication yet.

### W06-E — Consolidated Implementation Closure

Scope:
- no new feature coding;
- run all v0.2.2 implementation regression matrices together;
- update implementation status/handoff;
- freeze exact RC candidate source for STEP 07.

Promotion gate:
- all W06-A..D accepted;
- no open required failing test;
- no required item silently deferred;
- full Windows technical suite PASS;
- 21 effects and advanced animation regression PASS;
- persistence stress PASS;
- portable/package acceptance PASS;
- CI + CodeQL PASS;
- exact next action becomes STEP 07 only.

## Required vs deferred test matrix

Required for v0.2.2:
- AED-01..AED-22 where applicable to the existing UI/controller path;
- PRS-01..PRS-22;
- PRS-26..PRS-30;
- WPK-01..WPK-30 applicable before publication;
- existing v0.2.1 K7/schema/render/21-effect/portable regression.

Deferred with GAP-03A:
- PRS-23, PRS-24 and PRS-25 runtime autosave/recovery integration cases.

## UI / image gate decision

**NO NEW UI IMAGE-PROMPT STEP IS REQUIRED FOR v0.2.2.**

Reason:
- authorized UI work is controller wiring inside the already-frozen `Animasi Aset` experience;
- no main-window redesign, new dock, new panel or new visual language is authorized;
- existing 42 UI references and eight STEP09 screenshot states remain source of truth;
- behavioral/offscreen Qt evidence is the correct verification method.

Therefore the special UI-image hard stop is **not triggered** in this v0.2.2 plan.

If implementation unexpectedly requires a visual redesign, STOP immediately and create a new UI planning/prompt gate before continuing.

## Source-of-truth completeness gate

Before W06-A starts, repository `main` must contain:
- STEP 00 Markdown + DOCX;
- STEP 01 Markdown + DOCX;
- STEP 02 Markdown + DOCX;
- STEP 03 Markdown + DOCX;
- STEP 04 Markdown + DOCX;
- this STEP 05 Markdown + DOCX;
- `V2_0.2.2_PLANNING_STATUS.md`;
- `IMPLEMENTATION_READINESS_INDEX.md`;
- v0.2.1 final closure/status;
- existing UI source-of-truth references.

Once this STEP 05 package is merged and CI/CodeQL remain healthy, the planning gate is complete.

## Implementation authorization

**AUTHORIZED, BUT ONLY STARTING WITH STEP 06 / W06-A ON THE NEXT USER TURN.**

STEP 05 itself performs no implementation.

The implementer must:
1. read STEP 00–05 in order;
2. follow the required/deferred matrix;
3. create failing-before evidence before each required fix;
4. complete one W06 wave per user turn;
5. report tests/gate/commit and exact next wave;
6. never jump to release publication before STEP 07.

## STEP 05 gate

**PASS — PLANNING COMPLETE / IMPLEMENTATION AUTHORIZED FOR NEXT STEP**

No UI-image prompt is required.
No coding occurred in STEP 05.

## Next exact STEP

**STEP 06 — Targeted Implementation Waves, beginning only with W06-A — Repository Hygiene + Workflow Security.**

Do not begin W06-B in the same turn as W06-A.
