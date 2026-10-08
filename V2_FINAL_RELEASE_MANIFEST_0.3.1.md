# V2 v0.3.1 — Candidate Distribution Contract (STEP02, source only)

**Current state:** NOT_PUBLISHED. **NO TAG, no tag, no GitHub Release, and no public download.** STEP03 may create an expiring **Actions artifact** containing a verified Windows candidate portable ZIP and matching source.zip. That technical artifact is not an official release, and its exact source SHA must be checked against its own BUILD_INFO.txt; this manifest does not invent any build checksum.

**Repository:** `inoriko920-dev/V2-AI-Video-Composer`  
**Candidate version:** `version=0.3.1`; future candidate tag `v0.3.1`.  
**Platform:** Windows 11 x64; PyInstaller onedir.  
**Frozen public previous stable:** `v0.3.0` at
`d5a085fe239763e469ad30e91f526179fe8b2595` (9 public assets).  
**Frozen earlier stable:** `v0.2.2` at
`eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.

## Scope

Single runtime change from the frozen stable source: canonicalizing microphone
recording paths to lowercase `.wav` even for input `.WAV` and `.WaV`. The
known merged PR #65 already implements this. PR #64 is CI/documentation only.
Project schemas v3 and v4, `advanced-v1`, the autosave recovery model, all 21
effects, frozen UI, and credentials remain unchanged.

## Source and candidate artifact identity contract — verified only after a successful STEP03 Actions run

A STEP03 read-only builder produces these **candidate-only** artifacts from
the exact same Git commit and version as the tested executable:

- `AI-Automatic-Video-Composer-0.3.1-win64.zip`: entire onedir package, root
  `AI Automatic Video Composer.exe`, `tools/ffmpeg/README.md`, no embedded
  `ffmpeg.exe` or `ffprobe.exe`.
- `AI-Automatic-Video-Composer-0.3.1-source.zip`: `git archive` of exact
  commit (a snapshot; **not a full** Git history or all refs).
- `BUILD_INFO.txt`: must include `version=0.3.1`,
  `release_commit=<40-character exact Git SHA>`, `schema_max=4`,
  `animation_contract=advanced-v1`, dependency versions and
  `publication_status=READY_FOR_PUBLICATION`.
- `SHA256SUMS.txt`: independently rechecked SHA-256 digests of each ZIP.
- `RELEASE_NOTES_0.3.1.md`, `V2_FINAL_RELEASE_MANIFEST_0.3.1.md`,
  `USER_GUIDE.md`, `MAINTENANCE.md`, `BACKUP_AND_RECOVERY.md`.

**READY_FOR_PUBLICATION is a technical artifact state, not PUBLISHED**.
No release_commit or ZIP SHA-256 values are asserted in this source file because
the resulting ZIP hashes depend on the exact successful STEP03 build. Use that
workflow run's BUILD_INFO.txt and SHA256SUMS.txt as authoritative candidate
evidence. A future final release must be explicitly approved and checked
against public bytes and tag identity again.

## Hard gates for STEP03/04/05

1. Reject existing `v0.3.1` tag/release and existing output location; no
   overwriting, no force tags, no previous-release replacement.
2. Confirm `v0.3.0` and `v0.2.2` refs and all nine stable assets unchanged.
3. `pyproject.toml`, `aavc.__version__`, installed metadata and EXE version
   agree on 0.3.1; no unreviewed dependency changes.
4. Secret scan, compileall, Ruff, strict mypy, full nonvisual tests, CodeQL
   and optional backend checks pass on exact final head.
5. Windows FFmpeg reference **9.0.2**, render effects, frozen UI screenshot,
   EXE smoke and five portable paths pass.
6. Validate ZIP CRC, membership, source provenance, rehash **SHA-256** digests,
   and embedded release notes against that same commit.
7. STEP03 workflow has `contents: read` only and uploads an expiring Actions
   artifact, never a GitHub Release.
8. Merge only after all head gates PASS; afterwards run CI/CodeQL on main
   merge commit before freezing candidate source.
9. Windows 11 **manual owner UAT** is separate and currently PENDING; do not
   claim the user tested the app.
10. Publication requires an independent explicit instruction; STEP02 does not
    create or request a public release.

## Rollback, secrets and privacy

The verified v0.3.0 public package remains rollback baseline. Never package
personal projects, sidecars, backup files, API keys or Credential Manager data.
FFmpeg/ffprobe remain external only. Independent full-repository disaster
recovery requires a separate `git bundle`, not a source.zip.
