# V2 v0.3.0 — Frozen Main Source Candidate Verification

**Verified on:** 8 October 2026 (WIB). **Result: PASS / NON-PUBLISHED RC ONLY**.  
**Main frozen source SHA:** `5c29d162982e5bbcff2c9263c265ba84c84bf886`.  
**Read-only workflow:** [run 37767700585](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37767700585), SUCCESS.  
**Workflow artifact:** ID `11547255962`, `AAVC-0.3.0-FROZEN-MAIN-NOT-PUBLISHED`, envelope digest `sha256:84ab740c7b9693159b6a63996bcab96f1732307d3f49482171b029eaf5b254c2`, 65,952,841 bytes. **The envelope digest is not the source/portable ZIP hash.**

## Why this supplemental verification was necessary

STEP07 RC preparation PR #62 was merged into main as `5c29d162982e5bbcff2c9263c265ba84c84bf886`, but its first passing non-published candidate Actions run `37766195762` referenced pre-merge PR SHA `5401919588711ec01a05149d1d02f32edbd6d74a`. The frozen-main branch-specific verification workflow explicitly checks out **exact main SHA** before running tests and `git archive HEAD` packaging; it does not publish or alter main.

## Final candidate contents independently downloaded and verified

| Item | SHA-256 | Bytes |
|---|---|---:|
| `AI-Automatic-Video-Composer-0.3.0-win64.zip` | `17ac952daa0656808f5733bb080926c1564d3dd8d1f2ed8ef863578d324fc2f5` | 62,263,000 |
| `AI-Automatic-Video-Composer-0.3.0-source.zip` | `d26e753fac039a7595a0593062efdd3bcd55aa8ba249463041474d369c317971` | 3,886,773 |

- Top-level Actions ZIP, embedded Windows ZIP and embedded exact-source ZIP CRC: **PASS**.
- Recomputed SHA256SUMS for both nested ZIPs: **PASS**; match published-within-artifact `SHA256SUMS.txt`.
- `BUILD_INFO.txt`: `version=0.3.0`, `release_commit=5c29d162982e5bbcff2c9263c265ba84c84bf886`, `schema_max=4`, `animation_contract=advanced-v1`, `publication_status=NOT_PUBLISHED`, external FFmpeg 9.0.2 reference.
- Portable package includes root EXE, `tools/ffmpeg/README.md`, release notes 0.3.0 and **does not include ffmpeg.exe/ffprobe.exe**.
- Exact-source ZIP includes `src/aavc/presentation/windows/recovery_main_window.py`, STEP07 documentation, `src/aavc/__init__.py` version 0.3.0.
- Windows workflow finished SUCCESS: frozen-source SHA, previous stable immutable tag, dependency pins, source secret scan, compile/Ruff/strict mypy, full nonvisual pytest, portable EXE/actual UI launch, five path cases (ASCII, spaces, apostrophe, Unicode, depth), FFmpeg external and app-local precedence, archive/checksum verification.
- `main` still points to `5c29d162982e5bbcff2c9263c265ba84c84bf886`; official `v0.2.2` tag remains `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.
- **No official GitHub v0.3.0 Release/tag has been published.**

## Gate and next action

**Frozen-main RC verification: PASS. Public release gate: HOLD.** The ZIPs are for trial only. This verification source and evidence live on a dedicated branch to avoid modifying the frozen `main` SHA. A separate explicit release authorization is required before a guarded publisher can create `v0.3.0` tag and GitHub Release with independent after-publication hash verification. Never overwrite any existing tags or previous stable assets.

Do not describe the source ZIP as a 100% Git history backup; it is `git archive HEAD` without .git history. Autosave is best-effort local saved-project recovery, not a zero-data-loss guarantee.
