# Maintenance Policy — AAVC 0.2.x

## Stable line
`0.2.x` is the current maintained V2 Windows desktop line. Patch releases must preserve project schema v3 compatibility unless a documented migration is added. Published `0.1.0` and `0.1.1` remain frozen historical releases and are never moved or overwritten.

## Change classes
- Patch (`0.2.x`): bug fixes, UI collision fixes, provider compatibility, security hardening, packaging fixes.
- Minor (`0.x.0`): new user-visible capability or compatible schema expansion.
- Major (`x.0.0`): intentional breaking project/schema/workflow change.

## Required gate before every release
1. compileall passes;
2. Ruff passes;
3. strict mypy passes;
4. cheap pytest passes;
5. representative STEP 09 Qt screenshot capture/verification passes;
6. portable PyInstaller build passes foundation smoke;
7. no secret/user runtime file appears in artifact;
8. SHA-256 is generated for the portable ZIP.

## External compatibility watch
Review before a patch release when any of these change:
- Gemini authentication/API behavior or provider error semantics;
- PySide6 / Qt version;
- Python 3.12 support window;
- FFmpeg build, codec set or license profile;
- Windows 11 packaging/runtime behavior.

## Security handling
Never request users to commit API keys. Reproduction bundles must use redacted diagnostics. Credential-store and provider changes require dedicated tests for raw-secret leakage.

## Project files
Keep versioned JSON migrations additive when possible. Never silently rewrite an unknown future schema version.
