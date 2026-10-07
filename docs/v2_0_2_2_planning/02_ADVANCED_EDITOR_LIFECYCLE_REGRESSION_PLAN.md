# STEP 02 — V2 0.2.2 Advanced Editor Lifecycle Regression Plan

Status: **PASS / PLANNING ONLY**

Audited main: `94b265959b08b666a0f512c85f3bd9e46e8afce2`  
Frozen stable release: `v0.2.1` @ `eb94efebf142ba8203dfc3ae3c5fa861222a0926`

## Purpose

STEP 02 defines regression coverage for the existing `Animasi Aset` / Keyframe editor and its integration with `ProjectSession`.
No application implementation is authorized in this STEP.

The plan must prove the user-visible lifecycle around:
- local working-copy edits;
- Apply / Discard / Cancel while switching assets;
- schema-v3 vs schema-v4 badge/state;
- advanced-v1 activation confirmation;
- project-wide dormant-track acknowledgement;
- repeated activation behavior;
- Remove confirmation;
- one-transaction Undo/Redo semantics.

## Source-derived lifecycle model

The current dialog already contains:
- `originals` and `working` assignment maps per asset;
- `dirty_assets` tracking;
- local edit suppression while controls are refreshed;
- Apply / Buang Perubahan / Batal choice when changing asset with local changes;
- Preset and Keyframe tabs;
- Legacy v3 / Advanced v4 badge input through `project_schema_version`;
- local keyframe Add / Delete / Previous / Next / Reset Track;
- dormant/ADV markers based on schema and advanced track requirements;
- destructive confirmation for removing an asset assignment.

The command layer already contains:
- `ApplyAnimationKeyframeEdit`;
- typed `AdvancedAnimationActivationRequired`;
- atomic v3 -> v4 + `animation_keyframe_contract=advanced-v1` promotion;
- dormant-track acknowledgement;
- no-repeat activation for already-v4 projects;
- exact Undo restoration to pre-edit state.

Existing `tests/unit/test_v2_k7_ui_transactions.py` proves the command-level transaction contract, but it does not drive the actual Qt dialog/controller lifecycle.

## Static integration gap discovered by STEP 02

A source audit found a concrete wiring mismatch between the intended K7 contract and the current UI caller:

1. `AnimationMenuMainWindow.edit_selected_scene_asset_motion()` calls:
   `show_asset_motion_dialog(self.window, scene, project.animations)`
   without passing `project_schema_version=project.schema_version`.

   Consequence to reproduce with tests:
   - the modal receives its default schema version `3`;
   - a real schema-v4 project can be presented as `Legacy v3`;
   - property marker/inline activation messaging can therefore use the wrong contract state.

2. After dialog Apply, the same controller currently executes:
   `SetAnimationAssignment(result.assignment)`.

   It does not route the edit through `ApplyAnimationKeyframeEdit`, and it does not handle `AdvancedAnimationActivationRequired`.

   Consequence to reproduce with tests:
   - v3 advanced edits can bypass the intended activation confirmation path;
   - schema-v4 + advanced-v1 atomic promotion is not proven by the user-facing controller path;
   - project-wide dormant acknowledgement is not proven by the UI path;
   - command-level tests can pass while the actual click path remains incorrectly wired.

This STEP records the mismatch as a **confirmed static wiring gap**. It is not yet labeled a fixed runtime bug. STEP 06 implementation may only correct it after a failing regression test reproduces the user-visible behavior.

## Test architecture

No new test dependency is planned.

Use the existing stack:
- Python 3.12;
- PySide6 6.11.2;
- pytest 9.1.1;
- `QT_QPA_PLATFORM=offscreen` for tests that construct real widgets/dialogs;
- monkeypatching of `QMessageBox` / dialog execution only where deterministic button selection is required.

Do not add `pytest-qt` merely for convenience. A new dependency would violate the patch-scope rule unless STEP 04 separately proves it necessary.

Tests should be split into three layers:

### L1 — Pure dialog working-copy regression
Drive real `show_asset_motion_dialog` widgets offscreen and prove local state behavior without committing a `ProjectState` mutation.

### L2 — Window/controller wiring regression
Drive `AnimationMenuMainWindow.edit_selected_scene_asset_motion()` with deterministic dialog results and confirmation responses. Verify exactly which command reaches `ProjectSession` and how schema activation is handled.

### L3 — Session integration lifecycle
Use a real `ProjectSession` with v3/v4 project fixtures to prove history, dirty state, activation and Undo/Redo boundaries after the UI/controller action.

