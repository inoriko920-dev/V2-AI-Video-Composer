# ADR-012 / Qt Overlay Preview + Cached Base Proxy

Status: PROVISIONAL
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Interactive layout/animation must remain responsive while final uses FFmpeg.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
FFmpeg builds base proxy; Qt plays it and renders live foreground/subtitles with same timing/effect specs.

## Alternatives considered
MLT single-engine preview; full pre-render after every edit.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Fast interactive foreground edits and small backend footprint.

## Consequences — negative / trade-offs
Parity needs SPK-003.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
