# ADR-004 / Versioned JSON Project Document

Status: ACCEPTED
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Project is metadata-heavy and external-media referenced; no need for DB server.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
Use .aavcproj JSON, schema version, migration, atomic temp+replace, recovery snapshots.

## Alternatives considered
SQLite; ZIP-embedded media; opaque binary.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Inspectable, migratable, easy fixtures.

## Consequences — negative / trade-offs
Need schema discipline and atomic writer.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
