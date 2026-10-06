# Final Release Manifest — AI Automatic Video Composer 0.1.0

Factory status: **STEP 00–15 COMPLETE**

This manifest intentionally triggers the final Windows release workflow after `STEP15_STATUS.md` was closed as PASS, so the exact source-backup artifact contains the final status record.

Final release contract:
- version: `0.1.0`
- platform: Windows 11 x64
- packaging: PyInstaller onedir -> portable ZIP
- source backup: exact release commit via `git archive`
- integrity: SHA-256 for portable and source archives
- FFmpeg policy: external approved build from app-local `tools/ffmpeg/` or Windows PATH; no bundled binary in 0.1.0
- secrets: no raw API key in source or release artifact
- maintenance: `MAINTENANCE.md`
- recovery: `BACKUP_AND_RECOVERY.md`
- release notes: `RELEASE_NOTES_0.1.0.md`

The GitHub Actions result for this manifest commit is the canonical final release evidence.
