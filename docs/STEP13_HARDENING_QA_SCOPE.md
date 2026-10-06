# STEP 13 — Hardening & QA Scope

STEP 13 hardens the already-working product path instead of adding new creative features.

## Required hardening areas
- render preflight must block missing/invalid media before FFmpeg execution
- background work must support cooperative cancellation without blocking the UI thread
- diagnostics must redact provider secrets before export
- recovery/provider failures must remain deterministic and testable
- CI must keep compile, Ruff, strict mypy, cheap pytest, and representative Qt screenshot capture green

## Acceptance
1. negative-path unit tests exist for missing render inputs
2. job cancellation reaches a terminal CANCELLED state
3. diagnostic ZIP output contains no explicit secrets supplied to the redactor
4. STEP 09 representative UI screenshots continue to pass on Windows CI
5. no live AI provider calls are required by CI
