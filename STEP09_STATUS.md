# STEP 09 — App Shell / UI Implementation

Status: **PASS**

Implemented:
- Canonical light white/blue design tokens.
- Canonical menu and 48px editor toolbar.
- Resizable editor shell: left Scene/Aset, center preview, right inspector, bottom timeline, and status area.
- Presentation routes for UI-002, UI-003, UI-010, UI-013, UI-014, UI-027, UI-035, UI-041.
- Representative Home, New Project DOCX, editor overview, SINGLE, DOUBLE, Subtitle, Export, and Validation UI.
- Windows CI capture of all 8 representative 1920x1080 Qt states.
- Stable offscreen Windows font handling.
- CI verifies exactly 8 screenshot PNGs and uploads `step09-ui-actual` as build evidence.
- Pure geometry acceptance tests for 1920x1080 and compact desktop.

Acceptance evidence:
- Latest STEP 11 branch CI is green.
- Compile, Ruff, strict mypy, cheap pytest, Qt capture, screenshot verification, and artifact upload pass on the Windows runner.
- Actual screenshots were reviewed against the frozen STEP 04/05 visual direction.
- Home and New Project follow the light white/blue reference hierarchy.
- Editor overview, SINGLE, DOUBLE, Subtitle, Export, and Validation retain the canonical shell and required controls while normalizing collisions and one-off generation artifacts.
- No blocking clipping/overlap was found in the representative 1920x1080 captures.
- Generated reference images are treated as visual/product references, not pixel-perfect static screens; real Qt widgets remain the implementation source of truth.

Gate decision:
- Runtime screenshot gate: PASS.
- Representative visual-parity gate: PASS.
- STEP 09 is formally closed and no longer blocks STEP 10+ progression.

Reference note:
- The active frozen source inventory used by the repository is the STEP 04/05 canonical UI set recorded by the project documents. Representative STEP 09 evidence uses the eight states listed above.
