# K0 — Contract & Capability Scaffolding

Status: **PASS**

Validated implementation commit:
`e399d00af10fdd5540e48262170eff58285cfdf7`

## Implemented
- Added `src/aavc/animation/contract.py`.
- Locked schema v3 legacy vs schema v4 + `animation_keyframe_contract="advanced-v1"`.
- Added advanced-track detection and dormant-track location helpers.
- Serializer now separates automatic migration target v3 from maximum readable schema v4.
- No automatic v3 -> v4 migration.
- `dumps_project()` preserves validated `ProjectState.schema_version`.
- Normal Save blocks v4 -> v3 overwrite with `SCHEMA_DOWNGRADE_BLOCKED`.
- First schema upgrade backup uses target-specific `.pre-schema-vN.bak` and never clobbers an existing backup.
- Recovery autosave may follow Undo across v4/v3 without schema-backup clutter.
- RenderPlan carries resolved project schema + animation contract.
- Added `src/aavc/rendering/advanced_capabilities.py` scaffold.
- K0 capability probe fingerprints the resolved FFmpeg tool but intentionally claims zero advanced render features.
- `FFmpegToolCapabilityService` exposes the advanced probe and invalidates it on refresh.
- Project validation and render preflight are contract-aware:
  - v3 advanced tracks => `ADVANCED_TRACK_DORMANT` WARNING;
  - active v4 advanced tracks without promoted backend => `ADVANCED_BACKEND_UNAVAILABLE` ERROR.
- Validation Center routes advanced issues through the existing UI.

## Tests added
- `tests/unit/test_v2_schema_v4_contract.py`
- `tests/unit/test_v2_advanced_capabilities.py`

Existing Wave E / Wave F expectations were updated only for the intentional dormant-warning code change.

## Gate evidence
Validated head: `e399d00af10fdd5540e48262170eff58285cfdf7`

- CI run `37597905709`: **PASS**
  - dependency check PASS
  - compile PASS
  - Ruff PASS
  - strict mypy PASS
  - cheap/unit tests PASS
  - STEP09 frozen UI capture + verification PASS
- V2 Automated User Acceptance run `37597905722`: **PASS**
  - real FFmpeg + ffprobe PASS
  - compile/Ruff/mypy PASS
  - full technical acceptance PASS
  - all existing real-render acceptance contained in suite PASS
  - Windows portable build PASS
  - portable verification PASS
  - packaged EXE launch + real UI capture PASS
  - acceptance evidence upload PASS
- CodeQL run `37597905712`: **PASS**
- Optional Backend Spike run `37597905759`: **PASS**

Draft PR #19 was used only to trigger PR CI, then closed without merge.
The validated K0 head was fast-forwarded into `v2/0.2.1-advanced-animation-planning`.

## Scope discipline
K0 did NOT:
- activate opacity rendering;
- implement crop/blur/shadow/glow/mask;
- activate Bezier/velocity/overshoot production semantics;
- redesign UI;
- publish RC/release;
- modify `main` or the immutable `v0.2.0` tag/release.

## Next wave
**K1 — Opacity**

K1 remains separate and must satisfy its STEP 07 gate before K2.
