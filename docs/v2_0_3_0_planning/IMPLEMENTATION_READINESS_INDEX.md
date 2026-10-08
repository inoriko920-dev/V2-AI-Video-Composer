# ACTIVE V2 v0.3.0 HANDOFF — STEP05 DoR / NO CODING (8 OCT 2026 WIB)

The three revised STEP03-R dialog PNGs and one final image-filled DOCX are approved and in main via PR #54; STEP04 testing Markdown + Word are in main via PR #55. Latest user `lanjutkan` grants only STEP05 planning. Read `05_IMPLEMENTATION_READINESS_AND_SOL_WAVE_AUTHORIZATION_PLAN.md` and the matching Word for required source-of-truth inventory, five W06-A..E wave scopes, test-first RED/GREEN gates and final implementation-authorization conditions.

DoR requires all docs STEP00–05 and approved UI resources in main, plus final-head CI/CodeQL/Windows/backend PASS, docs-only changes and merge. Do **not** infer STEP06 authority from wording such as 'ready'; a separate future user turn is required to begin W06-A. All prior 13-image planning is superseded by the 3-dialog approval. Preserve v0.2.2 stable release, schema-v4 and exact 42-screen editor UI.

---

# ACTIVE HANDOFF — STEP04 TEST-FIRST PLANNING (8 OCT 2026 WIB)

The previous STEP03-R UI gate is **COMPLETE/PASS** after PR #54 merged: three approved PNGs, original editor screenshot, and one final image-filled reference DOCX are authoritative. The user's new `lanjutkan` authorizes **STEP04 planning only**. Read `04_RECOVERY_FAILURE_INJECTION_WINDOWS_TEST_PLAN.md` and the matching DOCX after STEP01/STEP02 safety contracts and before planning STEP05. Matrix IDs: RCV-01..24, SCH-01..12, AT-01..20, UI-01..12, COMP-01..10. Treat all as proposed future tests, **not executed tests**.

STEP04 cannot be declared PASS until both Markdown and real native DOCX have been committed in this V2 repository; PR-head CI + CodeQL + Windows + backend are SUCCESS; the PR is merged and main/trusted stable tag verified. This STEP cannot authorize SOL implementation, Qt changes or release. Following STEP04 PASS, require a separate user turn for STEP05 source-of-truth and wave authorization. Maintain original 42-screen frozen editor and exactly 3 approved dialog references.

---

# LATEST AI HANDOFF OVERRIDE — STEP03-R (8 OCT 2026 WIB)

**AUTHORITATIVE NEW UI POLICY: EXISTING MAIN UI 1:1; ONLY THREE NEW RECOVERY DIALOG REFERENCES.** User explicitly approved this reduction, superseding thirteen legacy images. The original 13 TXT and 6-page prompt DOCX are archival history, NOT pending gates.

Read in order: `docs/UI_FREEZE.md`; `docs/v2_0_3_0_planning/03_STEP03_DIALOG_ONLY_UI_SCOPE_REVISION.md`; `docs/v2_0_3_0_planning/docx/03_V2_0.3.0_DIALOG_ONLY_SCOPE_REVISION.docx`; three `prompt_ui_step03_revised/*.txt`; STEP01/02 recovery safety contract. Real editor is `UI-013_ACTUAL.png`, not `UI-002_ACTUAL.png` (Home), from CI captured STEP09 artifacts.

**STATUS: Revised prompt planning ready; WAITING FOR THREE approved dialog PNGs + ONE FINAL IMAGE-EMBEDDED USER-APPROVED UI REFERENCE DOCX in the repo.** Reuse old QStatusBar, GuardedMainWindow and QMessageBox for minor scenarios instead of bespoke new screens. Do not create an extra UI rebuild, modify Python/PySide6 source, advance STEP04, or publish release. Next generic "lanjutkan" does not remove this user approval hard stop.

---
# V2 0.3.0 — HANDOFF ON STEP03 HARD STOP

**STOP — STEP03 PROMPTS ONLY COMPLETE; ALL 13 UI IMAGES UNGENERATED/UNAPPROVED.** Main authority is `docs/v2_0_3_0_planning/03_UI_PROMPT_COMPLETION_AND_APPROVAL_GATE.md` and `03_PROMPT_GAMBAR_UI_RECOVERY_MASTER.md`.

The **DOCX in `docx/03_V2_0.3.0_STEP03_UI_IMAGE_PROMPTS_ONLY.docx` is a prompt book, not final UI artwork approval.** Each `prompt_ui_step03/UI-REC-XX_*.txt` is one independently generated PNG assignment. Wait for all 13 image results, user review/revisions and ONE actually image-filled, approved `03_V2_0.3.0_APPROVED_FINAL_UI_IMAGE_REFERENCES.docx` to be committed before resuming factory STEP04. No coding, UI Qt, project schema/version, release tag or old repo mutations.

Next bare "lanjutkan" **does not allow bypassing** the visual gate. Explicit image generation/review instructions are permitted, but do not start STEP04 from that request.

---
# ACTIVE HANDOFF — STEP03 UI IMAGE PROMPT HARD STOP

Read `docs/v2_0_3_0_planning/03_PROMPT_GAMBAR_UI_RECOVERY_MASTER.md` followed by its detailed DOCX `docs/v2_0_3_0_planning/docx/03_V2_0.3.0_STEP03_UI_IMAGE_PROMPTS_ONLY.docx`; individual ready-to-run prompts live in `docs/v2_0_3_0_planning/prompt_ui_step03/UI-REC-01_*.txt` through `UI-REC-13_*.txt`.

**Current authority: ASTRA prompts only, HARD STOP afterwards.** Generate all 13 UI reference PNGs one by one in the later image phase, review/revise, create ONE final UI image reference DOCX and commit approved artefacts to this V2 repository. **A new generic "lanjutkan" is not permission to skip that visual approval gate or start STEP04.** Stable v0.2.2 tag/source must remain immutable; original legacy repository untouched.

---
# CURRENT READINESS — v0.3.0 STEP02

**STEP00 PASS / STEP01 PASS / STEP02 COMPLETE only after PR #51 green merge / STEP03 NEXT on subsequent explicit turn.** Planning only; no SOL code or UI is authorized.

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

## STEP02 Word verification
- Canonical Markdown: docs/v2_0_3_0_planning/02_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.md.
- Actual native DOCX committed: docs/v2_0_3_0_planning/docx/02_V2_0.3.0_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.docx (52,472 bytes, 8 visually reviewed pages, 92 paragraphs and 6 tables).
- Generator: docs/v2_0_3_0_planning/_generator/generate_step02_docx.py.
- GitHub Actions run 37732412706 PASS; first run 37732349474 exposed an incorrect QA assertion that ignored table content and was fixed without app changes.
- After verified PR #51 final-head CI/CodeQL/Windows/backend PASS and merge to main, STEP02 is COMPLETE/PASS and STEP03 becomes the only next authorized planning STEP. Before merge, the gate remains HOLD.
