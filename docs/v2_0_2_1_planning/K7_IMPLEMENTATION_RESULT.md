# K7 — Copied UI + Transactions Implementation Result

Status: **PASS**

Validated implementation commit:
`188ea587551c0403c0afda2cf6e272606de5fde9`

## Implemented
- Extended the existing copied `Animasi Aset…` modal instead of redesigning the main window.
- Preset remains the default beginner path and now preserves all existing `keyframe_tracks`.
- Added the Keyframe tab in the existing white/blue Qt component grammar.
- Added property navigation for:
  - Position X / Position Y / Scale / Rotation;
  - Opacity / Crop Left / Crop Top / Crop Right / Crop Bottom / Mask Progress;
  - Blur / Shadow / Glow.
- Added normalized Scene-time keyframe editing with Add/Delete/Previous/Next and Reset Track.
- Added Hold / Linear / Bezier, easing, velocity 0..4 and overshoot 0..50% editing.
- Last keyframe disables outgoing-segment controls; velocity/overshoot are enabled only for outgoing Bezier semantics.
- Lightweight properties expose Live preview truth status; Blur/Shadow/Glow remain explicitly Approx during interaction while FFmpeg remains final truth.
- Added working-copy behavior so merely opening/selecting Keyframe controls does not mutate ProjectState.
- Asset switching with local changes requires Apply / Discard / Cancel.
- Manual removal requires explicit destructive confirmation and remains undoable.

## Transaction / schema activation contract
- Added `ApplyAnimationKeyframeEdit` and typed `AdvancedAnimationActivationRequired`.
- Foundational legacy-compatible keyframe edits remain schema v3.
- Preset-only edits remain schema v3 even when dormant advanced tracks already exist.
- A changed advanced property or Bezier/velocity/overshoot edit on v3 requires explicit activation.
- Activation confirmation explains schema v4 / advanced-v1, v0.2.0 compatibility impact and first-overwrite `.pre-schema-v4.bak`.
- Unrelated dormant advanced tracks require explicit acknowledgement before activation.
- Cancel/reject causes zero ProjectState/history mutation.
- Approved activation applies schema v4 + `animation_keyframe_contract=advanced-v1` + the asset edit atomically as one history entry.
- Undo restores the exact pre-edit v3 state.
- Existing advanced-v1 projects do not prompt again.
- Track removal never implicitly promotes or demotes the project.
- Existing manual-edit behavior for Auto/AI locked assignments remains allowed; automation protection is unchanged.

## Tests / regression
Added:
- `tests/unit/test_v2_k7_ui_transactions.py`

Extended:
- `tests/unit/test_native_asset_motion_editor.py`

Coverage includes:
- Preset keyframe preservation.
- Foundational edit staying v3.
- Advanced activation required before mutation.
- Atomic promotion + edit + exact Undo.
- Dormant project-wide acknowledgement.
- Track removal without promotion/demotion.
- Existing v4 no-repeat activation.
- Strict typing of Keyframe interpolation/easing/editor time.

## Gate evidence
Validated head:
`188ea587551c0403c0afda2cf6e272606de5fde9`

- CI run `37636430005`: **PASS**
  - secret scan PASS
  - dependency graph PASS
  - compile PASS
  - Ruff PASS
  - strict mypy PASS
  - cheap suite: **716 passed, 45 deselected**
  - 8 frozen STEP09 UI captures + verification PASS
  - STEP09 UI artifact `11489572164`
  - artifact digest `sha256:0b00d65cb552ae4eb5f2e7e874c8a22233576cc76fea78da36409cbf178d3d55`
- V2 Automated User Acceptance run `37636430226`: **PASS**
  - FFmpeg 9.0.2 real Windows runtime PASS
  - compile / Ruff / strict mypy PASS
  - full technical suite: **761 passed**
  - Windows portable build PASS
  - portable foundation verification PASS
  - packaged EXE launch + real UI capture PASS
  - acceptance artifact `11490500792`
  - artifact digest `sha256:c2aa8508f66f423713ac4945fc947a598445cdbaf1808a8a27b3207f65ed333f`
- CodeQL run `37636429927`: **PASS**
- Optional Backend Spike run `37636430057`: **PASS**

Draft PR #26 was used only as a CI/acceptance trigger against `main` and must be closed without merge.
The validated K7 line is intended to be fast-forwarded into `v2/0.2.1-advanced-animation-planning`.
`main` and immutable `v0.2.0` remain unchanged.

## Scope discipline
K7 did NOT:
- start K8 RC/release work;
- redesign the frozen main window;
- add a runtime dependency;
- alter the v0.2.0 tag/release;
- modify the legacy repository.

## Next wave
**K8 — Windows Acceptance / v0.2.1 RC**

K8 is the only next implementation/release wave eligible after K7 closure.
Per the one-wave-per-turn gate, **K8 must not begin in the same turn that completed K7**.
