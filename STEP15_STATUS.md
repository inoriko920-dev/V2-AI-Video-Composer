# STEP 15 — Final Release / Backup / Maintenance

Status: **PASS**

Final version: `0.1.0`

Completed:
- final release notes, maintenance policy, and backup/recovery policy
- explicit FFmpeg/ffprobe distribution decision: not redistributed in 0.1.0; resolved from app-local `tools/ffmpeg/` or Windows PATH
- runtime media-tool resolver with deterministic tests
- final PyInstaller portable content contract
- final Windows workflow producing portable ZIP, source-backup ZIP, BUILD_INFO and SHA256SUMS
- representative STEP 09 Qt screenshot capture and verification
- portable foundation smoke and release-content validation

Gate evidence:
- Final Release Windows run #3: **SUCCESS**
- workflow run ID: `37151744590`
- validated commit: `2ed9407ca4e2679135547b2021abee11943ca18b`
- artifact: `AAVC-0.1.0-final-win64`
- artifact digest: `sha256:3d9c6158640d45e30fb48f2bbfbb7b26fbbcce82d607a248e793f189f1f1d362`

Software Factory STEP 00–15 is now complete. A final manifest commit will rebuild the same release gate with this PASS record included in the exact source-backup snapshot.
