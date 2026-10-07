# K1 — Opacity Implementation Result

Status: **PASS**

Validated implementation commit:
`3c3c86e1b31407e4b262aa9dd7ebe56b217c0be9`

## Implemented
- Added advanced-v1 opacity to the canonical scalar keyframe evaluator.
- Opacity range is clamped to `0.0..1.0`.
- K1 supports hold/linear interpolation plus existing linear/ease_in/ease_out/ease_in_out easing.
- Bezier, velocity and overshoot remain blocked until K6.
- Schema v3 opacity tracks remain dormant and do not change the legacy filter graph.
- Schema v4 + `animation_keyframe_contract="advanced-v1"` activates supported opacity tracks.
- Qt preview applies opacity only for advanced-v1 projects and composes it with existing native alpha effects.
- FFmpeg final render uses runtime `sendcmd` + named `colorchannelmixer aa` alpha gain.
- Existing source alpha is multiplied, not replaced.
- Each rendered asset receives an isolated named opacity filter instance.
- Real FFmpeg capability probing promotes `OPACITY_RUNTIME_ALPHA` only after a micro-render succeeds.
- Full render and Selection In/Out exports fail closed with `ADVANCED_BACKEND_UNAVAILABLE` if the local FFmpeg runtime-alpha probe fails.
- Other advanced properties remain unavailable and fail closed.

## K1 proof
Added/updated:
- `tests/unit/test_v2_k1_opacity.py`
- `tests/integration/test_v2_k1_opacity_render.py`
- schema-v4 contract tests
- advanced-capability tests

Real FFmpeg proof covers:
- runtime opacity capability micro-render;
- RGB source alpha behavior;
- RGBA source-alpha preservation;
- canonical evaluator vs rendered alpha parity <= 1/255;
- real advanced-v1 application render;
- Selection In/Out render;
- opacity performance <= 2.5x same-machine baseline using warm-up + three measured runs.

## Gate evidence
Validated head: `3c3c86e1b31407e4b262aa9dd7ebe56b217c0be9`

- CI run `37600126469`: **PASS**
  - dependency graph PASS
  - compile PASS
  - Ruff PASS
  - mypy PASS
  - cheap/unit tests PASS
  - frozen STEP09 UI capture/verification PASS
- V2 Automated User Acceptance run `37600126505`: **PASS**
  - real FFmpeg + ffprobe PASS
  - compile/Ruff/strict mypy PASS
  - full technical suite including K1 real-FFmpeg parity/performance PASS
  - all-21-effects regression PASS
  - Selection In/Out regression PASS
  - Windows portable build PASS
  - portable verification PASS
  - packaged EXE launch + UI capture PASS
  - acceptance evidence upload PASS
- CodeQL run `37600126464`: **PASS**
- Optional Backend Spike run `37600126488`: **PASS**

Draft PR #20 was used only as a CI trigger and was closed without merge.
The validated K1 head was fast-forwarded into `v2/0.2.1-advanced-animation-planning`.

## Scope discipline
K1 did NOT:
- implement crop;
- implement blur/shadow/glow/mask;
- activate Bezier/velocity/overshoot;
- add advanced UI controls;
- redesign the copied UI;
- publish RC/final;
- modify `main` or immutable `v0.2.0`.

## Next wave
**K2 — Crop**

K2 is the only next implementation wave eligible to begin. K3–K8 remain blocked by their STEP 07 gates.
