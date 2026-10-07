# STEP 00 — Advanced Animation Scope & Gap Audit

Status: **PASS**

Detailed artifact:
`docx/00_V2_0.2.1_ADVANCED_ANIMATION_SCOPE_AND_GAP_AUDIT.docx`

## Scope lock
- Stable release `v0.2.0` remains immutable.
- v0.2.1 extends the existing scalar `AnimationKeyframeTrack` architecture; there is no animation-engine rewrite.
- Current production keyframes are `position_x`, `position_y`, `scale`, and `rotation_degrees`.
- Advanced properties targeted for staged activation are `opacity`, four crop edges, `blur`, `shadow`, `glow`, and `mask_progress`.
- Advanced interpolation fields targeted for staged activation are `bezier`, `velocity`, and `overshoot`.
- Existing 21 preset effects and the schema-v3 render path are regression baseline.
- FFmpeg remains the final renderer.
- UI is copied/reused from the V2 repository; no redesign is authorized.

## Gap summary
The schema already declares advanced properties/interpolation fields, but v0.2.0 intentionally activates only the four foundational properties with Hold/Linear interpolation. Advanced fields currently fail-soft and therefore require explicit data-contract, backend, preview, validation, testing and release gates before activation.

## Planning rule
No production coding was authorized by STEP 00. Planning must complete and all source-of-truth artifacts must be synchronized before implementation.

## Later refinements
- STEP 03 defines schema v3/v4 activation and overrides any provisional marker-only/default-activation concept.
- STEP 05C cancels the later mistaken UI image-generation requirement and restores copied UI as the visual source.
- STEP 06 owns implementation module mapping.
- STEP 07 owns verification/release gates.
- STEP 08 owns final implementation authorization.
