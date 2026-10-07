# V2 0.2.1 — Implementation Readiness Index

Status: **READY FOR K0 ONLY**

Stable release baseline:
- tag: `v0.2.0`
- release commit: `c6ad75308d302cd816301a2a7a34ebe7eb4148a7`
- immutable: **YES**

Planning branch:
`v2/0.2.1-advanced-animation-planning`

## Authoritative planning DOCXs

| Step | Repository path | SHA-256 |
|---|---|---|
| 00 | `docs/v2_0_2_1_planning/docx/00_V2_0.2.1_ADVANCED_ANIMATION_SCOPE_AND_GAP_AUDIT.docx` | `ee354c48d4dc9b3b86c7f515cddf3bb748ad38b45a27ad4ff22dbfd8276cfcba` |
| 01 | `docs/v2_0_2_1_planning/docx/01_V2_0.2.1_MATHEMATICAL_AND_PROPERTY_CONTRACT.docx` | `725c0ec86f720899c0c170eec527b3d29df0cff51c2851a86aa02e9a06d1652a` |
| 02 | `docs/v2_0_2_1_planning/docx/02_V2_0.2.1_BACKEND_FEASIBILITY_AND_RENDER_ARCHITECTURE.docx` | `ab5c658a2bd46770002f30fe55f02b1c28fc89e9675020bcedad8c57177a50df` |
| 03 | `docs/v2_0_2_1_planning/docx/03_V2_0.2.1_DATA_CONTRACT_ACTIVATION_AND_MIGRATION_PLAN.docx` | `cd7bd83eb0e32ac2dd0162c93a1f2e93e3008913bf8d81db271789184bdea140` |
| 04 | `docs/v2_0_2_1_planning/docx/04_V2_0.2.1_UI_AND_EDITING_INTERACTION_CONTRACT.docx` | `3f4c520259f6c17f8ad714533c4bfc28995d3c3aa9b7493a3e6524e5cca0756b` |
| 05C | `docs/v2_0_2_1_planning/docx/05C_V2_0.2.1_UI_SOURCE_OF_TRUTH_CORRECTION_AND_GATE_RESET.docx` | `7766cbab77bbe3725b5e160e99e4f7a7bcf866c3b34f9f0b555e0f843e7cc3f5` |
| 06 | `docs/v2_0_2_1_planning/docx/06_V2_0.2.1_IMPLEMENTATION_MODULE_AND_CHANGE_MAP.docx` | `3fe6b705b8e3772cf56c963bd1a34101796e30622dc285743e94ac999a4a496f` |
| 07 | `docs/v2_0_2_1_planning/docx/07_V2_0.2.1_VERIFICATION_REGRESSION_AND_RELEASE_GATE_PLAN.docx` | `89d6371d5583cf4f9e3ed6a363aca3af265020dc1b3c97b90a8187d89e832bc4` |
| 08 | `docs/v2_0_2_1_planning/docx/08_V2_0.2.1_SOURCE_OF_TRUTH_SYNC_AND_IMPLEMENTATION_AUTHORIZATION.docx` | `59d790b384fef2b2f3b910ee1083fafbd436c127a1e077ec1b67cbe9b4b0eb39` |

Binary DOCX sync commit:
`ef82d55cf6a03e20606b0cddc71f504b4c715e11`

## Authoritative text chain
- `00_SCOPE_AND_GAP_AUDIT.md`
- `01_MATHEMATICAL_PROPERTY_CONTRACT.md`
- `02_BACKEND_FEASIBILITY_RENDER_ARCHITECTURE.md`
- `03_DATA_CONTRACT_ACTIVATION_MIGRATION_PLAN.md`
- `04_UI_EDITING_INTERACTION_CONTRACT.md`
- `05C_UI_SOURCE_OF_TRUTH_CORRECTION_AND_GATE_RESET.md`
- `06_IMPLEMENTATION_MODULE_CHANGE_MAP.md`
- `07_VERIFICATION_REGRESSION_RELEASE_GATE_PLAN.md`
- `08_SOURCE_OF_TRUTH_SYNC_IMPLEMENTATION_AUTHORIZATION.md`

## Superseded artifact
`05_UI_STATE_INVENTORY_IMAGE_PROMPT_PACKAGE.md` is retained only as historical trace and must begin with **SUPERSEDED**.

Its UI-043–UI-052 generation requirement is invalid after STEP 05C.

## Visual/UI source
- `docs/UI_FREEZE.md`
- `resources/ui_reference/final/README.md`
- existing copied Qt presentation code

The repository does not contain UI-001–UI-042 PNG binaries. No regeneration is required; implementation must copy/reuse the existing Qt UI and its established style/component grammar.

## Precedence rules
1. Current user instruction and explicit corrections.
2. STEP 08 readiness index/status.
3. STEP 05C for UI source-of-truth.
4. STEP 07 for verification/release gates.
5. STEP 06 for module/change ownership and K0–K8 sequencing.
6. STEP 03 for schema/activation/save/recovery.
7. STEP 01/02 for math/backend architecture.
8. Earlier statements only where not superseded.

Specific refinements:
- STEP 03 overrides STEP 01 provisional default-advanced wording.
- STEP 04 clarifies manual editing remains allowed for assignments protected from Auto Motion.
- STEP 05C cancels new UI image generation.

## K0 allowed scope
- new `animation/contract.py`;
- schema v3/v4 + marker invariant helpers;
- serializer maximum-readable vs automatic-migration split;
- no automatic v3→v4 migration;
- RenderPlan contract propagation;
- advanced capability-probe scaffolding;
- contract-aware preflight scaffolding;
- K0 tests.

## K0 forbidden scope
- no advanced property rendering yet;
- no K1 opacity implementation;
- no crop/blur/shadow/glow/mask implementation;
- no Bezier production activation beyond scaffolding needed for contract tests;
- no main-window redesign;
- no RC/release publication.

## Implementation gate
Planning source of truth: **PASS**
Copied UI source: **PASS**
Superseded UI-image workflow removed: **PASS**
Binary DOCX synchronization: **PASS**
Text handoff chain: **PASS**
K0 implementation: **AUTHORIZED**
K1–K8: **BLOCKED pending their gates**
