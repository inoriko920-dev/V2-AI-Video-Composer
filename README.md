# V2 AI Video Composer

## Current stable release — v0.3.0 (8 October 2026)

**v0.3.0 is published and independently verified.** [Download the official Windows 11 x64 portable ZIP](https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/download/v0.3.0/AI-Automatic-Video-Composer-0.3.0-win64.zip) or [open the stable Release and its checksum assets](https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/tag/v0.3.0).

- Frozen published source/tag: `d5a085fe239763e469ad30e91f526179fe8b2595`; all nine public assets checked, including both ZIP SHA-256 values.
- Version 0.3.0 adds guarded **local autosave and project recovery** for projects that have been manually saved at least once. The existing white/blue editor and approved UI references remain unchanged.
- Windows exact-source verification, **907 tests**, portable EXE launch, five-path matrix, FFmpeg modes and CodeQL: PASS.
- **FFmpeg/ffprobe are external dependencies**. Follow the portable package instructions to install them beside the EXE or on PATH.
- Historical `v0.2.2` and older releases remain available; do not replace their tags or assets.
- Publication evidence and the remaining **manual-on-Windows** acceptance checklist: [post-release closure](docs/v2_0_3_0_planning/10_POST_RELEASE_PUBLICATION_CLOSURE.md).

The earlier version/wave details below are retained as **historical snapshots**, not authoritative current release status.

This repository is the **only writable development target for V2**.

- Legacy repository: `inoriko920-dev/AI-Automatic-Video-Composer` — **read-only reference; do not modify**.
- Imported legacy baseline commit: `7d77fc9f724d359c7da6c4796dffce5104740952`.
- Imported baseline Git root tree: `7abd82b4a69428a0b1bd25a8d992f402cb0a2ff8`.
- V2 planning source of truth: `docs/v2_planning/`.
- Current implementation status and exact next action: `V2_IMPLEMENTATION_STATUS.md`.
- STEP 13 CODING GATE: **PASS** on 2026-10-07 after planning review and explicit user continuation.
- Wave A: **COMPLETE** — source-of-truth lock + baseline CI passed with no functional application changes.
- Wave B: **COMPLETE** — backend capability contracts added; FFmpeg behavior/dependencies unchanged.
- Wave C: **COMPLETE** — staged-output validation, render cancellation/progress, FFmpeg capability probe, and benchmark harness passed CI.
- Wave D: **COMPLETE** — schema v3 keyframe data model and backward migration passed CI; existing effects remain canonical.
- Wave E: **COMPLETE** — foundational X/Y position, scale, and rotation keyframes passed preview/final parity gates.
- Wave F: **COMPLETE** — transactional manual editing, Scene animation copy/paste, and validation repair actions passed CI.
- Wave J: **COMPLETE** — stable `v0.2.0` is published and verified.

The historical README copied from the legacy repository is preserved below as baseline documentation.

---

# AI Automatic Video Composer

Windows desktop application for composing narrative/infographic videos from scene DOCX + canonical `Axxx.png` assets.

## Project status

**Software Factory STEP 00–15: COMPLETE.**

- STEP 00–08: product, architecture, repository and CI foundation complete
- STEP 09: **PASS** — actual Windows/PySide6 screenshots captured and verified in CI
- STEP 10: minimum end-to-end vertical slice complete
- STEP 11: feature implementation waves complete; Ruff, strict mypy and pytest gates pass
- STEP 12: external/provider integration complete
- STEP 13: hardening and QA complete
- STEP 14: **PASS / Release Candidate Ready**
- STEP 15: **PASS / Final Release Ready**

Historical v0.2.1 checkpoint (superseded by v0.3.0): **0.2.1**. Earlier `v0.2.0`, `v0.1.1`, and `v0.1.0` remain frozen.

Archived 0.2.1 release line: **0.2.1 published / verified** at `eb94efebf142ba8203dfc3ae3c5fa861222a0926` (not the latest release).

- Stability-hardened runtime source: `9ce7d3c3125947c69e7dcf357f6ecbbc6707fee7`
- Post-merge CI run `37429362040`: **PASS**
- Post-merge CodeQL run `37429362044`: **PASS**
- Windows portable packaging run `37429446908`: **PASS**
- Actions artifact ID: `11396573064`
- Portable ZIP SHA-256: `6d9f3d57dd5c8ba47a18bb65a56e5c26ce8cac1962bacfee0ffff8c9efdfbe52`
- Portable smoke/content verification: **PASS**
- Stability hardening includes atomic render output, tolerant external-process decoding, atomic narration replacement, future-schema rejection, malformed-DOCX error boundaries, blocking application close while Render/Auto AI work is active, strict rejection of empty/malformed SRT imports, and safe handling of corrupt Windows Credential Manager blobs.
- Published `v0.1.1` remains frozen and unchanged.

