# V2 AI Video Composer — Planning Source of Truth

Status: **PLANNING ONLY — APPLICATION IMPLEMENTATION NOT STARTED**

## Repository preservation rule

- inoriko920-dev/AI-Automatic-Video-Composer is a **read-only legacy reference** for this V2 project.
- All V2 development, experiments, dependency spikes, UI work, testing changes, and release work must occur only in inoriko920-dev/V2-AI-Video-Composer.
- The V2 baseline was imported from legacy main commit 7d77fc9f724d359c7da6c4796dffce5104740952.
- The imported V2 snapshot was verified with the exact same Git root tree SHA: 7abd82b4a69428a0b1bd25a8d992f402cb0a2ff8.
- V2 migration commit: 835130da71b5a2114100ada903f524dd926a068a.

## Required reading order

Read V2_MASTER_PLANNING_INDEX.docx, then STEP 00 through STEP 13 in order. STEP 13 defines the implementation waves and gates.

## Coding gate

**Do not begin major application coding merely because the planning documents exist.** The STEP 13 CODING GATE also requires planning review/approval. Until that gate is explicitly PASS, changes in this directory are documentation/source-of-truth work only.

## Mature-component direction

The plan keeps the proven FFmpeg CLI path as the reference/fallback backend while evaluating mature components only behind adapters. openshot-qt application/UI code is not to be copied into V2. libopenshot, MLT, PyAV, and OpenTimelineIO are evaluated only for clearly bounded roles with Windows packaging, regression, and licensing gates.

## Regenerating DOCX

The canonical planning data and generator live in _generator/. GitHub Actions regenerates the DOCX files when the generator or planning data changes. The generator is documentation infrastructure; it is not application runtime code.
