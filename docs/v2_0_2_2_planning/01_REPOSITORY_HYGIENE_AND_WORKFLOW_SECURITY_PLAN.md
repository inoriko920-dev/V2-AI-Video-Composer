# STEP 01 — V2 0.2.2 Repository Hygiene & Workflow Security Plan

Status: **PASS / PLANNING ONLY**

Audited main: `bbc8135cdddff182e92d376c590914ccc125e3a4`  
Frozen stable release: `v0.2.1` @ `eb94efebf142ba8203dfc3ae3c5fa861222a0926`

## Purpose

STEP 01 audits repository hygiene and GitHub Actions security for the v0.2.2 maintenance line.
No application runtime implementation is authorized in this STEP.

## Non-negotiable constraints

- do not modify application runtime source;
- do not move, overwrite or republish `v0.2.1` or `v0.2.0`;
- do not merge stale PR #11, PR #17 or the stale Dependabot branch;
- do not redesign UI, change schema v4, add a runtime backend, or change Gemini credential behavior;
- do not delete historical branches until unique commits are reviewed and a verified full-history backup exists;
- do not expand workflow permissions merely to simplify automation.

## Audit results

### H-01 — stale pull requests

PR #11 and PR #17 are still open, unmerged and based on obsolete v0.2.0-era history.

Decision:
- close both as superseded;
- do not merge, rebase or reuse their heads.

### H-02 — stale Dependabot branch

`dependabot/github_actions/github-actions-fef1ef3f32` is diverged from current main:
- 1 commit ahead;
- 57 commits behind;
- only `.github/workflows/backup-single-app.yml` differs.

Decision:
- do not merge it as-is;
- regenerate the update from current main after the backup workflow is corrected.

### H-03 — branch accumulation

Wave A–J, v0.2.0, v0.2.1 K-wave, postrelease, DOCX-fix and temporary backup branches remain.

Decision:
- do not mass-delete blindly;
- preserve main and the active v0.2.2 planning line;
- treat old implementation/release/fix branches as deletion candidates only after unique-commit comparison;
- require verified full-history backup before deletion;
- immutable release tags remain authoritative.

## Workflow audit

### Workflows that are already appropriately read-only

- `ci.yml`: push main + pull_request, `contents: read`.
- `backend-spike.yml`: pull request + manual, `contents: read`.
- `v2-user-acceptance.yml`: pull request + manual, `contents: read`.
- `package-windows.yml`: manual, `contents: read`.
- `release-0.1.1.yml`: historical manual verifier, `contents: read`.
- `release-candidate.yml`: historical manual verifier, `contents: read`.
- `release-final.yml`: historical manual verifier, `contents: read`.
- `v2-wave-j-rc.yml`: historical manual verifier, `contents: read`.
- `v2-0.2.1-rc.yml`: historical manual verifier, `contents: read`.
- `v2-final-0.2.0.yml`: manual historical verifier, `contents: read`.
- `v2-final-0.2.1.yml`: manual historical verifier, `contents: read`.

`codeql.yml` uses `contents: read` plus `security-events: write`, which is appropriate for CodeQL result upload.

### W-01 — backup workflow is pointed at the wrong repository

Current `.github/workflows/backup-single-app.yml` still uses:
- `APP_NAME: AI-Automatic-Video-Composer`;
- `REPO_FULL: inoriko920-dev/AI-Automatic-Video-Composer`;
- stable release `v0.1.1`.

This is operationally unsafe inside the V2 repository because it can generate a misleading backup.

Planned correction:
- target V2-AI-Video-Composer;
- prefer repository identity derived from `github.repository`;
- while v0.2.2 is still planning, stable build source remains v0.2.1;
- preserve `contents: read`;
- prefer manual-only trigger after correction;
- require Git Bundle create/verify and source/build checksum verification.

### W-02 — STEP00 DOCX generator retains write-back capability

`.github/workflows/generate-v2-0.2.2-step00-docx.yml`:
- triggers from main path changes;
- has `contents: write`;
- commits generated output;
- pushes directly to main.

Its one-time STEP00 purpose is already complete.

