# ADR-008 / PyInstaller Onedir Portable Packaging

Status: ACCEPTED
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
User wants portable ZIP, not installer/single exe.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
Build Windows onedir package, bundle tools/resources, ZIP + manifest/checksum.

## Alternatives considered
onefile; installer-first; system Python.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
No Python install required; transparent bundled files.

## Consequences — negative / trade-offs
More files in distribution, spec maintenance.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
