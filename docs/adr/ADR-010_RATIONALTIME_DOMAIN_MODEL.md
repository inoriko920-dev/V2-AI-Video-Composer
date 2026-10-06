# ADR-010 / RationalTime Domain Model

Status: ACCEPTED
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Future FPS and subtitle/audio timing need drift-free deterministic model.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
Store exact rational seconds num/den; convert at backend/UI boundaries.

## Alternatives considered
float seconds; fixed 30fps ticks.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Exact conversion and future FPS support.

## Consequences — negative / trade-offs
More verbose serialization/types.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
