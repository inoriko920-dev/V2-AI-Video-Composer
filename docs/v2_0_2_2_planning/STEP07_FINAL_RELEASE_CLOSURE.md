# STEP 07 — v0.2.2 Stable Publication Closure

**Status: COMPLETE / PASS — PUBLISHED AND INDEPENDENTLY VERIFIED.**  
**Publication date:** 2026-10-08 (GitHub timestamp `2026-10-08T04:28:44Z`, 11:28:44 WIB).  
**Repository:** https://github.com/inoriko920-dev/V2-AI-Video-Composer  
**Canonical GitHub Release:** https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/tag/v0.2.2  
**GitHub Release ID:** `406412413`; stable (not draft, not prerelease).  
**Final immutable source/tag SHA:** `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef` (tag `v0.2.2`).

## Official downloads and integrity

| Published asset | Direct download | SHA-256 of published asset |
|---|---|---|
| Windows 11 x64 portable ZIP | [AI-Automatic-Video-Composer-0.2.2-win64.zip](https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/download/v0.2.2/AI-Automatic-Video-Composer-0.2.2-win64.zip) | `80232a96deedff0ee382c42e377999a8f9c5434e075b99c415a41a2e538d07e7` |
| Exact final source ZIP | [AI-Automatic-Video-Composer-0.2.2-source.zip](https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/download/v0.2.2/AI-Automatic-Video-Composer-0.2.2-source.zip) | `ec03dfe339fbc71a4bf199784de9e0a4ff5cb0d69b38399c179c1bc178f30183` |

The release also publishes `BUILD_INFO.txt`, `SHA256SUMS.txt`, `STEP07_FINAL_BUILD_EVIDENCE.txt`, release notes, manifest, user guide, maintenance and backup/recovery docs. **Important:** source ZIP is the exact `git archive HEAD` source snapshot of the final release SHA, not a full `.git` history backup; historical disaster recovery is handled separately by the single-app Git Bundle workflow.

## Exact gate evidence

- Frozen RC source `607fb5b59f6788892b60027d736cf99b8898c6a7`: [RC workflow 37725077066](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37725077066), PASS (795 tests, 5 special-path cases, external FFmpeg 9.0.2, secure portable and checksums).
- Final docs PR #46: CI `37725591668` PASS; CodeQL `37725591744` PASS; Windows user acceptance `37725591704` PASS; backend spike `37725591632` PASS.
- Final source merge SHA `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`: main push CI `37725970462` PASS; CodeQL `37725970445` PASS.
- [Guarded final publish workflow 37727140284](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37727140284): **PASS** for separate CodeQL, real Windows full candidate rebuild, and one-shot publication job.
- Final Windows candidate: **795 passed**, Ruff, mypy, source-secret scan, actual distributable credential scan, FFmpeg 9.0.2 PATH and app-local precedence, PyInstaller portable EXE smoke, actual UI capture, five extracted-portable folder path cases and ZIP SHA-256 re-verification all PASS.
- Publisher downloaded the candidate from the same Actions run, reverified SHA256SUMS, exact BUILD_INFO `release_commit`, `version=0.2.2`, `channel=final-verification`, schema max 4, `animation_contract=advanced-v1`, and FFmpeg reference 9.0.2.
- Publisher confirmed `main` still pointed to the expected final source commit; existing `v0.2.2` tag/release were absent; published v0.2.1 stable tag remained unchanged; newly created `v0.2.2` tag and GitHub Release assets were independently checked.
- Final candidate Actions artifact: ID `11528825413`, `AAVC-0.2.2-STEP07-FINAL-CANDIDATE-APPROVED`, archive digest `sha256:82665ec39bf8c8f101d6ccaebc256a8c529d5b4ad4ce8d40ea209592a3c6a819` (this digest is for the Actions artifact envelope, not either published ZIP).

## Immutable-tag and scope audit

- `v0.2.2` => `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`, exactly the final source.
- `v0.2.1` => `eb94efebf142ba8203dfc3ae3c5fa861222a0926`, preserved.
- `v0.2.0` and earlier stable releases untouched.
- Legacy/original repo `AI-Automatic-Video-Composer` not modified. Only V2 was developed and published.
- v0.2.2 is a maintenance patch preserving the current white/blue UI, 21 native effects, schema v4 and `advanced-v1` contract, FFmpeg final/reference renderer and Gemini provider/credential model.
- FFmpeg binaries are **external-only**, not redistributed in the ZIP; documented PATH/app-local installation required.

## Required fixes completed vs deferred

- W06-A repo/workflow hygiene and verified one-app Git Bundle backup — PASS.
- W06-B real advanced editor schema-v4 controller activation/confirmation — PASS.
- W06-C fail-closed corrupt existing Save/Save As and numbered pre-recovery preservation — PASS.
- W06-D secure deterministic Windows packaging with pinned FFmpeg 9.0.2 reference and source/portable checksums — PASS.
- W06-E all cross-wave regression and release candidate source freeze — PASS.
- STEP07 frozen RC, 5 special-path cases, final rebuild, guarded stable publication and independent tag/asset verification — PASS.
- **GAP-03A remains deferred:** production scheduled autosave and interactive startup Restore/Discard/Cancel flow are *not yet connected to the app runtime*; do not claim automatic recovery UX is available.
- Python security-line reevaluation, setuptools backend alignment, optional Ruff patch and broad dependency refresh remain deferred; no new runtime dependency introduced.
- 10/100/500-scene benchmark checks command construction and should not be described as completed real 500-scene video renders.

## Future handoff rule

**STEP00–STEP07 (v0.2.2 maintenance cycle): CLOSED / PASS.** Future changes must enter a new version's planning process. Never retarget existing v0.2.2/v0.2.1 release tags or replace published assets in place. Treat `v0.2.2` as the stable baseline; a future feature request or deferred GAP-03A requires its own authorized scope and implementation waves.

This is a post-publication documentation change only and does **not** change the frozen `v0.2.2` commit or published release assets.
