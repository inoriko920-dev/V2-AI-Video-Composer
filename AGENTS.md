# AGENTS.md — V2 AI Video Composer

## Project identity
- Repository: `inoriko920-dev/V2-AI-Video-Composer`.
- Product: Windows desktop video composer; Python 3.12 + PySide6; portable onedir ZIP.
- Legacy repository `inoriko920-dev/AI-Automatic-Video-Composer` is **read-only**. Never create branches, commits, issues, experiments, or fixes there for V2 work.

## Mandatory read order before work
1. `V2_IMPLEMENTATION_STATUS.md`
2. `docs/v2_planning/V2_MASTER_PLANNING_INDEX.docx`
3. `docs/v2_planning/STEP_00...` through the STEP governing the current wave
4. `docs/ARCHITECTURE.md`, `docs/CODE_CONSTITUTION.md`, `docs/PROJECT_STATE.md`, and `docs/UI_FREEZE.md` as inherited baseline references

## Current implementation protocol
- STEP 13 CODING GATE is PASS as of 2026-10-07.
- Implement only the current wave named in `V2_IMPLEMENTATION_STATUS.md`.
- One risky subsystem at a time; keep a green baseline and explicit rollback point.
- Mature media components are evaluated behind adapters/feature boundaries; do not replace the FFmpeg reference path in one large change.
- Do not change frozen UI behavior/reference surfaces without the UI gate required by STEP 13.

## Architecture invariants
- Dependency direction: `presentation -> application -> domain`.
- Infrastructure/adapters implement filesystem, subprocess, provider, credentials, media, and persistence boundaries.
- No direct filesystem/provider/subprocess access from UI/domain.
- No raw secrets in project state, logs, fixtures, or source.
- Preserve versioned project compatibility and recovery behavior unless the active wave explicitly changes it with migration tests.

## Search-before-create
Before adding a module, abstraction, helper, dependency, animation, timeline controller, or service, search the repository for an existing implementation and extend/reuse it when safe.

## Canonical validation
Use the repository scripts/workflows as the source of truth:
- `./scripts/dev.ps1`
- `./scripts/test.ps1`
- `./scripts/package.ps1`
- `./scripts/verify_portable.ps1`
- Windows GitHub Actions CI for compile, Ruff, strict mypy, pytest, and UI screenshot evidence

## Forbidden actions
- Modify the legacy repository.
- Mass refactor unrelated areas.
- Add or promote a dependency without the STEP 13 dependency gate.
- Bypass adapter boundaries with direct FFmpeg/provider/filesystem calls.
- Silently fall back after errors where the baseline contract expects an explicit failure.
- Overwrite another wave's work or remove regression coverage to make CI pass.
- Claim Windows/package success without workflow or artifact evidence.

## Change checklist
Before: identify current wave, acceptance criteria, affected contracts, regression tests, and rollback point.
During: keep commits reviewable; preserve baseline behavior unless the wave explicitly changes it.
After: report diff scope, tests/evidence, gate PASS/FAIL, unresolved risk, rollback commit, and exact next action.

## Review triggers
Request ASTRA-style planning/review before architecture replacement, dependency promotion, project-schema migration, broad UI redesign, render-backend default changes, or release-gate changes.
