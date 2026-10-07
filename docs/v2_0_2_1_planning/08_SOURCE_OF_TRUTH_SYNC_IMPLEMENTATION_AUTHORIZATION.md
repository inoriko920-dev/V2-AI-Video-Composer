# STEP 08 — Planning Source-of-Truth Synchronization & Implementation Authorization

Status: **PASS**

Detailed artifact:
`docx/08_V2_0.2.1_SOURCE_OF_TRUTH_SYNC_AND_IMPLEMENTATION_AUTHORIZATION.docx`

## Synchronization result
Authoritative planning DOCXs 00, 01, 02, 03, 04, 05C, 06, 07 and 08 are synchronized under:
`docs/v2_0_2_1_planning/docx/`

Initial binary synchronization commit:
`ef82d55cf6a03e20606b0cddc71f504b4c715e11`

Final STEP 08 DOCX replacement commit:
`8fd302905bddda8be3b633e0d2d0c0a1e8250fbe`

Final STEP 08 DOCX SHA-256:
`d807af60f5aa46c5796eed7a3282f60ffb45833b9ac38689c48fddad779ee8af`

The obsolete STEP 05 image-prompt DOCX is intentionally excluded from the authoritative DOCX directory.

## Supersession
STEP 05 UI-043–UI-052 image-generation planning is **SUPERSEDED** by STEP 05C.
- no UI-043–UI-052 images are required;
- no image-generation hard stop remains;
- existing copied Qt UI is the implementation source;
- `docs/UI_FREEZE.md` and `resources/ui_reference/final/README.md` remain policy/reference manifests.

The branch does not contain the UI-001–UI-042 PNG binaries. This is not a blocker under the corrected workflow because the user explicitly requires reuse/copy of the existing repository UI implementation rather than regeneration of UI images.

## Cross-step precedence
- STEP 03 overrides STEP 01 on default activation: new v0.2.1 projects remain schema v3 until explicit advanced edit.
- STEP 04 clarifies that the existing Auto Motion lock protects automated/batch overwrite; explicit manual editing remains allowed.
- STEP 05C overrides STEP 04/05 only where they implied new visual design/image-generation requirements.
- STEP 06 owns module/file/change mapping.
- STEP 07 owns verification, performance, STOP and release gates.
- STEP 08 owns synchronization and implementation authorization.

## K0 authorization
**AUTHORIZED after STEP 08 PASS.**

Only K0 may begin next:
- animation contract/schema-marker helpers;
- serializer/readability split for schema v4 without automatic v3→v4 migration;
- RenderPlan resolved contract propagation;
- advanced capability-probe scaffolding;
- contract-aware preflight structure;
- matching schema/capability regression tests.

K1–K8 remain locked behind their own STEP 07 gates.

## Mandatory handoff read order
1. `V2_0.2.1_PLANNING_STATUS.md`
2. `docs/v2_0_2_1_planning/IMPLEMENTATION_READINESS_INDEX.md`
3. STEP 05C correction
4. STEP 06 module/change map
5. STEP 07 verification/release gates
6. STEP 03 data contract
7. STEP 01 and STEP 02 technical contracts
8. copied Qt UI code + `docs/UI_FREEZE.md`

Do not infer requirements from superseded STEP 05.
