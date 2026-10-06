# DEPENDENCY_POLICY

1. Every runtime dependency requires owner, reason, license, exact pin, provenance and removal plan.
2. Domain imports stdlib/domain packages only.
3. No raw subprocess outside platform/process_runner.
4. No raw provider HTTP/SDK outside providers.
5. No absolute developer drive path in production code.
6. No plaintext secret in source, config examples, project file or logs.
7. One library per responsibility unless an ADR approves overlap.
8. MLT/libopenshot are not R1 runtime dependencies.
9. Qt module selection must be license-audited; avoid GPL-only modules without approval.
10. FFmpeg binary is an approved artifact with hash, version, buildconf, license, filter/encoder capability manifest.