Planned correction:
- retire automatic write-back;
- convert to manual/read-only artifact generation or remove;
- no direct `git push` to main.

### W-03 — legacy V2 planning generator is write-capable and not SHA-pinned

`.github/workflows/generate-v2-planning-docx.yml`:
- has `contents: write`;
- can push directly;
- uses `actions/checkout@v4`;
- uses `actions/setup-python@v5`.

Planned correction:
- manual/read-only artifact generation or retirement;
- remove direct push;
- pin actions to reviewed commit SHAs if retained.

### W-04 — historical v0.2.0 / v0.2.1 publication workflows are already retired correctly

The current v2 final workflows are:
- `workflow_dispatch` only;
- `contents: read`;
- verification-only.

Do not re-add publisher jobs or `contents: write`.
A future v0.2.2 publisher must be a newly planned workflow.

### W-05 — current CI secret posture

Audit found:
- no `pull_request_target` workflow;
- no GitHub Actions expression using `${{ secrets.NAME }}`;
- most external actions are already pinned by commit SHA.

Preserve this posture.

## Unpinned GitHub Actions references

Remaining tag-based action references:
- `backup-single-app.yml`: `actions/checkout@v4`;
- `backup-single-app.yml`: `actions/upload-artifact@v4`;
- `generate-v2-planning-docx.yml`: `actions/checkout@v4`;
- `generate-v2-planning-docx.yml`: `actions/setup-python@v5`.

Implementation target: no `@vN`, `@main`, `@master` or `@latest` external action ref remains in active workflows.

## Repository governance evidence

- Repository rulesets API returned an empty list.
- Classic main branch-protection endpoint returned 403 because the connected integration cannot read that administration endpoint.

Therefore:
- do not claim branch protection is enabled;
- do not claim branch protection is disabled;
- record it as `NEEDS_MANUAL_VERIFICATION`.

Target policy for later configuration:
- no force-push to main;
- no deletion of main;
- prefer PR-based implementation/release changes;
- require relevant CI/CodeQL checks where repository plan/settings allow;
- never allow historical release verifiers to regain publication permission;
- never retarget published v0.2.0/v0.2.1 tags.

## Planned implementation cards

### RHS-01 — stale PR closure
Objects: PR #11, PR #17.  
Acceptance: both closed, `merged=false`, with superseded note.

### RHS-02 — backup workflow correction
File: `.github/workflows/backup-single-app.yml`.  
Acceptance: V2 source + verified Git Bundle + v0.2.1 trusted build; `git bundle verify` PASS.

### RHS-03 — action pinning
Files: backup workflow and retained planning generator.  
Acceptance: no active tag-based action refs remain.

### RHS-04 — STEP00 generator retirement
File: `generate-v2-0.2.2-step00-docx.yml`.  
Acceptance: no `contents: write`; no direct push to main.

### RHS-05 — legacy planning generator retirement/conversion
File: `generate-v2-planning-docx.yml`.  
Acceptance: removed or manual/read-only; no direct push.

### RHS-06 — fresh dependency update
Object: stale Dependabot branch/PR.  
Acceptance: fresh update based on current main and normal CI PASS.

### RHS-07 — safe branch cleanup
Objects: historical/transient refs.  
Acceptance: unique-commit review + verified full Git bundle + no open PR dependency.

### RHS-08 — main governance verification
Object: GitHub repository settings.  
Acceptance: manual record/screenshot of effective protection before final v0.2.2 release.

## STEP 01 gate

**PASS**

The repository/workflow risk surface is bounded and mapped to explicit remediation cards.
No application code, schema, UI or dependency has been changed.

Repository remediation and application implementation remain blocked until STEP 05 authorizes exact implementation scope.

## Next exact STEP

**STEP 02 — Advanced Editor Lifecycle Regression Plan**

STEP 02 must plan direct Qt/offscreen regression coverage for:
- Apply / Discard / Cancel;
- asset switching;
- advanced activation confirmation;
- dormant-track acknowledgement;
- repeated activation;
- Undo/Redo transaction boundaries.

Do not begin STEP 03 or implementation in the same turn.
