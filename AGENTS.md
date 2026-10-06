# AGENTS.md SPECIFICATION — v1.0

Target length: concise, roughly 1–3 screens. It must contain:

1. Project identity: AI Automatic Video Composer; Windows desktop; portable onedir ZIP.
2. Source of truth: ARCHITECTURE, CODE_CONSTITUTION, PROJECT_STATE, active TASKS, UI_FREEZE.
3. Architecture: presentation -> application -> domain; adapters/infrastructure outside; composition root wiring only.
4. Search-before-create protocol.
5. Canonical commands: dev/test/package/portable verify (once implemented).
6. Forbidden actions: direct filesystem/provider/subprocess from UI/domain, raw secrets, hidden globals, silent fallback, mass refactor, unapproved dependency, overwrite others' work.
7. Before/during/after change checklist.
8. Evidence requirement: tests + diff + artifact/screenshots where relevant.
9. Astra review triggers.
10. Portable contract: PathService, no developer absolute paths, no writes into app bundle, no unapproved FFmpeg binary.
