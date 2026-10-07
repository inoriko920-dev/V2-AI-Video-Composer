# K3 — Blur Implementation Result

Status: **PASS**

Validated implementation commit:
`e721f69311475b5269d355af6bed0ef8f282ea9c`

## Hard STOP gate
K3 was not promoted until Windows real-FFmpeg proved all of the following:
- named `gblur` filter targeting works;
- runtime `sigma` control through `sendcmd` changes actual output frames;
- runtime vertical `sigmaV` is controlled together with horizontal `sigma`;
- the premultiply → blur → unpremultiply alpha path is accepted by the real backend.

The capability probe uses a static synthetic frame and `framemd5`; multiple distinct frame hashes are required. Syntax acceptance alone is insufficient.

Initial hard-gate proof commit:
`017b8c54bc540ac6245150e1ee16a13d9785d02d`

## Implemented
- Added advanced-v1 `blur` keyframe property with normalized range `0.0..1.0`.
- Added canonical Blur mapping in `src/aavc/animation/blur.py`.
- Sigma mapping:
  `blur * clamp(0.022222 * min(canvas_width, canvas_height), 8, 48)`.
- Legacy schema v3 Blur tracks remain dormant and leave the legacy filter graph unchanged.
- Schema v4 + `animation_keyframe_contract="advanced-v1"` activates supported Blur tracks.
- Hold/linear plus existing easing modes are supported.
- Bezier/velocity/overshoot remain blocked until K6.
- Qt preview exposes responsive Approx Blur using the same canonical sigma mapping.
- Final FFmpeg Blur is authoritative.
- Final renderer order is:
  crop → blur → scale → rotation → later advanced stages → opacity/overlay.
- If Crop and Blur are both active, the crop boundary is re-applied after Blur so cropped edges remain hard.
- Blur uses:
  - `format=rgba`
  - `premultiply=inplace=1`
  - runtime named `gblur`
  - `unpremultiply=inplace=1`
- Runtime sigma schedule is sampled at output-frame timestamps.
- Sigma values are rounded to 0.01 px.
- Adjacent unchanged samples are deduplicated.
- Horizontal `sigma` and vertical `sigmaV` are updated together.
- Full render and Selection In/Out fail closed if the local FFmpeg does not prove:
  - `NAMED_GBLUR`
  - `SENDCMD_RUNTIME_SIGMA`
  - `PREMULTIPLY_ALPHA`.

## Important issues found and fixed during K3
1. The first runtime implementation updated only `sigma`. Windows parity testing exposed that `sigmaV` retained its initial value, producing horizontal-only Blur after the first frame. K3 was corrected so both axes are commanded together.
2. The transparent-edge test originally compared unpremultiplied RGB values directly at very low alpha. FFmpeg 8-bit unpremultiply can introduce rounding in those nearly transparent pixels. The final test measures the visually composited 8-bit result and still enforces a maximum one-channel-level error; the quality gate was not widened.

## K3 proof
Added/updated:
- `src/aavc/animation/blur.py`
- K3 scalar activation in `animation/keyframes.py`
- Qt Approx Blur preview
- runtime Blur compiler in `rendering/advanced_filters.py`
- Blur stage integration in `rendering/ffmpeg_builder.py`
- heavy capability micro-probe
- shared export capability gate
- validation/preflight activation
- `tests/unit/test_v2_k3_blur.py`
- `tests/integration/test_v2_k3_blur_capability.py`
- `tests/integration/test_v2_k3_blur_render.py`
- schema/capability regression tests

Real FFmpeg proof covers:
- named gblur + runtime sigma/sigmaV capability;
- output-frame changes verified through framemd5;
- dynamic runtime Blur against static-reference Blur frame by frame;
- transparent RGBA edge compositing with <=1 8-bit channel-level error;
- crop + blur with hard crop boundary re-applied;
- full advanced-v1 application render;
- Selection In/Out render;
- 1280x720, 1920x1080 and 3840x2160 smoke;
- 60 fps smoke;
- Blur performance <=4x same-machine baseline;
- v3 dormant/filtergraph regression;
- full legacy all-21-effects and Selection regression through the acceptance suite.

## Gate evidence
Validated head:
`e721f69311475b5269d355af6bed0ef8f282ea9c`

- CI run `37617514404`: **PASS**
  - dependency graph PASS
  - compile PASS
  - Ruff PASS
  - strict mypy PASS
  - cheap/unit tests PASS
  - frozen STEP09 UI capture/verification PASS
- V2 Automated User Acceptance run `37617514527`: **PASS**
  - real FFmpeg + ffprobe PASS
  - compile/Ruff/strict mypy PASS
  - full technical suite: **700 passed**
  - K3 frame parity PASS
  - transparent-edge proof PASS
  - Crop + Blur ordering/boundary proof PASS
  - Blur performance <=4x PASS
  - all-21-effects regression PASS
  - Selection In/Out regression PASS
  - Windows portable build PASS
  - portable verification PASS
  - packaged EXE launch + UI capture PASS
  - acceptance evidence upload PASS
- CodeQL run `37617514414`: **PASS**
- Optional Backend Spike run `37617514483`: **PASS**

Draft PR #22 was used only as a CI trigger and was closed without merge.
The validated K3 head was fast-forwarded into `v2/0.2.1-advanced-animation-planning`.

## Scope discipline
K3 did NOT:
- implement Shadow;
- implement Glow;
- implement Mask Progress;
- activate Bezier/velocity/overshoot;
- add the later advanced editing UI wave;
- redesign the copied UI;
- publish RC/final;
- modify `main` or immutable `v0.2.0`.

## Next wave
**K4 — Shadow + Glow**

K4 is the only next implementation wave eligible to begin. It remains blocked until the user explicitly says **“lanjutkan”** and must satisfy the transparent-edge/heavy-performance STOP gates in STEP 07.
