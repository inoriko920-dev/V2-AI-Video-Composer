# STEP09-B — Verified Final-Source v0.3.0 Distribution Package

**Verified:** 8 October 2026 WIB  
**Result:** PASS / ready for publication approval, **NOT PUBLISHED**  
**Application:** `inoriko920-dev/V2-AI-Video-Composer` only  
**Exact final-main SHA:** `d5a085fe239763e469ad30e91f526179fe8b2595` (PR #63 merged)  
**Immutable previous stable `v0.2.2`:** `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`  
**GitHub Actions exact-source Windows verification:** [run 37770636024](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37770636024) — SUCCESS  
**Nonpublished GitHub Actions artifact:** `11548645506` (`AAVC-0.3.0-FINAL-READY-NOT-PUBLISHED`), 65,955,936 bytes, envelope digest `sha256:f4b0db7de2003b6290a23d9cfe09339ef823c3ad9aa7fa5c0994319ebf2dbcac`.

## Independent artifact extraction and checksum verification

The artifact was downloaded, its outer ZIP and both nested ZIP CRCs checked, SHA256SUMS recomputed from the actual binary bytes, and an extracted user-facing Windows package/source package inspected directly.

| Final nested ZIP | Bytes | SHA-256 |
|---|---:|---|
| `AI-Automatic-Video-Composer-0.3.0-win64.zip` | 62,262,479 | `066312fe6c983c797939fccf5682f5f4867c6ba528a099d18e67f33a8e1c7681` |
| `AI-Automatic-Video-Composer-0.3.0-source.zip` | 3,891,242 | `063c3fa88c03972fdcadcf6c3a7d7c7b183df07b146710cd209a59cbb11ca9df` |

Direct checks:

- Outer artifact ZIP: **CRC PASS, 12 entries**.
- Windows portable ZIP: **CRC PASS, 269 entries**.
- Exact-source ZIP: **CRC PASS, 674 entries**.
- Both SHA-256 values match the Actions-produced `SHA256SUMS.txt`: **PASS**.
- `BUILD_INFO.txt` contains `version=0.3.0`, `release_commit=d5a085fe239763e469ad30e91f526179fe8b2595`, `schema_max=4`, `animation_contract=advanced-v1`, `ffmpeg_distribution=external-only`, `publication_status=READY_FOR_PUBLICATION`: **PASS**. This is a **build-stage status only**, not proof of a public release.
- ZIP Windows contains the application EXE, FFmpeg external-install README and neutral `RELEASE_NOTES_0.3.0.md` (no `RELEASE CANDIDATE` or `NOT PUBLISHED` label): **PASS**.
- No `ffmpeg.exe` / `ffprobe.exe` bundled: **PASS**.
- Exact source contains recovery-aware Qt window module and the same released-notes bytes: **PASS**.
- Windows special-path matrix: ASCII, SPACES, APOSTROPHE, UNICODE, DEEP: **5/5 PASS**.
- Exact-main checkout before Windows full regression, Ruff, strict mypy, pinned FFmpeg 9.0.2, portable EXE smoke, actual UI capture and SHA checks: **PASS**.
- PR #63 final-head CI, CodeQL, backend and Windows user acceptance plus dedicated Windows candidate: **PASS** before merging.
- `main` still at source SHA above, `v0.2.2` tag unchanged, no official `v0.3.0` tag or GitHub Release.

## Superseded evidence

All previous v0.3.0 ZIP hashes from candidate commit `54019195...` and prior frozen source commit `5c29d162...` are **not** final. They must not be used for public release validation. Only the two hashes in the table above belong to the new final documentation and source commit.

## Next gate: separate publication approval

**Publication: HOLD.** The user has instructed further preparation but has not explicitly authorized creating a public stable `v0.3.0` tag and GitHub Release. When they explicitly authorize publication, the publisher must first recheck the tag/release absence, old immutable tag, exact source SHA, artifact digest, ZIP CRC and SHA, and expected file inventory. It may only then create a new non-force `v0.3.0` tag and release; following publication it must download and rehash public assets, check sizes and stable release flags, and report any PARTIAL PUBLICATION instead of overwriting tags.

**No public GitHub mutation or unapproved re-build occurred during this verification.** The one-time branch-only workflow was removed after completion; this handoff remains on the verification branch so the tested `main` source commit stays unchanged.

A source ZIP is a `git archive` snapshot; it is not a Git Bundle containing full branches/tags/commit history.
