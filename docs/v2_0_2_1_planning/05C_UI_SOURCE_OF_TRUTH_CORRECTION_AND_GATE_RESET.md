# STEP 05C — UI Source-of-Truth Correction & Gate Reset

Status: **PASS**

Detailed DOCX:
`05C_V2_0.2.1_UI_SOURCE_OF_TRUTH_CORRECTION_AND_GATE_RESET.docx`

## Reason for correction
The user's original project rule is authoritative: V2 must copy/reuse the UI foundation from the copied repository, not create a new UI design.

Repository evidence confirms:
- `docs/UI_FREEZE.md` defines exactly 42 canonical references: UI-001 through UI-042.
- `resources/ui_reference/final/README.md` confirms UI-001 through UI-042 as the canonical source set.
- Production UI must be real Qt widgets based on those references, not static images.

Therefore the STEP 05 requirement to generate UI-043 through UI-052 was incorrect.

## Corrected UI source of truth
Priority:
1. User instruction: copied repo UI is reused; no redesign.
2. Existing frozen UI references UI-001 through UI-042.
3. Existing Qt presentation code in the copied V2 repo.
4. STEP 00–03 technical contracts.
5. STEP 04 behavior decisions only where they fit the copied visual UI.
6. This STEP 05C correction.

The UI-043–UI-052 image prompt package is superseded and non-authoritative.

## Corrected integration rules
- Do not reconstruct the main window.
- Do not add a new permanent advanced-animation panel.
- Extend existing animation dialogs/widgets/classes with the smallest structural changes.
- Preserve current white/blue visual language, typography, spacing, control density, menus, Scene list, preview canvas and Validation Center.
- Advanced controls use existing Qt component/style grammar.
- Activation advanced-v1 uses a normal existing-style confirmation dialog.
- Validation reuses the existing Validation Center.
- Advanced preview reuses the existing preview canvas/playback path.

## STEP 04 correction
STEP 04 behavior decisions remain useful:
- preserve beginner Preset flow;
- use existing Asset Animation workflow;
- explicit advanced activation;
- truthful Approx/Exact heavy preview state;
- Validation Center routing.

Any implication that v0.2.1 requires a new 980x720 visual design, three-column redesign or new generated screenshots is non-binding. The copied repo UI has priority.

## STEP 05 correction
Cancelled:
- mandatory UI-043–UI-052 images;
- requirement that user generate new UI images;
- image review/revision loop;
- new UI-reference DOCX based on those images;
- UI_REFERENCE_WAIT hard stop.

The previous prompt ZIP may remain as obsolete history but must not be treated as source of truth.

## Revised gate
- Existing UI-001–UI-042 source of truth: **PASS**
- Need new generated UI images: **NO**
- UI_REFERENCE_WAIT: **CANCELLED**
- Planning continuation: **UNLOCKED**
- Production coding: **STILL BLOCKED** until remaining planning and source-of-truth synchronization are complete.

## Next exact action
**STEP 06 — Implementation Module & Change Map**

STEP 06 will map exact files/classes/interfaces/tests for schema v4 activation, persistence, keyframe evaluation/compiler, FFmpeg capability probing, preview integration, copied Asset Animation UI extensions, Validation Center mappings, recovery, Undo/Redo and Windows acceptance.

No new UI image generation is required.
