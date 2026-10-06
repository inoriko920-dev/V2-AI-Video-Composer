# STEP 14 — Release Candidate & Packaging

Status: **PASS**

Target RC: `AI Automatic Video Composer 0.1.0-rc1` untuk Windows 11 x64.

Implemented and verified:
- version `0.1.0rc1`
- PyInstaller onedir packaging includes resources, schemas, licenses and RC release notes
- packaged GUI executable supports file-based foundation smoke verification
- portable verifier checks smoke marker, required schema/release notes and forbidden secret/user files
- dedicated Windows Release Candidate workflow builds ZIP + SHA256SUMS and uploads an Actions artifact

Validation evidence:
- Release Candidate Windows run #2 (`37150777204`): SUCCESS
- compile: PASS
- Ruff: PASS
- strict mypy: PASS
- cheap pytest: PASS
- Windows PyInstaller onedir build: PASS
- packaged executable portable smoke: PASS
- RC ZIP + SHA256SUMS generation: PASS
- Actions artifact upload: PASS
- workflow artifact: `AAVC-0.1.0-rc1-win64`
- workflow artifact digest: `sha256:b266bb3baf2ac213f3da6968a9edffdd0809b1a74174507b7c56a94a60b66e28`
- inner portable ZIP SHA-256: `c61b245484680972fa93512291541d7f426223801bc3aad524b13db4e93befbf`

Known RC limitation:
- FFmpeg executable binary is intentionally not bundled yet; license/distribution closure remains a STEP 15 release decision.

Gate decision:
- STEP 14 technical gate: PASS
- STEP 14 formal gate: PASS
- project is ready for STEP 15 — Final Release / Backup / Maintenance
