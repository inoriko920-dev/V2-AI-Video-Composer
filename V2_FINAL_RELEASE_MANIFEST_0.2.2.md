# V2 Final Release Manifest — AI Automatic Video Composer 0.2.2

**Stage in source:** Final-publication candidate; publication requires a separately guarded exact-commit workflow.  
**Planned version/tag:** `0.2.2` / `v0.2.2` (tag may be created only after the guarded release gate passes).
**Target:** Windows 11 x64 portable onedir ZIP.

## Immutable sources and prerequisites

- v0.2.1 stable tag must remain at `eb94efebf142ba8203dfc3ae3c5fa861222a0926`.
- Published v0.2.0 and v0.2.1 releases are not modified.
- Consolidated STEP06 source: `607fb5b59f6788892b60027d736cf99b8898c6a7`.
- Frozen RC branch: `release/v0.2.2-rc-source-w06e-607fb5b59f67`.
- STEP07 frozen-source Windows RC validation: [run 37725077066](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37725077066) **PASS**.
- STEP07 RC artifact ID: `11527950278`; GitHub artifact archive digest: `sha256:860e58228cff566f8e323873e335dea74eec223bee926b4a0e271b5384327f5e`.
- RC scope passed: **795 technical tests**, real FFmpeg/ffprobe 9.0.2, 21 native effects, advanced v4 rendering, Save/Recovery regressions, scanned Windows portable build, EXE smoke, extracted-archive path matrix (5 cases), app-local/PATH precedence, and archive SHA-256 re-verification.
- W06-E final PR #45 CI 37724347445, CodeQL 37724347426, Windows acceptance 37724347375, backend 37724347500: PASS.
- W06-E main `607fb5b59f6788892b60027d736cf99b8898c6a7`: push CI 37724784652 and CodeQL 37724784710 PASS.

## Exact final source and release gates

The final release source commit is the merge commit of this final-documentation preparation. The guarded publisher MUST read and verify that exact 40-character SHA, checkout it directly, and generate `git archive HEAD` from it. A successful RC on another commit cannot substitute for the final build.

Final publication requires:

1. Final source commit frozen and independently read back from GitHub.
2. CI and CodeQL on final source PASS; full Windows nonvisual real-FFmpeg acceptance PASS; final portable EXE smoke and UI capture PASS.
3. Exactly `0.2.2` in runtime and package metadata; schema max v4; advanced-v1; 21 native effects.
4. Source-secret scan plus built-distributable credential scan PASS; portable ZIP excludes ffmpeg.exe and ffprobe.exe; FFmpeg 9.0.2 reference and app-local/PATH modes PASS.
5. Candidate bundle contains Windows portable ZIP, exact-source ZIP, BUILD_INFO (full source SHA, version, channel, schema, advanced contract, pinned tools), `SHA256SUMS.txt` (portable/source checksums), release notes, guide, maintenance, backup/recovery and this manifest.
6. Downloaded release candidate rechecked from archive, and SHA-256 values recomputed before publication. GitHub Release must refuse pre-existing v0.2.2 tag or release; no overwrite/move logic is permitted.
7. Publisher's limited write permission is isolated to the publication job and checked against source tag target. After publication, tag resolves to final source SHA and release is neither draft nor prerelease.

## Distribution and known limitations

FFmpeg binaries remain external, installed in `tools/ffmpeg/` or PATH, not redistributed. Project schema v4 advanced-v1, 21 effects, Gemini model and frozen white/blue UI are unchanged. The production autosave scheduler and user-facing Restore/Discard/Cancel startup UI (deferred GAP-03A) are not included.

Python 3.12.10, PySide6 6.11.2 and pinned project dependencies remain unchanged for reproducibility. Ruff 0.16.10, setuptools-backend alignment, Python security-line changes and broad dependency upgrades remain deferred.

**This committed manifest is the pre-publication source contract, not proof of a published release.** The published release URL/tag SHA and final workflow checks must be recorded in a subsequent post-publication closure document, without modifying the already-published tag or source.