## Planned regression matrix

### AED-01 — Open and cancel is zero mutation
Given a v3 project and existing assignment, opening the modal and pressing Batal must:
- return `None`;
- leave `ProjectSession.current` unchanged;
- leave `is_dirty` unchanged;
- create no Undo history entry;
- keep schema v3.

### AED-02 — Tab/property navigation is zero mutation
Switching Preset <-> Keyframe, selecting an advanced property, and browsing keyframes without editing must not mutate project/session state.

### AED-03 — Local preset edit marks only dialog working copy
Changing enter/exit/intensity/lock must mark the active asset dirty locally, preserve any existing keyframe tracks, and not touch `ProjectState` until Apply.

### AED-04 — Asset switch / Apply
When asset A is locally dirty and user selects asset B, choosing `Terapkan` must:
- return exactly one Apply result for asset A;
- use asset A's complete working copy;
- not silently apply asset B;
- close the modal deterministically.

### AED-05 — Asset switch / Discard
When asset A is dirty and user selects B, choosing `Buang Perubahan` must:
- restore asset A from `originals`;
- clear A from `dirty_assets`;
- continue to asset B;
- return no project mutation until a later Apply.

### AED-06 — Asset switch / Cancel
When asset A is dirty and user selects B, choosing `Batal` must:
- restore the combo selection to asset A;
- preserve A's local working copy;
- preserve dirty state;
- not close the modal;
- not mutate `ProjectState`.

### AED-07 — Correct schema badge / v3
A real schema-v3 project must open the modal with `Legacy v3` and dormant advanced track markers where applicable.

### AED-08 — Correct schema badge / v4
A real schema-v4 advanced-v1 project must pass its schema version into the dialog and display `Advanced v4`; advanced tracks must show as active ADV rather than Dormant.

This test is expected to expose the current caller mismatch before implementation.

### AED-09 — Foundational Apply remains v3
A Position/Scale/Rotation linear edit that remains legacy-compatible must:
- commit through the canonical transaction path;
- remain schema v3;
- create exactly one history entry;
- be Undo/Redo stable.

### AED-10 — Preset-only Apply with dormant advanced tracks remains v3
Preset changes on a v3 project containing dormant advanced tracks must preserve those tracks and must not activate advanced-v1.

### AED-11 — Advanced v3 Apply requires activation confirmation
An Opacity/Crop/Mask/Blur/Shadow/Glow advanced change, or Bezier/velocity/overshoot semantics, must not commit directly.
The controller must surface an activation decision before any mutation.

This test is expected to expose the current `SetAnimationAssignment` bypass before implementation.

### AED-12 — Reject advanced activation = zero mutation
If the user rejects `Aktifkan Advanced Animation?`:
- schema stays v3;
- metadata stays unchanged;
- assignment remains unchanged;
- session dirty/history state remains unchanged.

### AED-13 — Accept activation = one atomic history entry
If activation is accepted:
- schema becomes v4;
- `animation_keyframe_contract=advanced-v1` is written;
- the asset edit is committed in the same transaction;
- only one Undo entry is created;
- Undo restores the exact pre-edit v3 project;
- Redo restores the exact v4 project.

### AED-14 — Dormant project-wide acknowledgement is required
If unrelated dormant advanced tracks exist elsewhere in the project, activation must not proceed until the user explicitly acknowledges that those tracks become active project-wide.

Reject/close of the acknowledgement path must be zero mutation.

### AED-15 — Already-v4 advanced edit does not prompt again
Once schema v4 + advanced-v1 is active, a later advanced edit must not show the activation prompt again and must remain one normal history transaction.

### AED-16 — Repeated dialog open/close has no state leakage
Open, edit locally, cancel, reopen the same asset. The second dialog must start from actual project state, not a prior dialog's discarded local working copy.

### AED-17 — Remove / No is zero mutation
`Hapus Animasi Aset` followed by No must preserve assignment/history/session dirty state.

### AED-18 — Remove / Yes is one undoable mutation
Confirming removal must remove the whole assignment through the canonical remove command and one Undo must restore it exactly.

### AED-19 — Manual editing remains allowed on Auto/AI locked assignment
`locked=True` must continue to block automation replacement only. Direct manual preset/keyframe edits remain allowed and the lock flag is preserved/changed only according to explicit user controls.

### AED-20 — Invalid edit/error path cannot half-commit
If validation rejects a proposed track/assignment, the controller must show an error and leave schema, metadata, assignment and history unchanged.

