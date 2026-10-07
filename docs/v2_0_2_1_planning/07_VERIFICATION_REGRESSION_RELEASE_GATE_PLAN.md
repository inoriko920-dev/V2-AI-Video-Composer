# STEP 07 — Verification, Regression & Release Gate Plan

Status: **PASS**

Detailed artifact:
`07_V2_0.2.1_VERIFICATION_REGRESSION_AND_RELEASE_GATE_PLAN.docx`

## Core verification model
STEP 07 defines release-blocking verification tiers:
- T0 static/dependency
- T1 deterministic unit
- T2 real FFmpeg micro-proof
- T3 integration acceptance
- T4 portable/packaged
- T5 performance/parity
- T6 release reproducibility

Mandatory results may be PASS, FAIL, STOP, or documented NOT TESTED. No mandatory RC requirement may remain NOT TESTED.

## Schema / persistence / history gates
Release-blocking cases include:
- v1/v2 deterministic migration to v3;
- v3 open/save remains v3 unless explicit advanced edit is committed;
- first advanced edit promotes schema4 + advanced-v1 + track atomically;
- dormant-track acknowledgement has zero mutation before acceptance;
- promotion Undo/Redo restores exact v3/v4 states;
- no automatic demotion;
- first v3->v4 overwrite creates non-clobbering .pre-schema-v4.bak;
- normal v3 overwrite of existing v4 is blocked;
- autosave preserves exact schema without promotion-backup clutter;
- validated recovery may explicitly cross v3/v4;
- future schema and schema/marker mismatches reject before live-session mutation.

## Numerical and preview/render parity
Locked tolerances:
- foundational scalar math <= 1e-9;
- advanced scalar evaluator <= 1e-4;
- position <=1 px at 1080p, <=2 px at 4K;
- scale <=1 px/axis at 1080p;
- rotation <=0.10 degrees;
- opacity <=1/255;
- crop edge <=1 px at 1080p;
- mask edge <=1 px;
- blur sigma <=0.25 px equivalent;
- shadow offset <=1 px;
- shadow/glow alpha <=2/255.

One canonical scalar evaluator is authoritative for unit tests, preview and sampled FFmpeg schedules.

## Real FFmpeg proof
Real micro-render proof is mandatory for:
- opacity;
- stable-canvas crop;
- mask progress;
- commandable blur;
- shadow;
- glow;
- Bezier motion;
- heavy combinations;
- DOUBLE Scene isolation.

Capability proof must cover:
- dynamic spatial alpha;
- named gblur;
- sendcmd runtime sigma;
- alphaextract/alphamerge + premultiply/unpremultiply;
- overlay expressions;
- executable fingerprint/cache invalidation.

K3 Blur is STOP if frame-accurate Windows sendcmd/gblur proof fails.
K4 Shadow/Glow is STOP if transparent-edge artifacts cannot meet tolerance without architecture change.

## Preview gates
- lightweight Qt target >=30 fps at 1280x720 with up to two assets;
- no repeated UI stall >100 ms;
- heavy Qt preview remains Approx only;
- FFmpeg truth preview uses debounce/revision IDs/stale-result discard;
- cancellation acknowledgement target <500 ms;
- exact-preview cache is bounded and invalidated by source/revision/resolution/FFmpeg fingerprint.

## Relative performance budgets
Measure same-machine baseline and advanced cases in one Windows job:
- one warm-up + three measured runs;
- median elapsed-time ratio is authoritative.

Budgets:
- opacity <=2.5x baseline;
- crop <=2.5x;
- mask <=2.5x;
- single blur <=4x;
- blur+shadow+glow <=8x;
- 4K correctness is mandatory first; heavy 4K target remains <=8x;
- 60fps smoke must not change correctness.

Existing 10/100/500 Scene command-build benchmark remains a regression gate.

## Cancellation / atomicity
Success, failure and cancellation must preserve:
- final-output atomicity;
- existing destination on failure;
- workspace cleanup;
- stale schedule isolation;
- Windows non-ASCII path safety.

Advanced sidecars must never enter the portable artifact.

## Full v0.2.0 regression gate
RC is blocked by any regression in:
- all 21 effects real FFmpeg rendering;
- foundational keyframes;
- dormant advanced-looking v3 data;
- SINGLE/DOUBLE layouts;
- Scene fades;
- Selection In/Out;
- subtitles;
- narration;
- Undo/Redo;
- Copy Scene Animations;
- AI/Random lock behavior;
- v3 save/open/recovery;
- portable EXE smoke;
- existing eight STEP09 UI captures.

## Combination matrix
Mandatory combinations include:
- opacity + position;
- crop + rotation;
- crop + blur;
- mask + shadow;
- glow + opacity;
- blur + shadow + glow + opacity;
- Bezier position + scale;
- Bezier + overshoot + clamp;
- advanced asset + legacy second asset;
- advanced + preset effect.

## Windows matrix
Required:
- ASCII paths;
- spaces;
- apostrophe;
- Unicode;
- deep path;
- FFmpeg from PATH;
- app-local tools slot where available;
- missing FFmpeg failure path;
- changed FFmpeg fingerprint/cache invalidation.

Target remains Windows 11 x64; GitHub Actions windows-latest is the reproducible automated gate.

## UI policy
No new user-generated UI reference images are required.
UI-001–UI-042 remain the visual source of truth.
Advanced UI proof is behavioral + actual-app QA evidence only.

## Workflow strategy
- keep `ci.yml` as PR static/unit gate;
- extend `v2-user-acceptance.yml` for advanced real-FFmpeg acceptance;
- create new `v2-0.2.1-rc.yml` for 0.2.1rc1;
- create new `v2-final-0.2.1.yml` for 0.2.1 final;
- do not repurpose historical v0.2.0 workflows.

## RC target
Planned RC version: `0.2.1rc1`.
RC requires T0–T6 PASS, 21-effect + Selection real renders, advanced proof, parity/performance, cancellation/recovery, Windows paths, portable build, packaged EXE launch/capture, no secret/runtime leakage, portable/source ZIP and SHA-256 evidence.

There are no waivers for release-blocking gates.

## Final v0.2.1
Final must repeat all required gates from the final commit, create portable/source backups, verify SHA-256, record build manifest, update user/maintenance/backup docs for schema v4/advanced-v1, and create a new v0.2.1 tag without altering v0.2.0.

## K0–K8 wave gates
Every implementation wave has an explicit promotion gate.
A feature that fails a STOP gate may only be omitted if project/UI/preflight no longer expose it as active. Dormant data must remain preserved. No hidden fallback is allowed.

## STEP 07 gate
- verification tiers: **PASS**
- schema/persistence/history matrix: **PASS**
- numerical/parity matrix: **PASS**
- real FFmpeg proof matrix: **PASS**
- transparent-alpha STOP gates: **PASS**
- preview/cancellation gates: **PASS**
- performance budgets: **PASS**
- v0.2.0 regression gate: **PASS**
- Windows/package gates: **PASS**
- RC/final workflow plan: **PASS**
- K0–K8 promotion gates: **PASS**
- production coding authorized: **NO — BLOCKED**

## Next exact action
**STEP 08 — Planning Source-of-Truth Synchronization & Implementation Authorization Gate**

STEP 08 must synchronize all authoritative planning DOCXs/text handoffs into the repository, clearly mark the superseded STEP 05 image requirement, verify the copied UI reference chain, create one implementation-readiness index, and only then decide whether K0 implementation may begin.
