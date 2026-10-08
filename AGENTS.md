# ACTIVE V2 STEP07 — 0.3.0 RC PREP ONLY (8 OCT 2026 WIB)

W06-A..E technically merged and PASS. User's latest `lanjutkan` permits **non-published** release candidate preparation, version alignment, Windows 11 x64 acceptance, source/portable ZIPs, SHA-256 and handoff. No public v0.3.0 release, no new tag, no `contents:write` workflow permitted. Follow `docs/v2_0_3_0_planning/07_V0_3_0_RC_PREPARATION_AND_RELEASE_GATE.md`, existing release workflows and 3 approved STEP03-R UI PNGs/DOCX. Immutable previous stable `v0.2.2` at `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`. One ProjectSession, schema v3/v4 and `advanced-v1`, 21 native effects, external FFmpeg 9.0.2 and Gemini model preserved. Do not mark RC PASS until final-head CI/CodeQL/backend/Windows/RC artifact and main merge are verified. Public release only with later explicit instruction.

---

# ACTIVE V2 v0.3.0 — W06-E FINAL ACCEPTANCE ONLY (8 OCT 2026 WIB)

The user's latest `lanjutkan` authorizes W06-E cross-wave tests/bug fixes and release-readiness evidence, **NOT a public release**. W06-A/B/C/D already in main. Fix repeated recovery conflict prompt after a successful Restore when on-disk and snapshot bytes match, preserve forensic sidecars; remove worker thread reads of live canonical Qt session. Read `docs/v2_0_3_0_planning/06_W06_E_FINAL_ACCEPTANCE_AND_RELEASE_READINESS_EVIDENCE.md`. Test-first RED `37762298469`; GREEN 10 targeted tests `37762488770`. Keep one ProjectSession, unchanged 42 frozen UI references, three user-approved recovery PNGs, v0.2.2 stable tag and external FFmpeg. W06-E PASS only after final-head CI/CodeQL/backend/Windows acceptance and main merge. Any release or version bump requires another explicit instruction.

---

# CURRENT V2 v0.3.0 — W06-D RECOVERY UI IMPLEMENTATION ONLY (8 OCT 2026 WIB)

Latest user `lanjutkan` authorizes W06-D only, after W06-C PR #59 PASS. Source-of-truth is the top of `V2_0.3.0_PLANNING_STATUS.md` and `docs/v2_0_3_0_planning/06_W06_D_QT_AUTOSAVE_UI_IMPLEMENTATION_EVIDENCE.md`, plus the already approved STEP03-R three PNGs/one DOCX. Preserve all 42 original Qt screens. New UI limited to DLG-01 verified, DLG-02 uncertain/second confirmation in same component, and DLG-03 invalid native QMessageBox; no new screens or redesign. Bind W06-A scheduler / W06-B persistence / W06-C transactions using existing Qt status bar and one worker. Guard Save/Discard/Cancel before any recovery probe. No provider, FFmpeg, render engine, schema, release, version, original repo or stable v0.2.2 tag change. W06-D PASS requires PR-head CI/CodeQL/backend/Windows and main merge; W06-E only on **separate later `lanjutkan`**.

---

# ACTIVE V2 v0.3.0 — STEP06 W06-C SOL ONLY (8 OCT 2026 WIB)

Previous W06-A/B fully merged. User's latest `lanjutkan` authorizes W06-C transactions (Save/Save As/Open preflight/Restore/Discard), one shared process lease with W06-B, SHA-256 baseline comparisons, epoch fences, non-clobber backups, rollback/partial-commit evidence and test-first verification. Read `V2_0.3.0_PLANNING_STATUS.md` current top and `docs/v2_0_3_0_planning/06_W06_C_RECOVERY_TRANSACTIONS_IMPLEMENTATION_EVIDENCE.md`. No Qt, dialog designs, QTimer, AI/FFmpeg/animation changes or version/release. W06-C is PASS only after final-head CI/CodeQL/Windows/backend and main merge. W06-D Qt wiring requires a **new subsequent user instruction**. v0.2.2 tag, legacy repo and 3 approved UI recovery PNGs are immutable.

---

# ACTIVE V2 v0.3.0 — STEP06 W06-B ONLY (8 OCT 2026 WIB)

