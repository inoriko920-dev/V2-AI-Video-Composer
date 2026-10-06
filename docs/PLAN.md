# PLAN — Post Release 0.1.0

Software Factory STEP 00 through STEP 15 is complete and release `0.1.0` is sealed.

## Current phase
Post-release maintenance on the `0.1.x` stable line. There is no automatic STEP 16 and no active feature wave.

## Change routing
1. Reproduce or define the requested change precisely.
2. Search existing modules/tests before creating new code.
3. Classify the change using `MAINTENANCE.md`.
4. Preserve architecture, project-schema compatibility, UI Freeze contracts, credential safety, and portable-path rules.
5. Add or update focused tests for behavior changes.
6. Run the required quality/release gates appropriate to the change.
7. Update `docs/PROJECT_STATE.md` and `docs/TASKS.md` when a new active task or release phase begins.

## Version direction
- `0.1.x`: bug fixes, UI collision fixes, provider compatibility, security hardening, packaging fixes.
- next minor `0.x.0`: approved compatible user-visible capability or schema expansion.
- `x.0.0`: intentional breaking project/schema/workflow change.

## Next formal work
Wait for a concrete maintenance item or explicitly approved feature request. Do not reopen completed STEP 09–15 implementation merely because older planning text references it.
