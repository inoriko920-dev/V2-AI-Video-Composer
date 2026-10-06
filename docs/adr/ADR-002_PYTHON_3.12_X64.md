# ADR-002 / Python 3.12 x64

Status: ACCEPTED
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Fast iteration, existing Python-oriented workflow, PySide6 official bindings, AI maintainability.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
Use Python 3.12 x64; exact patch pinned in STEP 08.

## Alternatives considered
C++/Qt; C#/.NET; Electron.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Fast development and good tooling.

## Consequences — negative / trade-offs
Runtime packaging larger/slower than native; performance-critical work delegated to FFmpeg/Qt.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