## Official release 0.1.1

GitHub Release **`v0.1.1` is published and verified**.

- Release source: `release/0.1.1`
- Release commit: `a6515ee7c4c9cda88a0c8aa93892c36eaf292d2e`
- Canonical publication workflow: `Maintenance Release Windows 0.1.1` run `#1` / `37181599863`
- Windows portable ZIP SHA-256: `84ad8cc93f055cb95fc2624511a9eecd541505627628090c277a048e5e8495b4`
- Source backup ZIP SHA-256: `a5a00b196e76d34684deef97b9dc605b748e1a32f2f92fe6f761c25b13f720bb`

0.1.1 is a maintenance-only patch. It restores the actual app-local FFmpeg slot at `tools/ffmpeg/` beside `AI Automatic Video Composer.exe`, strengthens portable verification, removes the redundant `_internal/tools/ffmpeg/README.md` copy, and aligns package/runtime version metadata. FFmpeg and ffprobe remain external dependencies and are not redistributed by AAVC.

The published bundle includes the portable Windows ZIP, exact source ZIP, release notes, maintenance policy, backup/recovery policy, `BUILD_INFO.txt`, and `SHA256SUMS.txt`. The checksum file and portable ZIP structure were independently verified.

## Historical release 0.1.0

The original final-release baseline remains published and unchanged:

- Tag: `v0.1.0`
- Release source: `release/0.1.0`
- Release commit: `92da28bbb8177b11b3d09f000a4e7e01d389ccc5`
- Windows portable ZIP SHA-256: `c3e4f92656aefd3d57329627c52b8e057d2f8cac5a0a757471b90cb1d68915e8`
- Source backup ZIP SHA-256: `1264b1dc483932b496acf87dee21c93f92d4e1b222aa37ca2284fbf99b9df328`

The portable binary is generated by GitHub Actions and is intentionally not committed as a large binary into the source tree.

Historical STEP 15 factory-gate evidence remains recorded in `STEP15_STATUS.md` and `FINAL_RELEASE_MANIFEST.md`; maintenance release evidence is recorded in the post-release state and release documentation.

## Technology baseline

- Python 3.12 x64
- PySide6 / Qt Widgets
- Modular monolith
- `presentation -> application -> domain`
- FFmpeg / ffprobe media pipeline
- ASS/libass subtitle pipeline
- PyInstaller onedir portable packaging
- Windows GitHub Actions quality/release validation

## Implemented capabilities

- Prompt-1 DOCX scene parsing and canonical `Axxx` asset binding
- SINGLE / DOUBLE layout contracts
- versioned `.aavcproj` ProjectState persistence
- undo / redo and recovery snapshots
- canonical 21-effect visual animation registry
- deterministic random animation with seed, cooldown and lock awareness
- subtitle styling and subtitle animation compilation to ASS
- word-timing fallback
- FFmpeg deterministic render pipeline
- Documentary Crisp render-quality profile
- validation and asset relink workflow
- external AI/provider boundary and Gemini integration
- key-pool / secure Gemini credential management (slots 1–100)
- real microphone narration recording into project history
- bounded Gemini Auto (AI) for native render-backed animation assignment
- background render/Gemini execution through the canonical JobManager
- Windows portable packaging and final-release/test-build gates

## UI reference and parity

The product design is based on **42 canonical frozen visual references (`UI-001` through `UI-042`)** with a 1920×1080 desktop reference viewport.

The implementation uses real Qt widgets and follows the normalized UI Freeze rules: preserve the white/blue professional visual direction and feature coverage, while correcting accidental overlaps, inconsistent spacing and other image-generation artifacts.

STEP 09 is formally closed after actual Windows/PySide6 screenshot capture and CI verification. See `STEP09_STATUS.md` and `docs/UI_FREEZE.md`.

## User guide

Untuk cara menjalankan versi portable, menyiapkan Scene DOCX dan aset canonical, memahami kebutuhan FFmpeg/ffprobe, fitur UI yang aktif, serta batas produk yang sengaja dipertahankan, lihat:

- `docs/USER_GUIDE.md`

Panduan tersebut juga membedakan frozen release `v0.1.1` dari completed post-release 0.2 source/test-build line pada `main`.

## Canonical local commands (PowerShell)

```powershell
./scripts/dev.ps1
./scripts/test.ps1
./scripts/package.ps1
./scripts/verify_portable.ps1
```

## Release and maintenance

For release evidence, publication, rollback rules and maintenance policy, see:

