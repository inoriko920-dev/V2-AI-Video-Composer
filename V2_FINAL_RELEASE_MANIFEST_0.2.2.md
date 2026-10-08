# V2 0.2.2 Candidate Release Manifest

Status: **DRAFT / NON-PUBLISHING / STEP 06 W06-D**

## Candidate contract

- Candidate version: `0.2.2`
- Proposed (uncreated) tag: `v0.2.2`
- Target: Windows 11 x64; portable PyInstaller onedir ZIP
- Exact source: `git archive HEAD` from the checked-out candidate commit
- Metadata: `BUILD_INFO.txt` with source SHA, channel, project schema v4, advanced-v1 contract, Python, PySide6, PyInstaller and FFmpeg reference
- Integrity: `SHA256SUMS.txt` for exact source and Windows ZIP, independently re-verified during candidate creation
- User docs: `RELEASE_NOTES_0.2.2.md`, `USER_GUIDE.md`, maintenance and backup/recovery policies
- FFmpeg: validated external **9.0.2** reference, SHA-256 fingerprints recorded in acceptance logs, no binaries in public AAVC ZIP
- Security: repository tracked-file secret scan and built-artifact content scan (no secret values printed)
- UI: frozen white/blue, eight STEP09 states, 21 native effects
- Project compatibility: readable schema max 4, advanced-v1 keyframe contract

## Release gates

W06-D builds and tests candidate artifacts, not a published release. W06-E is the consolidated regression closure. STEP 07 must separately verify commit/tag immutability, CI, CodeQL, Windows acceptance, screenshots, real render/effects, portable executable, checksums and manual final authorization as required by Software Factory.

## Do not publish

The W06-D workflow uses `contents: read` only and cannot create or overwrite tags or GitHub Releases. Historical v0.2.1 and earlier workflows and tags must remain unchanged. Candidate source/hash evidence is tied to the exact checkout commit, **not** guaranteed byte-identical across rebuilds.
