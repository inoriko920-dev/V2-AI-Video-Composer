# STEP 04 — UI / Editing Interaction Contract

Status: **PASS**

Detailed planning artifact:
`04_V2_0.2.1_UI_AND_EDITING_INTERACTION_CONTRACT.docx`.

## Frozen UI decision
Do not redesign the main application.

Advanced animation/keyframe editing extends the existing canonical `Animasi Aset…` modal.
The main window, toolbar, Scene list, preview canvas, status bar, Validation Center and
42 frozen UI references remain structurally unchanged.

The Asset Animation dialog becomes a tabbed modal:
- **Preset** — default / beginner path;
- **Keyframe** — advanced/foundational track editing.

Approximate working size: 980x720, centered and modal.

## Top context strip
- asset selector;
- project state badge: Legacy v3 / Advanced v4;
- existing Auto/AI protection lock;
- local-dialog dirty indicator.

Changing asset with local unsaved editor changes requires:
Terapkan / Buang Perubahan / Batal.

## Preset tab
Preserve the existing v0.2.0 workflow:
- enter effect;
- exit effect;
- intensity 0..2;
- Kunci dari Auto Motion.

Critical implementation correction:
Preset editing must preserve existing `keyframe_tracks`.
The current fresh-assignment helper may not be used in a way that discards tracks.

Preset editing by itself never activates advanced-v1.

## Keyframe tab layout
Three-column modal layout:
1. Left — property navigator (~22%).
2. Center — keyframe/segment editor (~45%).
3. Right — property values + preview truth status (~33%).

No permanent advanced-keyframe dock is added to the main window.

### Property groups
Transform:
- Position X
- Position Y
- Scale
- Rotation

Visibility & Framing:
- Opacity
- Crop Left
- Crop Top
- Crop Right
- Crop Bottom
- Reveal / Mask Progress

Effects:
- Blur
- Shadow
- Glow

### Track markers
- no track: hollow dot;
- foundational active: blue dot;
- advanced active: blue dot + ADV;
- dormant v3 advanced: amber + Dormant;
- validation warning: amber triangle;
- blocking error/backend unavailable: red exclamation.

## Mini keyframe editor
- normalized 0..100% Scene-time ruler;
- selected keyframe diamond;
- Add / Delete keyframe;
- Previous / Next keyframe;
- time editor 0.000..1.000 + human Scene-time label;
- property-specific value editor;
- Hold / Linear / Bezier;
- Linear / Ease In / Ease Out / Ease In-Out;
- velocity 0..4 for Bezier;
- overshoot 0..50% for Bezier;
- Reset Track removes one property track only.

Interpolation/easing/overshoot belong to the selected keyframe's outgoing segment.
Velocity on the segment start is outgoing tangent; next keyframe velocity is incoming tangent.
UI must label this as **Segmen ke keyframe berikutnya**.

Last keyframe has no outgoing segment controls.
Velocity/overshoot are disabled for Hold/Linear.

## Property display ranges
- Position X/Y: -10%..+10%;
- Scale: 0.75x..1.50x;
- Rotation: -30..+30 degrees;
- Opacity: 0..100%;
- Crop each edge: 0..45%;
- Mask progress: 0..100%;
- Blur/Shadow/Glow: 0..100%.

Crop editor shows:
`Visible: W xx% · H yy%`.
Unsafe >90% joint crop shows STEP 01 normalization warning.

## Advanced-v1 activation UX
Merely opening Keyframe or selecting an advanced property does not promote.

Activation is requested only when Apply would commit:
- an advanced property track; or
- Bezier/velocity/overshoot semantics.

Activation dialog:
- title: `Aktifkan Advanced Animation?`;
- explain schema v4 / advanced-v1;
- explain v0.2.0 cannot open the saved advanced project;
- explain first v3 overwrite backup `.pre-schema-v4.bak`;
- summarize project-wide dormant advanced tracks that would become active;
- if unrelated dormant tracks exist, require acknowledgement checkbox;
- Cancel => zero mutation;
- `Aktifkan & Terapkan` => one atomic promotion + edit transaction.

No repeated prompt once already advanced-v1.

## Preview truth states
Lightweight properties:
- Position / Scale / Rotation / Opacity / Crop / Mask => **Live** Qt preview.

Heavy properties:
- Blur / Shadow / Glow during interaction => **Approx**;
- asynchronous FFmpeg truth-preview => **Exact**.

