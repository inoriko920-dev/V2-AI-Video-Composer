# ADR-009 / CI-first Windows Validation

Status: ACCEPTED
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Owner should not need toolchain; Windows build cannot be assumed from other OS.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
GitHub Actions Windows pipeline for checks/test/package/smoke.

## Alternatives considered
Manual-only builds.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Reproducibility and artifacts.

## Consequences — negative / trade-offs
GPU-specific behavior often remains runtime-probed/NOT TESTED.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
