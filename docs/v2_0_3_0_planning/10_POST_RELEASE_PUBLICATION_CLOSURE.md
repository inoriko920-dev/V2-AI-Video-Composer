# V2 AI Video Composer v0.3.0 — Post-release closure and handoff

Date: 8 October 2026, WIB (UTC+7)  
Scope: `inoriko920-dev/V2-AI-Video-Composer` **only**.  
Type: **historical evidence for an already-published release**; documentation-only post-release housekeeping, not a source-code change and not approval to publish another version.

## Final outcome

**PUBLICATION SUCCESS / PASS.** Public GitHub Release:
https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/tag/v0.3.0

- Release ID: `406788270`; version/tag: `v0.3.0`.
- Publication time from GitHub API: `2026-10-08T12:11:35Z` = **19:11:35 WIB**.
- Public release is `draft=false`, `prerelease=false`.
- Frozen release source and tag target: `d5a085fe239763e469ad30e91f526179fe8b2595`. Branch `main` was at this SHA when publication was verified.
- Previous published `v0.2.2` tag remains `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`; no old release asset was replaced.
- Final source-specific Windows qualification: [Actions #37770636024](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37770636024), PASS.
- Stable publication and public-download qualification: [Actions #37775119272](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37775119272), SUCCESS.
- CI on frozen main: [#37770538638](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37770538638), SUCCESS.
- CodeQL on frozen main: [#37770538585](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37770538585), SUCCESS.

## Final public release asset ledger

GitHub reports exactly **nine public assets** with `uploaded` state; the successful publishing workflow also downloaded all nine *public* assets and checked each byte's SHA-256 against its staged original.

| Artifact | Published SHA-256 |
| --- | --- |
| `AI-Automatic-Video-Composer-0.3.0-win64.zip` | `066312fe6c983c797939fccf5682f5f4867c6ba528a099d18e67f33a8e1c7681` |
| `AI-Automatic-Video-Composer-0.3.0-source.zip` | `063c3fa88c03972fdcadcf6c3a7d7c7b183df07b146710cd209a59cbb11ca9df` |

The seven other published assets are: `BUILD_INFO.txt`, `SHA256SUMS.txt`, `RELEASE_NOTES_0.3.0.md`, `V2_FINAL_RELEASE_MANIFEST_0.3.0.md`, `USER_GUIDE.md`, `MAINTENANCE.md`, and `BACKUP_AND_RECOVERY.md`. Their checksums are exposed in the public GitHub Release API, and the two ZIP hashes can be verified against the public `SHA256SUMS.txt`.

**Important provenance:** the source ZIP is an exact-source archive, **not** a complete repository disaster-recovery mirror; it does not include all commit history, refs, or branches.

## Evidence of Windows and product acceptance

Final Windows exact-main run #37770636024 reports:
- **907 nonvisual tests passed**; secret scan, pinned dependency graph, compile, Ruff, strict mypy.
- Windows portable EXE build and smoke, real UI screenshot capture.
- Special path tests **5/5 PASS** (ASCII, spaces, apostrophe, Unicode, nested/deep path).
- FFmpeg 9.0.2 reference tested for system PATH and app-local installation; **FFmpeg/ffprobe binaries are not included** in the public ZIP.
- Exact `BUILD_INFO.release_commit`, ZIP CRC and nested ZIP SHA-256 checks PASS.
- Frozen UI: 42 existing screens retained; three approved recovery dialogs retained; no redesign in this closeout.

Publication workflow #37775119272 reports `EXACT_MAIN_SOURCE_AND_NINE_RELEASE_ASSETS_PASS`, `DRAFT_ASSETS_NINE_OF_NINE_VERIFIED`, `PUBLIC_RELEASE_NINE_OF_NINE_SHA256_PASS`, and `FINAL_V0_3_0_PUBLICATION_PASS`.

## Guarded publication history (do not rerun)

Early publisher runs #37774513572 and #37774604355 failed safely at the ZIP/source comparison check before tag creation; the source was produced on Windows, so the final workflow compares its checked-in content with the frozen Git blobs allowing only CRLF-normalized text serialization. Run #37774936584 then created the correct stable tag and nine-asset draft but stopped at a draft-by-tag lookup returning 404. The successful follow-up #37775119272 reused **the same existing draft by release ID `406788270`**, verified all assets and published it. Earlier failed attempts do not imply a defective public package. No duplicate release or replacement of a historical tag was made.

The one-time publishing workflow is an operational audit artifact on a dedicated `publish/v0.3.0-approved-20261008` branch, **not** the runtime or the default branch. Treat it as spent; do not push to it or trigger/re-run it for a new version. Do not force-update `v0.3.0`, `v0.2.2` or existing published asset bytes.

## Actual-user Windows acceptance (not yet demonstrated)

Automated CI acceptance is **not** a substitute for manual use on the owner's Windows 11 PC. The next meaningful milestone is one real-world test and user bug report, not another speculative implementation wave.

1. Download the **public** `0.3.0-win64.zip` and its `SHA256SUMS.txt`, verify SHA-256, extract the entire directory and launch the root EXE.
2. Install compatible **external** FFmpeg/ffprobe in `tools/ffmpeg/` beside the executable or on the Windows PATH. Confirm the app can locate them.
3. Create a test project, **Save manually at least once**, modify it, and check that autosave eventually makes a local recovery candidate without clearing the dirty state or modifying the last manual Save.
4. Reopen with a valid recovery candidate: verify the Indonesian restore/use-saved/cancel decisions work and that Cancel does not change the project.
5. Try a copy of a project with modified or unreadable recovery metadata and verify the conflict/invalid dialogs are conservative. Preserve forensic sidecars/backups; do not deliberately corrupt the only project copy.
6. Render a small sample on the user's machine; confirm preview, final file, and FFmpeg discovery. Save the failure logs, Windows version and steps to reproduce if anything fails.

**Manual Windows user acceptance gate:** PENDING. Do not claim it passed until actual hands-on evidence exists.

## Next-version gate

- v0.3.0 release closure: **PASS** (public presence, checksum/source, historic tag, CI).
- Postrelease documentation synchronization: complete only after this docs-only PR passes checks and merges.
- User acceptance on physical Windows device: **PENDING**.
- Any v0.3.1 bug fix or new v0.4.0 feature must start as a new user-approved scoped plan; search existing implementations first, retain the 42 UI references, approved recovery dialogs, schema v3/v4, external FFmpeg model, and immutable published releases.
- Do not change the legacy original `AI-Automatic-Video-Composer` repository.

