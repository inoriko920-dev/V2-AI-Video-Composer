# K4 — Shadow + Glow Implementation Result

Status: **PASS**

Validated implementation commit:
`5ef4099deb09cec8853bd360e43d37702ca48417`

## Implemented
- Activated advanced-v1 `shadow` and `glow` scalar tracks with range 0..1.
- Added canonical Shadow mapping:
  - alpha = `0.55 * shadow`
  - offset = `0.012 * min(canvas_width, canvas_height) * shadow`
  - sigma = `0.014 * min(canvas_width, canvas_height) * shadow`
- Added canonical Glow mapping:
  - alpha = `0.65 * glow`
  - sigma = `0.018 * min(canvas_width, canvas_height) * glow`
- Fixed rendering colors for K4:
  - Shadow = black
  - Glow = white
- Final FFmpeg path derives effects from the post-rotation alpha channel:
  - split source
  - alphaextract
  - named gblur with runtime sigma schedule
  - colorize
  - alphamerge
  - runtime alpha gain
  - composite effect layers behind original source
- K4 stage executes after Rotation and before group Opacity.
- Shadow offset is driven by the canonical scalar expression.
- Qt preview provides responsive Approx Shadow/Glow using the same canonical state mapping.
- Real capability probe validates dynamic alpha branch + overlay expressions and promotes:
  - `ALPHA_BRANCH`
  - `OVERLAY_EXPRESSIONS`
- Full render and Selection In/Out fail closed if required K4 FFmpeg capabilities are missing.
- Schema v3 Shadow/Glow tracks remain dormant.
- Bezier/velocity/overshoot remain blocked until K6.
- Mask Progress remains unavailable until K5.

## Important defects caught during K4
1. Ruff exposed an isolated scheduler bug where the Shadow branch still assigned the old `commands` variable and could reuse the Glow command stream. Fixed by giving Shadow its own `sigma_commands` and `alpha_commands`.
2. First real application render failed with FFmpeg `No such filter: ''` because the post-K4 output label was reconnected as an empty filter edge. Fixed by inserting an explicit K4-only `null` continuation stage. Legacy/v3 graph construction remains unchanged.

The locked gates were not weakened.

## Tests / proof
K4 proof covers:
- exact canonical Shadow/Glow mapping;
- Qt Approx state vs canonical evaluator;
- alphaextract/gblur/colorize/alphamerge graph structure;
- stage order Rotation < K4 < Opacity;
- schema-v4 preflight/validation;
- schema-v3 dormant/filtergraph regression;
- K6 Bezier blocking;
- fail-closed capability gate;
- real dynamic alpha-branch capability probe;
- dynamic Shadow/Glow vs static-reference frames;
- transparent-edge pure Shadow/Glow effect-color golden tests;
- real project render;
- Selection In/Out;
- 720p, 1080p, 4K and 60 fps smoke;
- Blur + Shadow + Glow performance <= 8x same-machine baseline.

## Final gate evidence
Validated head: `5ef4099deb09cec8853bd360e43d37702ca48417`

- CI run `37622110062`: **PASS**
  - dependency graph PASS
  - compile PASS
  - Ruff PASS
  - mypy PASS
  - cheap/unit suite PASS
  - frozen STEP09 UI capture/verification PASS
- V2 Automated User Acceptance run `37622110130`: **PASS**
  - real FFmpeg + ffprobe PASS
  - compile/Ruff/strict mypy PASS
  - full technical suite: **722 passed**
  - K4 real-render / transparent-edge / heavy performance gates PASS
  - Windows portable build PASS
  - portable verification PASS
  - packaged EXE launch + real UI capture PASS
  - acceptance evidence upload PASS
- CodeQL run `37622110293`: **PASS**
- Optional Backend Spike run `37622110056`: **PASS**

Draft PR #23 was used only as a CI trigger and was closed without merge.
The validated K4 head was fast-forwarded into `v2/0.2.1-advanced-animation-planning`.

## Scope discipline
K4 did NOT:
- implement Mask Progress;
- activate Bezier/velocity/overshoot;
- add K7 advanced editing UI;
- redesign the copied UI;
- publish RC/final;
- modify `main` or immutable `v0.2.0`.

## Next wave
**K5 — Mask Progress**

K5 is the only next implementation wave eligible to begin.
K6–K8 remain blocked behind their STEP 07 gates.
