# V2 v0.3.0 — Distribution Manifest

**Distribution metadata:** this document defines required package contents.
It does not itself establish whether a public GitHub Release exists; confirm
publication and tag identity from the GitHub Releases page.

**Repository:** `inoriko920-dev/V2-AI-Video-Composer`.
**Package version and matching release tag:** `0.3.0` / `v0.3.0`.
**Platform:** Windows 11 x64 portable PyInstaller onedir.
**Previous immutable stable:** `v0.2.2` at
`eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.
**Exact distribution source:** the 40-character SHA in `BUILD_INFO.txt` must
match the released tag target and the source archive. Never substitute a
previously validated build from a different commit.

## Source of truth

The central v0.3.0 feature is local **autosave** and guarded project recovery.

STEP00–05 v0.3.0 planning and approved UI final DOCX+three PNGs are retained
under `docs/v2_0_3_0_planning/`. W06-A through W06-E are merged in main and
validated; see `06_W06_E_FINAL_ACCEPTANCE_AND_RELEASE_READINESS_EVIDENCE.md`
for the final cross-wave safety matrix. No additional project serializer,
second Undo stack, UI redesign, provider, FFmpeg binary or credential source.

## Required distribution assets, same source commit

- `AI-Automatic-Video-Composer-0.3.0-win64.zip` — full portable folder,
  verified root EXE and FFmpeg installation instructions, no FFmpeg binary.
- `AI-Automatic-Video-Composer-0.3.0-source.zip` — **exact `git archive HEAD`**
  source snapshot (not a full history disaster-recovery bundle).
- `BUILD_INFO.txt` — `version=0.3.0`, `release_commit` exact 40-character
  SHA, a build channel, schema max 4, `advanced-v1`, Python/PySide6/
  PyInstaller versions and `publication_status=READY_FOR_PUBLICATION`.
  The status describes build validation, not a claim that GitHub has published it.
- `SHA256SUMS.txt` — independent SHA-256 of the two ZIPs, recomputed before
  artifact acceptance.
- `RELEASE_NOTES_0.3.0.md`, this manifest, `USER_GUIDE.md`,
  `MAINTENANCE.md` and `BACKUP_AND_RECOVERY.md`.

## Verification gates for a release

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

## Evidence and provenance

The read-only workflow under `.github/workflows/v2-0.3.0-rc.yml` validates and
uploads a temporary Actions artifact; it has no GitHub Release creation rights.
A separate explicitly approved publisher must verify exact bytes and the
release tag before sharing assets publicly. GitHub Release API and published
asset hashes are authoritative for actual publication. No guarantees are made
against arbitrary external editors or sudden power loss.
