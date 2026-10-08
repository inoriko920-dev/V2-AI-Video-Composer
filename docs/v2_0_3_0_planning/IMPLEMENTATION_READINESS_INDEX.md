# V2 0.3.0 — New Planning / AI Handoff Index

**Authority:** New ASTRA planning cycle for user-visible autosave/recovery completion. No SOL coding or release publication authorized.

## Mandatory reading order for any later AI
1. `AGENTS.md`
2. `docs/v2_0_2_2_planning/STEP07_FINAL_RELEASE_CLOSURE.md` — immutable v0.2.2 stable baseline
3. `V2_0.3.0_PLANNING_STATUS.md`
4. `docs/v2_0_3_0_planning/00_PRODUCT_GAP_AUDIT_AND_RECOVERY_SCOPE.md`
5. `docs/v2_0_3_0_planning/docx/00_V2_0.3.0_PRODUCT_GAP_AUDIT_AND_RECOVERY_SCOPE.docx`
6. `docs/v2_0_2_2_planning/03_SCHEMA_V4_PERSISTENCE_RECOVERY_STRESS_PLAN.md`
7. `docs/ARCHITECTURE.md`, `docs/CODE_CONSTITUTION.md`, `docs/PROJECT_STATE.md`, `docs/UI_FREEZE.md`
8. STEP 01–05 and final UI reference DOCX, once those actually exist and are accepted

## Current authority and hard gates
- STEP 00 product audit and scope: **PASS / COMPLETE after PR #48 CI/CodeQL/Windows checks and merge**.
- STEP 01 functional flow planning: **NOT STARTED**.
- STEP 02 architecture/error policy planning: **NOT STARTED**.
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