### AED-21 — Dirty state / title consistency
After successful Apply, session `is_dirty` and the main-window dirty marker must reflect the new transaction. After Undo to the saved checkpoint, state/title behavior must follow the existing ProjectSession checkpoint contract.

### AED-22 — Frozen main UI remains unchanged
The existing eight STEP09 main-window screenshots remain a regression gate. Lifecycle hardening must not redesign the main window or alter the 42 frozen UI references.

## Planned test files

Likely implementation targets after STEP 05 authorization:

New:
- `tests/unit/test_v2_0_2_2_asset_motion_dialog_lifecycle.py`
- `tests/unit/test_v2_0_2_2_animation_menu_advanced_wiring.py`
- `tests/integration/test_v2_0_2_2_advanced_editor_lifecycle.py`

Extend only where it preserves ownership:
- `tests/unit/test_v2_k7_ui_transactions.py` for command invariants;
- `tests/unit/test_animation_menu_window.py` for routing/state helper invariants;
- `tests/unit/test_native_asset_motion_editor.py` for preset-track preservation/removal behavior.

Probable application files that later failing tests may authorize for correction:
- `src/aavc/presentation/windows/animation_menu_window.py`;
- `src/aavc/presentation/dialogs/asset_motion.py` only if the dialog itself fails a lifecycle test.

Do not pre-authorize edits to persistence/schema/render code from this STEP.

## Deterministic Qt test rules

- Set `QT_QPA_PLATFORM=offscreen` before constructing QApplication.
- Reuse a single QApplication per test process where possible.
- Never rely on human clicking or wall-clock sleeps.
- Use deterministic QMessageBox button selection through monkeypatch/test hooks.
- Do not save screenshots as the assertion for lifecycle semantics; assert state/command/history directly.
- Screenshot gates remain a separate visual-regression check.
- Ensure every constructed dialog/window is closed/deleted so repeated tests do not leak widgets or event state.

## Activation confirmation contract for implementation tests

The UI-facing activation flow must eventually prove the exact sequence:

1. Dialog returns an Apply candidate.
2. Controller calls `ApplyAnimationKeyframeEdit(candidate)` without activation flags.
3. If no activation is required, command commits normally.
4. If `AdvancedAnimationActivationRequired` is raised, controller displays activation information before mutation.
5. If unrelated dormant tracks exist, confirmation explicitly includes/collects acknowledgement.
6. Cancel/reject returns with zero mutation.
7. Accept retries the same command with `activate_advanced=True` and, when required, `acknowledge_dormant=True`.
8. The successful retry is one atomic ProjectSession history entry.
9. Existing v4 projects skip steps 4-7.

The test should assert this command sequence, not only the final schema number.

## Release-blocking acceptance criteria

STEP 06 implementation may not be considered complete until all mandatory cases below pass on Windows CI:
- AED-01 through AED-21;
- existing K7 command tests;
- existing 21-effect/preset regression tests;
- existing full cheap unit suite;
- CodeQL;
- eight STEP09 screenshot capture/verification;
- no new runtime/test dependency unless separately approved.

At RC/final, the broader v0.2.2 gate will also include real FFmpeg and packaged-EXE acceptance from later planning STEPs.

## Stop conditions

Implementation must STOP rather than hide failure if:
- an advanced Apply can mutate a v3 project without an explicit activation decision;
- Cancel/Discard mutates ProjectState or history;
- one accepted advanced edit creates multiple history entries;
- Undo does not restore the exact pre-edit project;
- a v4 project is presented as Legacy v3;
- repeated dialogs leak discarded working-copy state;
- the fix requires schema v5, UI redesign, or a new runtime dependency.

Any such architectural expansion would require a new planning decision rather than being smuggled into v0.2.2.

## STEP 02 gate

**PASS**

The advanced-editor lifecycle is now expressed as a deterministic regression contract, including the currently untested Qt/controller boundary and the static caller/command mismatch discovered during audit.

No application code has been changed. The mismatch remains intentionally unfixed until later implementation authorization and failing-before evidence.

## Next exact STEP

**STEP 03 — Schema-v4 Persistence / Recovery Stress Plan**

STEP 03 must define stress/regression coverage for:
- v3 -> v4 first overwrite backup;
- non-clobbering `.pre-schema-v4.bak` behavior;
- repeated Save / Save As;
- autosave/recovery across v3/v4;
- downgrade prevention;
- future-schema / marker mismatch rejection;
- crash/recovery simulation and exact state preservation.

Do not begin STEP 04 or implementation in the same turn.