- `FINAL_RELEASE_MANIFEST.md`
- `STEP14_STATUS.md`
- `STEP15_STATUS.md`
- `RELEASE_NOTES_0.1.1.md`
- `docs/RELEASE_PUBLISHING.md`
- `docs/USER_GUIDE.md`
- `MAINTENANCE.md`
- `BACKUP_AND_RECOVERY.md`
- `docs/`

Historical 0.2.x note: the 0.2.1 final source added advanced-v1; published `v0.2.0` remains immutable. The current stable release is **v0.3.0**.

Archived v0.2.1 release state: **published / verified; Windows final gate, CI, CodeQL, portable packaging, packaged-EXE launch, checksum verification, and guarded publication PASS**. Current v0.3.0 evidence is linked above.


## License

AI Automatic Video Composer project source is licensed under the **MIT License**. See `LICENSE`.

Third-party dependencies retain their own licenses. FFmpeg/ffprobe are external dependencies and are not redistributed by AAVC.


## V2 implementation wave status
- Wave F: **COMPLETE** — transactional manual editing and validation UX passed CI.
- Wave G: **COMPLETE** — Gemini background cancellation/progress and secret-free key-pool health diagnostics passed CI.
- Wave H: **COMPLETE** — frozen-reference UI parity, truthful action state, and focus/disabled interaction polish passed CI + screenshot gates.
- Wave I: **COMPLETE** — PyAV Windows feasibility spike passed; no optional backend was promoted into runtime.
- Wave J: **COMPLETE** — 21/21 effects are native and stable `v0.2.0` is published / verified.


## Wave I dependency gate
Wave I is complete. PyAV 19.0.1 passed the isolated Windows/Python 3.12 feasibility
spike, but it was deliberately **not** added to the application runtime because no
measured product need currently justifies the additional dependency/portable footprint.
FFmpeg/ffprobe CLI remains the production reference/fallback. libopenshot/MLT remain
deferred pending a concrete capability need and native packaging/license evidence.


## V2 0.2.0 release-candidate gate
Wave J is active. The V2 source is moving to `0.2.0rc1` for a Windows portable
user-test build. This gate produces reproducible ZIP/checksum/source artifacts only;
it does not create or replace a GitHub Release. Final `v0.2.0` publication remains
blocked on RC user acceptance and final release validation.


### 0.2.0rc1 automated RC gate
The first Wave J RC gate passed on PR #12: Windows CI, CodeQL, 605 regression tests,
STEP09 screenshots, PyInstaller onedir, packaged foundation smoke, SHA-256 bundle
generation, and Actions artifact upload all passed. Final v0.2.0 publication remains
blocked until user-test acceptance.


### V2 0.2.0rc1 user-test status
Automated RC gates are **PASS** and PR #12 is merged. The Windows portable
`0.2.0rc1` build is ready for user testing. Final `v0.2.0` is intentionally not
published until user acceptance confirms there is no blocker.


### 21-effect animation blocker closure
PR #13 is merged. The canonical 21-effect registry is now fully included in the native
preview/FFmpeg capability matrix. The refreshed 0.2.0rc1 gate passed Windows CI,
CodeQL, 627 regression tests (1 deselected), all 8 STEP09 screenshots, PyInstaller
onedir packaging, portable smoke/content/secret verification, and RC artifact upload.
Use refreshed user-test artifact ID `11459479975`; the earlier RC artifact is superseded
for animation testing. Advanced opacity/crop/blur/shadow/glow/mask keyframe tracks and
bezier/velocity/overshoot remain explicitly outside the production-ready keyframe set.


### V2 0.2.0 stable release
`v0.2.0` is published and verified at commit `c6ad75308d302cd816301a2a7a34ebe7eb4148a7`.
The final Windows workflow, CodeQL, automated user acceptance, 21-effect real FFmpeg
render, portable verification, packaged-EXE UI launch, and SHA-256 integrity checks all
passed. The release/tag is immutable; future fixes must use a new version.


### V2 0.2.1 advanced-animation release

The 0.2.1 line adds schema-v4 / advanced-v1 animation editing for opacity, four-side
crop, blur, shadow, glow, mask progress, and Bezier/velocity/overshoot semantics while
preserving schema-v3 behavior until the user explicitly commits an advanced edit.
The accepted 0.2.1rc1 Windows gate passed 761 technical tests, real FFmpeg validation,
portable packaging, packaged-EXE UI launch, 10/100/500 Scene benchmark evidence, CI,
CodeQL, and checksum reproducibility. Stable `v0.2.1` is now published and verified at
`eb94efebf142ba8203dfc3ae3c5fa861222a0926`. The release/tag is immutable; the former
publisher workflow is retained only as a read-only historical verifier. `v0.2.0` remains
published and unchanged.
