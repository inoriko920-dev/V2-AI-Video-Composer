# ASTRA Bug Audit Plan — AAVC — 2026-10-06

Source: uploaded `00_ASTRA_BUG_AUDIT_PLAN_AAVC_2026-10-06.docx`.
Baseline audited: `main @ 8feeeb2e6e90489e5edb890ee67f3f59ca3d438c`.

## Scope
Maintenance only. Do not reopen STEP 00–15, redesign UI, change provider, schema product scope, or published v0.1.1.

## Findings
- **AAVC-ASTRA-01 (P1)** — structurally invalid project payload can replace the active session/recovery target before preview fails.
- **AAVC-ASTRA-02 (P1)** — large FFmpeg filter graph can push Windows CreateProcessW command line over 32,767 UTF-16 units.
- **AAVC-ASTRA-03 (P2)** — ASS subtitle path escaping fails for legal paths containing apostrophes.
- **AAVC-ASTRA-04 (P2)** — preview time is tick-count based, so delayed redraws accumulate drift.
- **AAVC-ASTRA-05 (P2)** — Pause currently uses Stop/reset semantics and resets playhead to the start of the scene.

## Required implementation order
1. Persistence boundary validation and transactional open/recovery.
2. FFmpeg graph transport + subtitle path escaping.
3. Monotonic playback clock + real Pause/Resume semantics.
4. Integration gates, Windows build, portable smoke, CI/CodeQL, docs synchronization.

## Guardrails
- Preserve `presentation -> application -> domain`.
- Keep ProjectSession, ProcessRunner and existing rendering owner canonical.
- Keep unique temp staging and atomic output.
- No shell=True.
- Missing media remains relinkable and is not treated as corrupt project JSON.
- Published tag/release v0.1.1 remains frozen.
- Windows-only acceptance claims require Windows evidence.

## Acceptance summary
Each bug must have a regression that fails on the audited behavior and passes after patch. Final closure requires canonical tests plus Windows coverage for command length/path/multimedia/portable behavior.
