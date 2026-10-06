# ADR-003 / PySide6 Qt Widgets

Status: ACCEPTED
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Frozen UI is desktop editor with split panes, custom preview/timeline, modal/drawer, DPI/focus.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
Use Qt Widgets with custom painting where required.

## Alternatives considered
Tkinter; Electron; QML-first.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Native desktop controls, resizable panels, strong Windows fit.

## Consequences — negative / trade-offs
License/module selection requires governance.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
