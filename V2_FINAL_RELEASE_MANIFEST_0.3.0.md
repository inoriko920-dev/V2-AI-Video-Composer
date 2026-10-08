# V2 v0.3.0 — Non-Published Release Candidate Manifest

**Status: NOT PUBLISHED / RC PREPARATION.**

**Repository:** `inoriko920-dev/V2-AI-Video-Composer`.
**Target version and future tag:** `0.3.0` / `v0.3.0`.
**Platform:** Windows 11 x64 portable PyInstaller onedir.
**Previous immutable stable:** `v0.2.2` at
`eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.
**Pre-RC source:** `7d9ad7eda513daccea13a00c44d3d79bf76d9106`
(W06-E PR #61 merged).
**Exact RC source:** determined by the final merge/source SHA, **never infer from
an earlier passing build**.

## Source of truth

STEP00–05 v0.3.0 planning and approved UI final DOCX+three PNGs are retained
under `docs/v2_0_3_0_planning/`. W06-A through W06-E are merged in main and
validated; see `06_W06_E_FINAL_ACCEPTANCE_AND_RELEASE_READINESS_EVIDENCE.md`
for the final cross-wave safety matrix. No additional project serializer,
second Undo stack, UI redesign, provider, FFmpeg binary or credential source.

## Required RC assets, same source commit

- `AI-Automatic-Video-Composer-0.3.0-win64.zip` — full portable folder,
  verified root EXE and FFmpeg installation instructions, no FFmpeg binary.
- `AI-Automatic-Video-Composer-0.3.0-source.zip` — **exact `git archive HEAD`**
  source snapshot (not a full history disaster-recovery bundle).
- `BUILD_INFO.txt` — `version=0.3.0`, `release_commit` exact 40-character
  SHA, `channel=rc`, schema max 4, `advanced-v1`, Python/PySide6/
  PyInstaller versions and `publication_status=NOT_PUBLISHED`.
- `SHA256SUMS.txt` — independent SHA-256 of the two ZIPs, recomputed before
  artifact acceptance.
- `RELEASE_NOTES_0.3.0.md`, this manifest, `USER_GUIDE.md`,
  `MAINTENANCE.md` and `BACKUP_AND_RECOVERY.md`.

## Hard gates to graduate from RC

1. No preexisting `v0.3.0` Git tag or GitHub Release; never force-move a tag.
2. `v0.2.2` continues to resolve exactly to
   `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.
3. Runtime `aavc.__version__` equals `pyproject.toml`/installed metadata,
   all `0.3.0`.
4. Secret scan, pinned lockfile/install graph, compile, Ruff, strict mypy and
   complete nonvisual pytest PASS. Approved frozen UI screenshots unchanged.
5. Exact FFmpeg 9.0.2 reference tested in PATH and app-local modes; no
   `ffmpeg.exe`/`ffprobe.exe` copied into public ZIP.
6. Windows portable build, EXE smoke and actual Qt window capture PASS;
   special paths (spaces, Unicode, apostrophe and longer nested path) when
   qualified in RC.
7. Artifacts are downloaded/inspected and SHA-256 independently checked.
8. Only a separate, explicitly approved guarded **publication** stage may
   create the stable tag/release and publish user-facing ZIPs.

## Current release decision

The workflow under `.github/workflows/v2-0.3.0-rc.yml` has **read-only GitHub
content permission** and can only upload an expiring workflow artifact.
It cannot and must not create a public release.

**Windows acceptance and a non-published RC are not proof that v0.3.0 has
already been released.** Record actual run, SHA and hashes only after execution.
No guarantees are made against arbitrary external editors or sudden power loss.
