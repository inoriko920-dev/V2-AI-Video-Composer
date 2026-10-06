# ADR-011 / ASS/libass Final Subtitle Pipeline

Status: PROVISIONAL
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Need crisp final-resolution text, outline/shadow/box and karaoke.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
Generate ASS and burn via verified FFmpeg libass capability.

## Alternatives considered
drawtext-only; Python rasterize every frame.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Mature text renderer; karaoke support.

## Consequences — negative / trade-offs
Depends on chosen FFmpeg build capability/license.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
