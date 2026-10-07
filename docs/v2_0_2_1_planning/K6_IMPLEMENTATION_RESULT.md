# K6 — Bezier / Velocity / Overshoot Implementation Result

Status: **PASS**

Validated implementation commit:
`800f2811076efe9ed2867ce2b657071510f000ce`

## Implemented
- Activated advanced-v1 cubic Bezier interpolation without changing the stored scalar keyframe schema.
- Bezier tangent contract follows STEP 01 exactly:
  - `m0 = clamp(velocity0 or 1, 0, 4) * D`
  - `m1 = clamp(velocity1 or 1, 0, 4) * D`
  - `P1 = v0 + m0/3`
  - `P2 = v1 - m1/3`.
- Velocity hard-clamps to `0..4`.
- Overshoot hard-clamps to `0..0.50`.
- Overshoot is applied only on outgoing Bezier segments:
  `B(u_eased) + D * o * sin(pi*u_eased) * u_eased`.
- Overshoot contribution is exactly zero at both segment endpoints.
- Final property clamp is applied after Bezier/overshoot evaluation.
- Start keyframe owns outgoing interpolation/easing/overshoot.
- End keyframe velocity acts as the incoming Bezier tangent.
- Velocity/overshoot attached to non-Bezier segments are not silently reinterpreted; validation emits `ADVANCED_PARAMETER_MISMATCH`.
- Out-of-range velocity/overshoot produces `ADVANCED_VALUE_CLAMPED` warnings while canonical evaluation clamps deterministically.

## Contract isolation
- Schema v3 / legacy semantics remain unchanged.
- Legacy foundational `keyframe_track_support_reason()` still accepts only the old hold/linear behavior.
- Bezier/velocity/overshoot are activated only when the project contract is `advanced-v1`.
- Foundational Position X/Y, Scale and Rotation use Bezier only under advanced-v1.
- Opacity/Crop/Mask runtime command compilers consume the K6 canonical advanced evaluator.
- Blur/Shadow/Glow frame-sampled schedulers consume the same K6 canonical evaluator.
- No linear fallback is used for active advanced-v1 Bezier tracks.

## FFmpeg / preview
- Foundational FFmpeg expressions compile the same cubic Bezier/overshoot math as the Python evaluator.
- Qt preview receives the project contract and uses advanced semantics only for advanced-v1.
- Existing legacy presets remain additive with advanced foundational motion.
- Heavy-effect runtime schedules are generated from canonical evaluator samples, preserving the already-proven K3–K5 backends.

## Tests / proof
Added:
- `tests/unit/test_v2_k6_bezier_velocity_overshoot.py`
- `tests/integration/test_v2_k6_bezier_render.py`

Coverage includes:
- velocity multipliers 0, 1 and 4;
- overshoot 0, 0.25 and 0.50;
- endpoint exactness;
- hard parameter clamps;
- mismatch warnings on non-Bezier segments;
- incoming end-keyframe velocity;
- schema-v3 legacy blocking vs advanced-v1 activation;
- Position/Scale/Rotation preview parity;
- FFmpeg foundational Bezier expressions;
- all advanced property families using Bezier;
- real FFmpeg opacity parity against the canonical evaluator;
- real all-property advanced-v1 render;
- Selection In/Out render;
- v0.2.0 foundational regression through the full acceptance suite.

## Gate evidence
Validated head:
`800f2811076efe9ed2867ce2b657071510f000ce`

- CI run `37628344987`: **PASS**
  - dependency graph PASS
  - compile PASS
  - Ruff PASS
  - mypy PASS
  - unit/cheap suite PASS
  - frozen STEP09 UI capture/verification PASS
- V2 Automated User Acceptance run `37628344855`: **PASS after infrastructure-only rerun**
  - first attempt stopped before code tests because the FFmpeg provisioning step failed;
  - no code, test, or gate was weakened;
  - unchanged failed job was rerun;
  - real FFmpeg + ffprobe PASS;
  - compile/Ruff/strict mypy PASS;
  - full technical suite: **754 passed**;
  - K6 real-FFmpeg Bezier proof PASS;
  - full render + Selection In/Out PASS;
  - Windows portable build PASS;
  - portable verification PASS;
  - packaged EXE launch + UI capture PASS;
  - acceptance evidence upload PASS.
- CodeQL run `37628345269`: **PASS**
- Optional Backend Spike run `37628344862`: **PASS**

Draft PR #25 was used only as a CI trigger and was closed without merge.
The validated K6 head was fast-forwarded into `v2/0.2.1-advanced-animation-planning`.

## Scope discipline
K6 did NOT:
- implement K7 advanced editing UI/transaction activation;
- redesign the copied UI;
- publish RC/final;
- modify `main`;
- alter immutable `v0.2.0`.

## Next wave
**K7 — Copied UI + Transactions**

K7 is the only next implementation wave eligible to begin.
K8 remains blocked behind the STEP 07 release/acceptance gate.
