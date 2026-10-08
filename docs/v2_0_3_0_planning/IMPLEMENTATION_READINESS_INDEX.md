# CURRENT READINESS — v0.3.0 STEP02

**STEP00 PASS / STEP01 PASS / STEP02 PENDING Word+PR gate / STEP03 NOT STARTED.** Planning only; no SOL code or UI is authorized.

Read after STEP01: `docs/v2_0_3_0_planning/02_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.md` and its actual repository DOCX `docs/v2_0_3_0_planning/docx/02_V2_0.3.0_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.docx`.

STEP02 source-of-truth architecture: RecoveryCoordinator is application-only; existing RecoveryManager/persistence serializer handles byte safety; single writer/path lease; Qt adapter is scheduling-only; sidecar SHA-256 is integrity check, not cryptographic authentication; two-file snapshot+metadata cannot be assumed atomic; stale tokens and Save As collisions fail closed. Current published v0.2.2 is immutable. STEP03 future UI prompt **HARD STOP** remains mandatory.

---
# CURRENT READINESS — V2 0.3.0

**STEP00 PASS / STEP01 PASS / STEP02 NEXT.** STEP01 PR #49 merged. CI run 37730948284 PASS; CodeQL 37730948270 PASS; Windows acceptance 37730948312 PASS; backend 37730948224 PASS. No coding, UI image generation, schema/version changes or release publication authorized. Published v0.2.2 remains immutable. The future STEP03 UI image-prompt stop is mandatory.

# V2 0.3.0 — New Planning / AI Handoff Index

**Authority:** New ASTRA planning cycle; STEP00 PASS. STEP01 functional spec is the ONLY current work. No SOL coding or release publication authorized.

## Mandatory reading order for any later AI
1. `AGENTS.md`
2. `docs/v2_0_2_2_planning/STEP07_FINAL_RELEASE_CLOSURE.md` — immutable v0.2.2 stable baseline
3. `V2_0.3.0_PLANNING_STATUS.md`
4. `docs/v2_0_3_0_planning/00_PRODUCT_GAP_AUDIT_AND_RECOVERY_SCOPE.md`
5. `docs/v2_0_3_0_planning/docx/00_V2_0.3.0_PRODUCT_GAP_AUDIT_AND_RECOVERY_SCOPE.docx`
6. `docs/v2_0_2_2_planning/03_SCHEMA_V4_PERSISTENCE_RECOVERY_STRESS_PLAN.md`
7. `docs/ARCHITECTURE.md`, `docs/CODE_CONSTITUTION.md`, `docs/PROJECT_STATE.md`, `docs/UI_FREEZE.md`
8. docs/v2_0_3_0_planning/01_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.md
9. docs/v2_0_3_0_planning/docx/01_V2_0.3.0_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.docx (must exist in repo before STEP01 PASS)
10. STEP02–05 and final UI reference DOCX, once those actually exist and are accepted

## Current authority and hard gates
- STEP 00 product audit and scope: **PASS / COMPLETE after PR #48 CI/CodeQL/Windows checks and merge**.
- STEP 01 functional flow planning: **PASS / COMPLETE**.
- STEP 02 architecture/error policy planning: **CURRENT / Word and CI gate pending**.
- STEP 03 **UI prompt hard stop**: **NOT STARTED**; special user approval and one final UI reference DOCX mandatory.
- STEP 04 testing plan: **NOT STARTED**.
- STEP 05 coding authorization: **NOT STARTED**.
- STEP 06 code implementation: **PROHIBITED**.
- STEP 07 release: **PROHIBITED**.

## Proposal and implementation boundaries
- **Reuse first**: `RecoveryManager`, `ProjectSession`, Qt window/startup, existing serializer/schema v4.
- **Potential version**: v0.3.0 (proposed minor). Do not bump metadata yet.
- **Priority**: GAP-03A, production autosave/recovery UX, with deterministic safety.
- **Preserve**: v0.2.2 tag/release; white-blue UI/42 reference screens; 21 native effects; Gemini credential boundaries; external FFmpeg; schema v4 and advanced-v1.
- **Do not silently declare complete**: automatic snapshots, open-time recovery, corrupt-recovery workflow, successful Save clearing stale autosaves. These require new runtime tests.
- **Next exact action**: user-authorized STEP 01 only after this STEP 00 passes; one STEP per conversation turn.

## Handoff evidence
- Audit baseline main SHA `186844bdab3a8665488204fd75b9309f1fad5d5b`.
- Frozen stable SHA `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`, released at https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/tag/v0.2.2 .
- Documentation and DOCX generator created on branch `v2/0.3.0-planning-step00`.
- Current branch changes are planning-only. No app source code/UI/schema/release workflow modifications are allowed.

## Generated DOCX provenance
- Canonical file: `docs/v2_0_3_0_planning/docx/00_V2_0.3.0_PRODUCT_GAP_AUDIT_AND_RECOVERY_SCOPE.docx` (actual DOCX bytes committed to repo).
- Reproducible generator: `docs/v2_0_3_0_planning/_generator/generate_step00_docx.py`.
- Actions evidence: generation `37728819011` PASS, independent read-only review `37728948765` PASS, refined generator/QA `37729351791` PASS.
- Visual QA: rendered 5 pages; tables legible, repeated headers, no extra/orphan page.
- One-shot write-capable workflow removed itself without writing to main. Review workflow removed before merge.
- Only next authorized action after CI/CodeQL and merge: STEP01 functional recovery lifecycle planning.

## STEP01 specific handoff
- Contract uses existing RecoveryManager and ProjectSession; no second project serializer/history engine.
- User's unsaved-current-project guard resolves BEFORE inspecting/opening the target's recovery candidate.
- Verified valid candidate -> Restore / Discard / Cancel; metadata-free or changed-disk candidate -> conflict warning with extra explicit Restore acknowledgement.
- Timer cadence proposed: 20s debounce, maximum 120s dirty lag, 60s poll and bounded errors.
- Functional 24-case matrix and coordinator state transition contract are the source for STEP02 architecture and STEP04 test plans.
- STEP03 image prompt phase must STOP pending approved final UI images and one committed final UI reference DOCX, even after bare 'lanjutkan'.
- STEP01 gate: PASS. Native DOCX committed; 9-page visual QA PASS; PR #49 merged as 38094913ebcab3d1992b252659d40a0049caf6a6; CI, CodeQL, Windows acceptance and backend PASS. STEP02 is NEXT only on new explicit user 'lanjutkan'.

## STEP01 planning-document audit
- Source spec: docs/v2_0_3_0_planning/01_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.md.
- Detailed DOCX: docs/v2_0_3_0_planning/docx/01_V2_0.3.0_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.docx (52,688 bytes, 9 pages, readable and rendered).
- Deterministic generator: docs/v2_0_3_0_planning/_generator/generate_step01_docx.py.
- GitHub Action DOCX creation: 37730728343 PASS; ephemeral writer deleted itself from dedicated branch.
- Tests and feature implementation still NOT AUTHORIZED. All referenced RCV-01 to RCV-24 are *planned*, not passing automated runtime tests.
- UI STEP03 hard stop and all planning DOCX prerequisites unchanged.