Status states:
- ✓ Exact;
- ● Live;
- ≈ Approx;
- … Verifying;
- ! Exact preview unavailable.

Heavy truth-preview debounces around 250 ms, is cancellable/revision-safe,
and stale job results never overwrite the latest state.
A `Verifikasi Preview` action may request immediate exact heavy preview.

The existing main preview controls remain canonical; no second playback engine.

## Lock semantics clarification
Existing `Kunci dari Auto Motion` protects against Auto/AI replacement.
It is **not** a blanket prohibition on the user's direct manual editing.

- Manual preset edit: allowed.
- Manual keyframe edit: allowed.
- Auto Motion / Gemini Auto: preserve locked assignment.
- Copy Scene Animations onto locked target: reject atomically.
- Manual assignment removal: allowed only after explicit destructive confirmation.
- Lock state may be changed manually in the same Apply transaction.

## Validation Center mapping
Render category + `Buka Scene`:
- ADVANCED_TRACK_DORMANT
- ADVANCED_VALUE_CLAMPED
- ADVANCED_CROP_NORMALIZED
- ADVANCED_PARAMETER_MISMATCH
- ADVANCED_BACKEND_UNAVAILABLE

Project category:
- ADVANCED_CONTRACT_* load errors;
- SCHEMA_DOWNGRADE_BLOCKED save error / Save As guidance.

Asset Animation dialog shows only the most relevant current-asset issue inline and links
to Validation Center when multiple issues exist.

## Dialog state model
- opened / clean;
- local dirty;
- activation required;
- validation blocked;
- applying;
- applied;
- cancelled.

Dialog-local edits use a working copy.
No ProjectState mutation occurs until Apply succeeds.

Switching tabs never discards local edits.
Closing/switching asset with local changes requires explicit discard/apply handling.

## Accessibility / beginner safeguards
- Preset remains the default tab.
- Explicit visible labels for all controls.
- Icons/colors are never the only warning/error signal.
- Tooltips explain Bezier, velocity, overshoot and exact preview in Bahasa Indonesia.
- Delete affects selected keyframe only when keyframe editor has focus.
- Esc closes confirmation first; Enter applies only when safe.
- No global destructive shortcut.

## No-redesign constraints
- no permanent keyframe dock/panel;
- no main-toolbar count change;
- no Scene-list width change;
- no second preview/playback engine;
- no per-property top-level menu tree;
- no static PNG UI shipping;
- no change to global white/blue visual language;
- no change to the 42 frozen main states except later evidence for the new modal.

## STEP 04 implementation test contract
Implementation must prove:
- Preset remains default and 21 preset effects do not regress.
- Preset Apply preserves keyframe tracks.
- Keyframe tab represents v3 dormant and v4 active state correctly.
- Foundational edits do not activate advanced-v1.
- Advanced Apply on v3 requires confirmation and promotes only after confirmation.
- Opening Keyframe tab alone never promotes.
- Dormant project-wide activation acknowledgement works.
- Cancel creates no history/dirty/schema mutation.
- Bezier controls appear only when meaningful.
- Crop warning matches STEP 01.
- Heavy preview transitions Approx -> Verifying -> Exact.
- Stale heavy jobs never win.
- Backend-unavailable state routes to validation and blocks export when required.
- Auto/AI lock remains manual-editable but automation-protected.
- Undo restores exact pre-edit state.
- Frozen main-window screenshot states do not regress.

## STEP 04 gate
- Main-window redesign avoided: **PASS**
- Canonical animation editor chosen: **PASS**
- Preset backward-compatible flow: **PASS**
- Property grouping: **PASS**
- Keyframe / Bezier interaction: **PASS**
- Activation acknowledgement UX: **PASS**
- Preview truth states: **PASS**
- Lock semantics: **PASS**
- Validation mapping: **PASS**
- Accessibility / local edit behavior: **PASS**
- UI image-prompt generation started: **NO**
- Production coding authorized: **NO — BLOCKED**

## Next exact action
**STEP 05 — UI State Inventory & Image-Prompt Preparation**

STEP 05 must enumerate all new visual-reference states, freeze exact content/state for
each screenshot, and prepare the UI image-prompt package.

**UI STOP-GATE:** when the actual UI-image prompt package is completed, stop completely.
Do not continue to later planning/coding merely because the user says “lanjutkan”.
Work resumes only after all UI reference images are generated, reviewed/revised, and
compiled into one UI-reference DOCX.

**CODING GATE: BLOCKED**
