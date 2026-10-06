# ADR-001 / Modular Monolith Layered Architecture

Status: ACCEPTED
Date: 3 Oktober 2026
Owner: ASTRA / Product Architecture

## Context
Desktop product needs clear ownership without microservice overhead.

## Architecture drivers
ADRIVER-001..010 as applicable.

## Decision
Presentation -> Application -> Domain; infrastructure adapters wired at composition root.

## Alternatives considered
Full editor fork; service-locator monolith; microservices.

## Why chosen
Derived from PB-AAVC-v1.0 and UIF-AAVC-v1.0; favors portable Windows, deterministic project state, UI freeze fidelity and maintainability.

## Consequences — positive
Simple dependency direction, AI-readable modules, local transactions.

## Consequences — negative / trade-offs
Requires deliberate port interfaces and architecture tests.

## Migration / rollback
Revisit by superseding ADR; do not silently change runtime architecture.

## Validation evidence
STEP 02 discovery + STEP 05 freeze + official documentation cited in master STEP 06.

## Open assumptions
Exact dependency patch versions and capability-specific details are pinned/validated in later steps.

## Trigger to revisit
A mandatory spike fails, a frozen requirement cannot be met, license constraints block distribution, or benchmark proves architecture unsafe.
