# ADR-005 / Central Job System

Status: ACCEPTED
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Long operations must never block UI; cancel/progress/retry semantics need one owner.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
JobManager + QThreadPool; external processes through ProcessRunner.

## Alternatives considered
Ad-hoc threads; asyncio everywhere.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Consistent lifecycle and diagnostics.

## Consequences — negative / trade-offs
Requires stale-result/revision guards.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
