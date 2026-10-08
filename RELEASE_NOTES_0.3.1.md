# AI Automatic Video Composer v0.3.1 — Patch Candidate Notes

**Status: NOT_PUBLISHED / NOT PUBLISHED.** This file describes a **source-only
maintenance candidate** under STEP02. It is not a public release, and it is not
evidence that a Windows v0.3.1 portable ZIP has been built or tested. The
current public stable is [v0.3.0](https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/tag/v0.3.0).

**Target:** Windows 11 x64, PyInstaller onedir portable (future STEP03/04).
**Scope:** Compatibility/maintenance patch only, no new feature wave.

## Patch relative to v0.3.0

- Normalize microphone narration recording destinations to lowercase **.wav**
  when the input path has uppercase or mixed-case extensions such as **.WAV**
  and **.WaV**. No-extension and other-extension names are canonicalized too.
- Existing recording staging, atomic finalization and old-file preservation
  on failure remain unchanged.
- Align version metadata, bundled release notes and Windows acceptance to
  distinguish active source version 0.3.1 from **immutable published v0.3.0**
  artifacts. This is a packaging/quality change, not a new editor feature.

## Unchanged behavior / compatibility

- Project schemas v3/v4, advanced-v1, all 21 native effects, timeline, render,
  subtitles, preview, frozen white/blue editor UI and the three approved recovery
  dialogs remain intact.
- Local **autosave** and project **recovery** continue to work only for projects
  that were saved manually at least once. Keep backups and recovery sidecars;
  they are user data, not application release assets.
- Gemini credential handling, PySide6/Python pins and FFmpeg architecture
  remain unchanged. **FFmpeg** and ffprobe are external dependencies, with
  FFmpeg 9.0.2 as the Windows reference. They are not bundled in this app.

## Verification, identity, and publication

STEP02 covers source identity, tests and bundled-document metadata only. STEP03
must add a dedicated read-only candidate builder, exact-source ZIP and SHA-256
manifest; STEP04 must prove Windows tests, executable smoke, UI capture and
render. A separate explicit user authorization is required before any v0.3.1
tag or GitHub Release is created.

Do not use v0.3.0 assets as a substitute for the v0.3.1 candidate. Never
replace the previously published v0.3.0 or v0.2.2 tags, assets or checksums.
The source ZIP planned for v0.3.1 is a source snapshot and not a complete
Git-history disaster-recovery backup.

**Owner Windows 11 manual acceptance remains PENDING.**
