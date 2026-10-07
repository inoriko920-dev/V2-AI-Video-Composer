# K5 — Mask Progress Implementation Result

Status: **PASS**

Validated implementation commit:
`365485b6cc4fb3cb380ee7a3e87039b942097101`

## Implemented
- Activated advanced-v1 `mask_progress` with normalized range `0.0..1.0`.
- Semantics are a hard-edge left-to-right reveal:
  - 0.0 = fully hidden;
  - 1.0 = fully visible.
- Schema v3 Mask Progress tracks remain dormant and do not change the legacy graph.
- Schema v4 + `animation_keyframe_contract="advanced-v1"` activates supported Mask tracks.
- Hold/linear plus the existing easing modes remain supported.
- Bezier/velocity/overshoot remain blocked until K6.
- Canonical reveal boundary uses `ceil(width * progress)`.
- FFmpeg final render uses the already-proven fixed-canvas spatial-alpha path:
  - `format=rgba`;
  - named transparent `drawbox`;
  - runtime `sendcmd` updates the reveal boundary;
  - source RGB/alpha inside the visible region remains untouched.
- Locked advanced stage order is preserved:
  Rotation -> Mask Progress -> Shadow/Glow -> Opacity.
- Qt preview clips the existing pixmap left-to-right using the same canonical scalar evaluator.
- Full render and Selection In/Out fail closed unless the local FFmpeg proves `DYNAMIC_SPATIAL_ALPHA`.

## K5 proof
Added/updated:
- K5 scalar activation in `animation/keyframes.py`;
- K5 render compiler in `rendering/advanced_filters.py`;
- K5 stage integration in `rendering/ffmpeg_builder.py`;
- export capability requirement;
- validation/preflight activation;
- Qt preview Mask clipping;
- `tests/unit/test_v2_k5_mask_progress.py`;
- `tests/integration/test_v2_k5_mask_progress_render.py`;
- schema-v4 K6 fail-closed regression test.

Real FFmpeg proof covers:
- RGB source alpha behavior;
- RGBA source-alpha preservation;
- per-frame hard-edge parity using `ceil(width * progress)` with <=1 px edge tolerance;
- Mask + Shadow composition;
- real advanced-v1 application render;
- Selection In/Out render;
- 1280x720, 1920x1080 and 3840x2160 smoke;
- 60 fps smoke;
- Mask performance <=2.5x same-machine baseline;
- v3 dormant/filtergraph regression;
- full legacy all-21-effects and Selection regression through the acceptance suite.

## Gate evidence
Validated head:
`365485b6cc4fb3cb380ee7a3e87039b942097101`

- CI run `37623857325`: **PASS**
  - dependency graph PASS
  - compile PASS
  - Ruff PASS
  - mypy PASS
  - cheap/unit tests PASS
  - frozen STEP09 UI capture/verification PASS
- V2 Automated User Acceptance run `37623857303`: **PASS after infrastructure-only rerun**
  - initial attempt failed before code execution because Chocolatey returned HTTP 504 while fetching FFmpeg 9.0.2;
  - no code or gate was weakened for that external failure;
  - failed job was rerun unchanged;
  - real FFmpeg + ffprobe PASS;
  - compile/Ruff/strict mypy PASS;
  - full technical suite: **738 passed**;
  - K5 real-render/parity/performance gates PASS;
  - Mask + Shadow combination PASS;
  - Windows portable build PASS;
  - portable verification PASS;
  - packaged EXE launch + real UI capture PASS;
  - acceptance evidence upload PASS.
- CodeQL run `37623857264`: **PASS**
- Optional Backend Spike run `37623857212`: **PASS**

Draft PR #24 was used only as a CI trigger and was closed without merge.
The validated K5 head was fast-forwarded into `v2/0.2.1-advanced-animation-planning`.

## Scope discipline
K5 did NOT:
- activate Bezier / velocity / overshoot;
- implement the K7 advanced editing UI;
- redesign the copied UI;
- publish RC/final;
- modify `main` or immutable `v0.2.0`.

## Next wave
**K6 — Bezier / Velocity / Overshoot**

K6 is the only next implementation wave eligible to begin. K7–K8 remain blocked behind their STEP 07 gates.
