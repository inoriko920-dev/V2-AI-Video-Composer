# ADR-006 / Thin FFmpeg/ffprobe Media Backend

Status: ACCEPTED
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Automatic compositor scope is narrower than full NLE; packaging/CI/license control important.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
Bundled CLI with capability probe, immutable RenderPlan and centralized command builder.

## Alternatives considered
MLT core; libopenshot core; editor fork.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Small runtime surface, mature media support, explicit capability.

## Consequences — negative / trade-offs
Preview/final parity and complex effects require compiler tests.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
