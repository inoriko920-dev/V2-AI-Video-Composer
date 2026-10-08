# AI Automatic Video Composer 0.2.2 — Maintenance Candidate

Status: **PRE-RELEASE / NOT YET PUBLISHED**

0.2.2 is a targeted maintenance/hardening patch over published v0.2.1. It is not a new feature release. Final publication requires separate STEP 07 release validation; this document does not authorize a tag or GitHub Release.

## Corrections incorporated into the candidate

- **W06-A — Repo/workflow security:** one-app V2 Git Bundle backup corrected; workflow action pinning and read-only planning DOCX generation.
- **W06-B — Advanced animation editor:** actual schema v4 context is displayed; Apply follows the canonical advanced-activation command with explicit user confirmation; reject leaves state unchanged.
- **W06-C — Project data safety:** failed Save/Save As does not destroy unreadable target projects; repeated recovery creates numbered, non-clobbering pre-recovery backups.
- **W06-D — Packaging:** Windows onedir spec disables opportunistic UPX; built-artifact content is scanned for supported credential signatures and forbidden runtime files; FFmpeg 9.0.2 reference is enforced and both app-local and PATH resolution are checked; candidate source and Windows portable ZIPs have SHA-256 evidence.

## Compatibility and stable architecture

- Maximum project schema remains **v4**; `animation_keyframe_contract=advanced-v1` is unchanged.
- Native 21 effects, FFmpeg final/reference rendering, copied white/blue PySide6 UI, Gemini provider/credential model remain unchanged.
- Windows 11 x64; Python 3.12.10; PySide6 6.11.2; PyInstaller onedir; no installer conversion.
- The application keeps FFmpeg/ffprobe binaries **external**. Install an approved reference build on PATH or place it in app-local `tools/ffmpeg/`. The public archive contains instructions, not the FFmpeg executables.
- Existing published releases and `v0.2.1` source/tag are immutable.

## Explicit limitations

The repository contains the RecoveryManager service, but automatic periodic autosave and the interactive Restore / Discard / Cancel recovery flow are **not yet connected to the product runtime** (deferred GAP-03A). W06-C hardens recovery data safety; it does not claim full end-user recovery integration.

Windows candidate builds are validated through CI, CodeQL, real FFmpeg technical acceptance and packaged EXE smoke/UI capture. **Passing a candidate gate is not publication approval.**

## Before publication

STEP 06 / W06-E must consolidate all implementation regressions. STEP 07 must independently freeze final source identity, verify the release candidate, require clean CI/CodeQL/Windows acceptance, prove checksums and immutable-tag safeguards, and only then consider publication under a new v0.2.2 tag.
