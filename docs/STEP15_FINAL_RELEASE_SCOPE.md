# STEP 15 — Final Release / Backup / Maintenance

Goal: close the Software Factory roadmap with a reproducible Windows 11 x64 final release, explicit FFmpeg distribution policy, backup set, and maintenance contract.

## Final release decisions
- final version: `0.1.0`
- packaging: PyInstaller `onedir` -> portable ZIP
- repository remains the canonical source of truth
- final workflow also creates a source-backup ZIP and SHA-256 checksums
- API keys and user runtime data are never packaged
- FFmpeg/ffprobe are external tools for 0.1.0: app-local `tools/ffmpeg/` or Windows PATH
- AAVC does not auto-download or silently redistribute an unknown FFmpeg build

## Release gate
PASS requires:
- compile, Ruff, strict mypy, cheap pytest
- STEP 09 representative Qt capture/verification
- portable build and foundation smoke
- final ZIP and SHA256SUMS
- source-backup ZIP from exact release commit
- release/maintenance/backup documentation present in the portable/source artifacts

## Post-release
Maintenance follows `MAINTENANCE.md`; backup/recovery follows `BACKUP_AND_RECOVERY.md`.
