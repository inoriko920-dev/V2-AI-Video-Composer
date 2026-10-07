# STEP 00 — V2 0.2.2 Post-Release Audit & Scope

Status: **PASS**

Baseline:
- current planning baseline: `e9ff8540f3cad74035a592f4d4670c136ea64652`
- frozen stable release: `v0.2.1` @ `eb94efebf142ba8203dfc3ae3c5fa861222a0926`
- previous stable: `v0.2.0` @ `c6ad75308d302cd816301a2a7a34ebe7eb4148a7`

## Non-negotiable release protection

- Published `v0.2.1` is immutable and must never be moved, overwritten, or republished.
- Published `v0.2.0`, `v0.1.1`, and `v0.1.0` remain immutable history.
- All v0.2.2 work must branch from current post-release `main`.
- Schema v4 + `animation_keyframe_contract=advanced-v1` remains the production contract.
- No UI redesign, schema-v5 work, or new runtime dependency is authorized during planning.
- Existing copied white/blue Qt UI remains authoritative.

## Audit result

No confirmed release-blocking runtime defect was found.

Evidence:
- v0.2.1 final workflow `37643499394`: PASS;
- final Windows technical suite: 761 PASS;
- main CI `37643499386`: PASS;
- main CodeQL `37643499315`: PASS;
- post-release main CI `37646796063`: PASS;
- no open GitHub issues;
- repository search found no TODO, FIXME, NotImplementedError, pytest.skip, or xfail markers.

v0.2.2 therefore becomes a **maintenance/hardening patch**, not a feature release.

## Findings

### F-00 — No confirmed runtime blocker
Do not invent defects merely to justify a patch. Any application fix must be backed by
a reproducible failure and regression evidence.

### F-01 — Stale pull requests
PR #11 and #17 remain open from older v0.2.0-era work and are based on obsolete main
history. They must be closed/superseded and must not be merged.

### F-02 — Stale dependency update
`dependabot/github_actions/github-actions-fef1ef3f32` is diverged: one commit ahead
but roughly forty commits behind current main. It only updates
`.github/workflows/backup-single-app.yml`. Do not merge it as-is. Any update must be
regenerated/rebased against current main and gated normally.

### F-03 — Visual regression structure
The repository has the canonical STEP09 screenshot pipeline, but `tests/visual` contains
no executable visual tests. This is a coverage-structure gap, not a proven runtime bug.

### F-04 — Advanced editor lifecycle is regression-sensitive
v0.2.1 introduced local working-copy behavior, Apply/Discard/Cancel asset switching,
advanced activation confirmation, dormant-track acknowledgement and atomic schema-v4
history. Add direct Qt/offscreen regression coverage before changing this surface.

### F-05 — Schema-v4 persistence/recovery is regression-sensitive
Promotion, first-overwrite `.pre-schema-v4.bak`, Save/Save As, recovery, no-downgrade,
and future-schema rejection deserve stress coverage.

### F-06 — Historical workflow surface
The repository keeps many historical release workflows for reproducibility. STEP 01
must verify that already-published release workflows are manual/read-only and that no
obsolete publisher can write contents.

## v0.2.2 scope

In scope:
- repository/workflow hygiene;
- workflow permissions and immutable-release protection;
- direct advanced-editor UI lifecycle regression tests;
- schema-v4 persistence/recovery stress tests;
- Windows portable/packaged-EXE regression;
- safe dependency/action refreshes only from current main;
- targeted fixes only when a failure is reproducible.

Out of scope:
- schema v5;
- new animation property families;
- main-window redesign;
- new generated UI reference set;
- new media runtime backend/dependency;
- Gemini provider/credential redesign;
- 21-effect contract rewrite;
- changing any published v0.2.1 asset/tag.

## Planning sequence
1. STEP 00 — Post-release audit and patch scope — **PASS**
2. STEP 01 — Repository hygiene + workflow security plan — **NEXT**
3. STEP 02 — Advanced editor lifecycle regression plan
4. STEP 03 — Schema-v4 persistence/recovery stress plan
5. STEP 04 — Windows packaging/dependency maintenance plan
6. STEP 05 — Implementation authorization + exact module/change map
7. STEP 06 — Targeted implementation waves
8. STEP 07 — v0.2.2 RC + final release gate

Every planning STEP requires a detailed DOCX. Application coding remains blocked until
STEP 05 authorizes exact files/tests.

## Implementation stop rules

- No application-code changes during STEP 00–05 planning except evidence-only work explicitly recorded.
- Do not bump runtime/package version from 0.2.1 until implementation/release authorization.
- Do not alter schema contract in this patch cycle.
- Do not upgrade a dependency merely because a newer release exists.
- Do not merge stale PRs as shortcuts.
- Do not claim a bug fix without reproducible failing-before/passing-after evidence.
- Do not publish v0.2.2 before exact-source Windows gates, checksums, and immutable-tag guard pass.

## UI rule
No UI redesign is planned. The current v0.2.1 copied Qt UI is authoritative. If a later
STEP unexpectedly requires a visual redesign/new reference image, the existing UI prompt
stop-gate immediately reactivates before coding.

## Next exact action
**STEP 01 — Repository Hygiene + Workflow Security Plan**

Do not begin STEP 02 or application implementation in the same turn.


## STEP 00 gate decision
**PASS**

The release baseline is healthy, risks are identified, scope is bounded, and the next
planning action is unambiguous. No application implementation is authorized yet.

## Handoff summary
- Read `V2_0.2.1_FINAL_STATUS.md` and `docs/v2_0_2_1_planning/FINAL_RELEASE_CLOSURE.md` first.
- Treat v0.2.1 as immutable production baseline.
- Start v0.2.2 only from current post-release main.
- STEP 00 contains no application implementation.
- STEP 01 is repository/workflow hygiene planning.
- Do not reopen old Wave J or v0.2.0 PRs as implementation bases.
