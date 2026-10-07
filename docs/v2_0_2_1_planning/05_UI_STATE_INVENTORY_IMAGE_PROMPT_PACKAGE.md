# STEP 05 — UI State Inventory & Image-Prompt Package

Status: **PASS / UI_REFERENCE_WAIT HARD STOP**

Detailed artifact:
`05_V2_0.2.1_UI_STATE_INVENTORY_AND_IMAGE_PROMPT_PACKAGE.docx`

Prompt package:
`V2_0.2.1_STEP05_UI_PROMPTS_UI-043_UI-052.zip`

## HARD STOP
STEP 05 completes the actual UI image prompt package.

After this point:
- DO NOT start STEP 06;
- DO NOT code;
- DO NOT modify schema/backend/runtime/UI implementation;
- DO NOT run advanced backend prototypes;
- DO NOT move planning forward merely because the user says "lanjutkan".

The only valid continuation is:
1. user generates UI-043 through UI-052;
2. user uploads all generated images;
3. assistant reviews every image against STEP 04/05;
4. failed states are regenerated/revised until all PASS;
5. assistant compiles all approved images into one final v0.2.1 UI-reference DOCX;
6. only after that reference DOCX exists may the UI stop-gate be unlocked.

## Base visual contract
All new references:
- 1920x1080 full desktop screenshot;
- existing professional white/blue V2 editor remains unchanged behind modal/dialog states;
- Indonesian UI;
- real desktop Qt-style widgets;
- compact mature typography;
- no permanent new main-window panel;
- no dark mode, glassmorphism, browser/mobile framing, people, stock imagery, decorative concept art or invented controls.

## Required provisional reference IDs
### UI-043 — Animasi Aset / Preset / Legacy v3
Expanded canonical Asset Animation modal. Preset tab active. Asset A005, Rise -> Drift, intensity 1.00, Legacy v3 badge. Preserves beginner v0.2.0 workflow.

### UI-044 — Keyframe / foundational Position X / Live
Legacy v3 remains active. Keyframe tab with Transform group, Position X selected, three keyframes, Linear + Ease Out, Live Qt preview. No advanced activation.

### UI-045 — Advanced Opacity pending activation
Legacy v3. Local dirty opacity keyframe edit with ADV indicator and amber message that Apply requires Advanced Animation. Merely opening/editing locally does not promote.

### UI-046 — Advanced activation confirmation / standard
Confirmation dialog "Aktifkan Advanced Animation?" explains schema v4, v0.2.0 incompatibility after save, first .pre-schema-v4.bak backup, buttons Batal and Aktifkan & Terapkan.

### UI-047 — Activation confirmation / dormant acknowledgement
Same confirmation but shows project-wide dormant track summary and required acknowledgement checkbox. Primary action disabled until acknowledged.

### UI-048 — Advanced v4 Bezier / velocity / overshoot
Advanced v4 badge. Scale track selected. Bezier + Ease In-Out, velocity 1.60, overshoot 25%, expert helper text, Live preview.

### UI-049 — Crop normalization warning
Advanced v4 crop editor. Left/Top/Right/Bottom shown together. Unsafe horizontal raw values produce normalized visible width 10% and amber warning while fixed canvas coordinates remain stable.

### UI-050 — Heavy Blur / Approx -> Verifying
Advanced v4 Blur. Qt interaction badge "≈ Approx" plus FFmpeg truth-preview job state "... Verifying". Exact-preview button disabled while job runs.

### UI-051 — Heavy Blur / Exact / backend ready
Successful heavy truth-preview state. "✓ Exact", current revision verified, "Backend Advanced: Siap", no current Blur error.

### UI-052 — Validation Center / advanced issues
Existing Validation Center, Render tab, 1 error + 3 warnings:
- ADVANCED_BACKEND_UNAVAILABLE;
- ADVANCED_TRACK_DORMANT;
- ADVANCED_CROP_NORMALIZED;
- ADVANCED_PARAMETER_MISMATCH.
All route to existing Buka Scene action where applicable. No new Validation category.

## Acceptance requirements
Every image must:
- use the correct UI ID/state;
- preserve frozen main-window composition;
- use the correct modal/dialog hierarchy;
- show all required Indonesian labels legibly;
- contain no invented control/feature;
- preserve the professional white/blue V2 language;
- use amber/red states appropriately;
- agree with STEP 01–04 contracts.

## Filenames expected from user
- UI-043.png
- UI-044.png
- UI-045.png
- UI-046.png
- UI-047.png
- UI-048.png
- UI-049.png
- UI-050.png
- UI-051.png
- UI-052.png

## Gate
- UI state inventory: **PASS**
- actual image prompt package: **PASS**
- TXT/ZIP prompt package: **PASS**
- generated UI images: **PENDING USER**
- image review/revision: **BLOCKED**
- final UI-reference DOCX: **BLOCKED**
- STEP 06 / coding: **HARD BLOCKED**