Authorized scope: new provenance sidecar / strict disk and snapshot SHA-256 inspection, safe checked quarantine staging, isolated failure-injection tests and wave evidence; reuse RecoveryManager and canonical serializer. W06-A completed via #57. W06-B green only after PR CI/CodeQL/Windows/backend and merge. No production Qt integration, no Save/Restore/Discard session transaction, no new UI, no v0.3.0 release, no schema/version/provider/FFmpeg changes. Old 42 UI screens and 3 approved recovery dialogs frozen. **W06-C requires next separate `lanjutkan`** after W06-B PASS. Original legacy repo and v0.2.2 tag immutable.

---

# ACTIVE V2 v0.3.0 — STEP06 W06-A SOL IMPLEMENTATION ONLY (8 OCT 2026 WIB)

W06-A is explicitly authorized after STEP05 PR #56 merged and verified. Read `V2_0.3.0_PLANNING_STATUS.md` top and `docs/v2_0_3_0_planning/06_W06_A_COORDINATOR_IMPLEMENTATION_EVIDENCE.md`, STEP05 plan, STEP04 tests and STEP01/02 architecture. Scope is ONLY pure monotonic autosave coordinator, semantic-revision and epoch fences with deterministic tests; no file IO, Qt, sidecars, Save/Restore integration, runtime version/release, or UI changes. W06-A PASS only after final-head checks and merged PR. W06-B requires separate new user turn. Legacy original repo and v0.2.2 stable are immutable; 3 approved recovery-dialog assets and 42 frozen UI remain unchanged.

---

# CURRENT V2 v0.3.0 — STEP05 DOCUMENTATION-ONLY OVERRIDE (8 OCT 2026)

Source-of-truth: `V2_0.3.0_PLANNING_STATUS.md` latest top section, `docs/v2_0_3_0_planning/05_IMPLEMENTATION_READINESS_AND_SOL_WAVE_AUTHORIZATION_PLAN.md`, STEP04 testing plan, STEP01/02 safety contracts, and the approved three-dialog STEP03-R visuals/Word. STEP03-R PR #54 and STEP04 PR #55 are merged; the original 13-image mandate is archived. The user authorized **STEP05 planning only**; no Qt/Python production changes, runtime tests, dependencies, release/version bumps, or new GitHub workflow permanent changes in STEP05. Stable v0.2.2 tag and legacy original repo immutable. After STEP05 DoR PASS, a separate new user turn is required before any W06-A code. SOL waves W06-A..E are sequential test-first, one wave per turn, each wave independently proven green/merged.

---

# CURRENT 2026-10-08 v0.3.0 STEP04 OVERRIDE — PLANNING ONLY

STEP03-R visual gate is **PASS** (PR #54 merged): only three approved recovery dialogs and a single final image-filled UI DOCX; original 42 main UI screens frozen. Current user instruction allows **STEP04 deterministic testing/failure-injection/Windows planning** ONLY. Read `V2_0.3.0_PLANNING_STATUS.md`, then `docs/v2_0_3_0_planning/04_RECOVERY_FAILURE_INJECTION_WINDOWS_TEST_PLAN.md`, STEP01/02 specs, final approved UI DOCX. A 13-image demand is archival/superseded. Do not implement production tests, coordinator, Qt UI, serializer, release or metadata in STEP04. STEP05 requires next separate user request after STEP04 document/PR PASS; STEP06 coding prohibited until authorized readiness gate. v0.2.2 stable tag/source and legacy repository are immutable.

---

# Current v0.3.0 recovery planning override (2026-10-08 WIB)

**Do not interpret prior v0.2.2 STEP13 coding PASS as permission to code v0.3.0.**
For v0.3.0 GAP-03A, STEP00/01/02 planning is PASS. STEP03 original 13-image prompt requirement was explicitly reduced with user approval to **THREE recovery-dialog image references** only; **preserve existing main UI 1:1**. Read latest `V2_0.3.0_PLANNING_STATUS.md`, then `docs/v2_0_3_0_planning/03_STEP03_DIALOG_ONLY_UI_SCOPE_REVISION.md` and its DOCX; the original 13 UI prompts are historical superseded source. **HARD STOP until three images are reviewed/approved and a single final image-embedded UI reference DOCX is committed.** Do not start STEP04 or SOL implementation from a generic `lanjutkan`. Qt/status bar and existing unsaved guard must be reused rather than making thirteen new windows.

The original application repository and published v0.2.2 tag/assets are immutable for this cycle.

---
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
