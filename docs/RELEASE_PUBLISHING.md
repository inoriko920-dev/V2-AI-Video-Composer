# GitHub Release Publishing — AAVC 0.2.x

## V2 0.2.0 publication

Status: **PUBLISHED / VERIFIED**

Canonical release:
- Version: `0.2.0`
- Git tag: `v0.2.0`
- Release commit: `c6ad75308d302cd816301a2a7a34ebe7eb4148a7`
- GitHub Release ID: `405435925`
- Final workflow run: `37579907844` — PASS
- Main CI: `37579907856` — PASS
- Main CodeQL: `37579907845` — PASS
- Windows ZIP SHA-256:
  `eea46b42400c91e22d731c8261b9d7f29933ee0f94d45bcaa331a001805c525c`
- Source ZIP SHA-256:
  `fbdabd43c71f1585e817ce30f27d611668ecb0dc3c39df0b19a441968f0f7fe9`
- Final candidate artifact: `11463714566`
- Final UI evidence artifact: `11464770244`

The guarded final workflow completed Windows validation, internal CodeQL, checksum
re-verification, immutable tag/release checks, publication, and published-tag
verification. The workflow is now retained as historical verification-only. Historical
`v0.1.0` and `v0.1.1` remain immutable, and `v0.2.0` must never be moved or
overwritten.

---

# Historical GitHub Release Publishing — AAVC 0.1.x

## Current publication status

**0.1.1 — PUBLISHED / VERIFIED**

Official GitHub Release `v0.1.1` was published on 2026-10-04 as a maintenance patch.

Canonical evidence:
- Version: `0.1.1`
- Git tag: `v0.1.1`
- Frozen source ref: `release/0.1.1`
- Sealed source commit: `a6515ee7c4c9cda88a0c8aa93892c36eaf292d2e`
- Maintenance Release Windows 0.1.1 run: `#1` / `37181599863`
- Windows ZIP SHA-256: `84ad8cc93f055cb95fc2624511a9eecd541505627628090c277a048e5e8495b4`
- Source ZIP SHA-256: `a5a00b196e76d34684deef97b9dc605b748e1a32f2f92fe6f761c25b13f720bb`

`BUILD_INFO.txt` records the same release commit and version `0.1.1`. `SHA256SUMS.txt` matches independently computed hashes for both release ZIP files.

Direct artifact inspection confirmed that the Windows ZIP contains `AI Automatic Video Composer.exe` and `tools/ffmpeg/README.md` at portable root, with no redundant `_internal/tools/ffmpeg/README.md` copy.

## 0.1.1 published files

- `AI-Automatic-Video-Composer-0.1.1-win64.zip`
- `AI-Automatic-Video-Composer-0.1.1-source.zip`
- `RELEASE_NOTES_0.1.1.md`
- `MAINTENANCE.md`
- `BACKUP_AND_RECOVERY.md`
- `BUILD_INFO.txt`
- `SHA256SUMS.txt`

## 0.1.1 publication closure

The successful publication used frozen `release/0.1.1`, validated version `0.1.1`, ran all release gates, and published the canonical `v0.1.1` assets. A one-shot branch was used only because the chat connector did not expose `workflow_dispatch`; duplicate publication was subsequently refused by the overwrite guard.

Publication is now closed. The workflow retained on `main` is historical verification-only: it has read-only repository permission, no publish input, no `contents: write` job, and cannot create or replace a Git tag or GitHub Release.

Do **not** repeat publication for `v0.1.1`; the existing release is the canonical artifact.

## Historical 0.1.0 release

Official GitHub Release `v0.1.0` remains published and unchanged.

Canonical evidence:
- Frozen source ref: `release/0.1.0`
- Sealed source commit: `92da28bbb8177b11b3d09f000a4e7e01d389ccc5`
- Final Release Windows run: `#6` / `37180132492`
- Windows ZIP SHA-256: `c3e4f92656aefd3d57329627c52b8e057d2f8cac5a0a757471b90cb1d68915e8`
- Source ZIP SHA-256: `1264b1dc483932b496acf87dee21c93f92d4e1b222aa37ca2284fbf99b9df328`

## Historical workflow retirement

All workflows for already-published releases are retained only for reproducibility and historical verification. They are `workflow_dispatch`-only and use read-only repository permissions.

- RC 0.1.0 verification is pinned to `release/step14-rc1`.
- Final 0.1.0 verification is pinned to `release/0.1.0`.
- 0.1.1 verification is pinned to `release/0.1.1`.
- None of these historical workflows contains a GitHub Release publication job or `contents: write` permission.
- Historical verification artifacts are named explicitly so they cannot be confused with canonical published releases.

These workflows must not be used to publish a new release. A future maintenance version must use a newly planned version, frozen source, release notes, gates, and guarded publication path.

## Future releases

Do not move or replace published `v0.1.0` or `v0.1.1` tags in place. Corrections must use an explicitly planned new version under `MAINTENANCE.md`.

For a later patch/minor/major release, define the new version, frozen source, release notes, compatibility implications, release gates, and guarded publication path before publication.
