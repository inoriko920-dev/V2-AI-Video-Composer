# K8 — Windows Acceptance / v0.2.1 RC Implementation Result

Status: **PASS**

Validated RC source commit:
`603039156a46d34935f5092b477b58eb74042e28`

RC version:
`0.2.1rc1`

## Implemented
- Runtime version and package metadata moved from frozen `0.2.0` to RC-only `0.2.1rc1`.
- Added `RELEASE_NOTES_0.2.1_RC1.md`.
- Added `docs/V2_0.2.1_RC1_USER_TEST.md`.
- Added dedicated `.github/workflows/v2-0.2.1-rc.yml`.
- The RC workflow checks out the exact PR-head/source commit instead of a temporary merge ref.
- Portable packaging now ships the 0.2.1 RC release notes.
- Portable verification requires the 0.2.1 RC release notes and preserves the existing secret/runtime-data exclusions.
- Final `v0.2.1` publication is explicitly blocked.

## T0–T6 proof
- T0 static/dependency: **PASS**
  - no-secret scan;
  - pinned dependency install;
  - pip dependency graph;
  - compile;
  - Ruff;
  - strict mypy;
  - CodeQL.
- T1 deterministic/unit regression: **PASS**
  - CI cheap suite: **716 passed, 45 deselected**.
- T2 real FFmpeg: **PASS**
  - FFmpeg 9.0.2 + ffprobe on Windows;
  - K1–K6 real-render/parity tests included in the full technical suite;
  - all-21-effect and Selection In/Out regressions remain green.
- T3 integration acceptance: **PASS**
  - full technical Windows suite: **761 passed**.
- T4 portable/packaged: **PASS**
  - PyInstaller onedir build;
  - portable foundation/content/secret verification;
  - packaged EXE launch and real UI capture.
- T5 performance/parity: **PASS**
  - advanced property performance/parity gates from K1–K6 remain green;
  - 10/100/500 Scene command-build benchmark generated successfully.
- T6 release reproducibility: **PASS**
  - exact source commit recorded;
  - portable ZIP + exact-source ZIP generated;
  - SHA-256 generated and re-verified in the same Windows job;
  - BUILD_INFO and RC gate evidence included in the candidate bundle.

## Gate evidence
All gates below tested the same RC source commit:
`603039156a46d34935f5092b477b58eb74042e28`

- CI run `37640175933`: **PASS**
  - 716 passed, 45 deselected;
  - 8 frozen STEP09 captures PASS;
  - STEP09 artifact `11491507122`;
  - STEP09 artifact digest `sha256:12c0ef06081194cb01f169fd236aee881e273811518c6e966dd3009a2f8260cb`.
- V2 Automated User Acceptance run `37640175991`: **PASS**
  - full technical suite: **761 passed**;
  - FFmpeg 9.0.2;
  - portable build/verification PASS;
  - packaged EXE launch/capture PASS;
  - acceptance artifact `11492360501`;
  - acceptance artifact digest `sha256:5bf225c536b3b0727dab91b837f4a712b9064ddc3cf6d844934510156966cd68`.
- CodeQL run `37640175822`: **PASS**.
- Optional Backend Spike run `37640175960`: **PASS**.
- V2 0.2.1 RC Gate run `37640176055`: **PASS**.
  - exact-source identity PASS;
  - RC version verification PASS;
  - 10/100/500 Scene benchmark PASS;
  - 8 STEP09 screenshots PASS;
  - portable build/verification PASS;
  - packaged EXE UI launch PASS;
  - portable/source checksum re-verification PASS.

## RC artifacts
Candidate bundle:
- artifact ID: `11491667304`
- artifact digest:
  `sha256:86ab9c85558dd664d768a761920b7ef393ef0b7f0dfde109c6c4b990f1333498`

STEP09 RC evidence:
- artifact ID: `11491667310`
- artifact digest:
  `sha256:0559365be6ce666aa2292cc760581045757b638547c0e04fa1ecd2caeeb84439`

Inside the candidate bundle:
- `AI-Automatic-Video-Composer-0.2.1-rc1-win64.zip`
  - SHA-256:
    `06a05c1e956a1510a7e9cb7e4b21b6825414bf4ddb21ee8ba69a44a21a6576a1`
- `AI-Automatic-Video-Composer-0.2.1-rc1-source.zip`
  - SHA-256:
    `8fc324756ad45c712777130303429a3229980e47982094a90cad194163f220aa`
- `BUILD_INFO.txt`
- `SHA256SUMS.txt`
- `RC_GATE_EVIDENCE.txt`
- `RELEASE_NOTES_0.2.1_RC1.md`
- `V2_0.2.1_RC1_USER_TEST.md`
- `MAINTENANCE.md`
- `BACKUP_AND_RECOVERY.md`
- `render_benchmark.json`
- packaged-EXE UI capture.

## Scope discipline
K8 did NOT:
- merge RC source to `main`;
- create or move a `v0.2.1` tag;
- publish a final GitHub Release;
- move/modify immutable `v0.2.0`;
- change the legacy repository;
- add a new runtime dependency;
- redesign the frozen main UI.

Draft PR #27 was used only as a CI/acceptance/RC packaging trigger and was closed without merge.

## K0–K8 closure
K0 through K8 are now **PASS** on the v0.2.1 development line.

## Next exact action
**Final v0.2.1 Release Gate — NOT STARTED**

A later turn may prepare and run the dedicated final v0.2.1 workflow from the accepted
final source. It must repeat the mandatory gates and may publish `v0.2.1` only after
that final gate passes. Do not alter `v0.2.0`.
