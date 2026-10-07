# K2 — Crop Implementation Result

Status: **PASS**

Validated implementation commit:
`3ba23aa4838d30d9db3997968a3538b9d6c49b12`

## Implemented
- Added advanced-v1 crop tracks:
  - `crop_left`
  - `crop_top`
  - `crop_right`
  - `crop_bottom`
- Each crop side is canonically clamped to `0.0..0.45`.
- Canonical crop visibility keeps a fixed asset canvas and at least 10% visible width/height.
- Hold/linear plus existing easing modes are active for K2 crop.
- Bezier/velocity/overshoot remain blocked until K6.
- Schema v3 crop tracks remain dormant and preserve the legacy filter graph.
- Qt preview uses the same crop visibility math and clips a same-size transparent pixmap; anchor/layout do not move.
- Final FFmpeg stage order is crop before dynamic scale and rotation.
- Crop outside pixels are replaced with transparent black while visible source pixels keep their existing alpha.
- Runtime crop is implemented with named `drawbox` filters controlled by `sendcmd [expr]`.
- Pixel edges use `ceil()` so FFmpeg edge rounding matches the canonical discrete-pixel contract.
- Full render and Selection In/Out require the real dynamic-spatial-alpha capability proof.
- Validation/preflight expose `ADVANCED_VALUE_CLAMPED` and `ADVANCED_CROP_NORMALIZED` warnings where applicable.
- Other not-yet-implemented advanced properties remain fail-closed.

## Backend decision and performance gate
The first K2 backend used alpha-plane `geq`. Correctness passed, but Windows measured about 10.29x baseline, so that backend was rejected by the locked <=2.5x gate.

K2 was reworked to runtime transparent edge `drawbox` filters. This keeps the fixed canvas while touching only cropped edge regions. The final Windows performance test passes the unchanged <=2.5x budget.

A second iteration found sub-pixel drawbox dimensions could become integer zero, which FFmpeg interprets as full-frame width/height. K2 now applies `ceil()` to runtime pixel edges. The canonical RGB/RGBA edge-parity test then passes without weakening its <=1 px edge tolerance.

## K2 proof
Added/updated:
- `src/aavc/animation/crop.py`
- K2 scalar activation in `animation/keyframes.py`
- Qt preview crop path
- runtime drawbox compiler in `rendering/advanced_filters.py`
- K2 capability micro-probe
- shared export capability gate
- validation/preflight crop warnings
- `tests/unit/test_v2_k2_crop.py`
- `tests/integration/test_v2_k2_crop_render.py`
- schema/capability regression tests

Real FFmpeg proof covers:
- runtime drawbox/sendcmd spatial-alpha capability;
- RGB and RGBA source-alpha preservation;
- crop edge parity <=1 px;
- fixed-canvas behavior;
- crop-before-scale/rotation ordering;
- full advanced-v1 render;
- Selection In/Out render;
- 1280x720, 1920x1080 and 3840x2160 correctness smoke;
- 60 fps smoke;
- crop performance <=2.5x same-machine baseline;
- legacy all-21-effects and Selection regression through the full acceptance suite.

## Gate evidence
Validated head: `3ba23aa4838d30d9db3997968a3538b9d6c49b12`

- CI run `37603958833`: **PASS**
  - dependency graph PASS
  - compile PASS
  - Ruff PASS
  - mypy PASS
  - cheap/unit tests PASS
  - frozen STEP09 UI capture/verification PASS
- V2 Automated User Acceptance run `37603958820`: **PASS**
  - real FFmpeg + ffprobe PASS
  - compile/Ruff/strict mypy PASS
  - full technical suite including K2 parity/performance PASS
  - all-21-effects regression PASS
  - Selection In/Out regression PASS
  - Windows portable build PASS
  - portable verification PASS
  - packaged EXE launch + UI capture PASS
  - acceptance evidence upload PASS
- CodeQL run `37603958862`: **PASS**
- Optional Backend Spike run `37603958861`: **PASS**

Draft PR #21 was used only as a CI trigger and was closed without merge.
The validated K2 head was fast-forwarded into `v2/0.2.1-advanced-animation-planning`.

## Scope discipline
K2 did NOT:
- implement Blur;
- implement Shadow/Glow;
- implement Mask Progress;
- activate Bezier/velocity/overshoot;
- add advanced UI controls;
- redesign the copied UI;
- publish RC/final;
- modify `main` or immutable `v0.2.0`.

## Next wave
**K3 — Blur**

K3 has a hard STOP gate: do not promote Blur unless Windows real-FFmpeg testing proves frame-accurate named `gblur` runtime sigma control through `sendcmd`.
