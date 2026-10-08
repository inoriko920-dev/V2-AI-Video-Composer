# AI Automatic Video Composer v0.3.0 — Release Candidate Notes

**Status:** RELEASE CANDIDATE / **NOT PUBLISHED**. This is preparation for a
future stable GitHub Release, not a public-download announcement.

**Target:** Windows 11 x64, portable PyInstaller onedir.
**Upgrade baseline:** Stable [v0.2.2](https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/tag/v0.2.2).

## New in 0.3.0: local autosave and project recovery

- **Scheduled autosave for an already-saved project.** During unsaved edits,
  the application schedules a local snapshot without changing the canonical
  Save baseline, clearing the unsaved indicator, or adding Undo/Redo commands.
  Core timing policy: 20-second debounce, 120-second maximum eligibility
  window after the first unsnapshotted edit, 60-second check, and
  30/120/300-second retry delays on failure. A 250-ms Qt timer only checks
  eligibility; it does **not** save to disk every 250 ms.
- **Safe recovery choice on project Open.** The three user-approved Indonesian
  dialogs distinguish a verified candidate, changed/uncertain baseline, and
  unreadable/corrupt candidate. Restore always requires an explicit choice;
  uncertain candidates require a second confirmation within the same modal.
  Cancel/Esc is a conservative no-change action.
- **Byte-level provenance and crash tolerance.** Autosave metadata includes
  bounded SHA-256 digests for the last manual Save and the candidate snapshot,
  and a digest of the project path identity. A crash between the two files
  classifies the candidate as uncertain rather than silently restoring it.
- **Pre-recovery backup before Restore.** A unique numbered backup preserves
  previous saved bytes. Save/Open/Save As/Restore/Discard operations fence
  stale callbacks; errors after writing disk are shown as partial commits,
  never misreported as zero mutation.
- **No repeated false conflicts after successful Restore.** If the retained,
  decoded snapshot and newly saved disk are already byte-identical, reopening
  does not trigger another unnecessary Restore dialog. The forensic candidate
  remains on disk.
- **Safer background processing.** Snapshot IO uses a single serial worker
  fed immutable captured project state. UI-thread ProjectSession/Coordinator
  data is not directly read on the worker thread.

## Compatibility and existing features

- Project schema v3 and advanced-v1 schema v4 are still supported. No new
  schema v5 and no implicit conversion from v3 to v4.
- The existing white/blue editor, 42 frozen UI references, timeline, preview,
  right-side AI controls, Gemini credential model, 21 native effects, and
  external FFmpeg architecture remain intact.
- Python 3.12.10, PySide6 6.11.2 and pinned dependency lock are retained.
- This RC is built from a dedicated source commit and must pass full Windows
  tests, portable EXE launch, screenshot capture, security scan and SHA-256
  validation before a public release can be considered.

## Using autosave responsibly

1. Start by creating and **manually saving** a project `.aavcproj` in a writable
   folder. Autosave is **not available for never-saved projects**.
2. Make edits normally; the app keeps the current session dirty. Continue
   manually saving meaningful milestones—autosave is a supplement, not a
   substitute for Save or an independent backup.
3. If a validated recovery candidate is found when opening a project, select
   Restore, use the saved project, or Cancel. Do not use Restore for a
   corrupted/unreadable candidate.
4. Keep `.autosave`, `.autosave.meta.json` and
   `.pre-recovery[.N].bak` together when troubleshooting. Do not delete them
   merely because a crash occurred.

## Limitations

This is **best-effort local recovery, not a guarantee against power loss,
disk failure, ransomware or an adversarial external file writer**. SHA-256
detects file changes but is not an authenticated signature. The in-process
lock does not coordinate every other application. During a slow or blocked
snapshot write, Save/Open may be delayed or fail closed. Recovery is not an
automatic cloud backup and does not protect an unsaved-new project before its
first manual Save.

## FFmpeg and distribution

FFmpeg/ffprobe are **not bundled** in the ZIP. Install a compatible pair in
`tools/ffmpeg/` beside the portable executable or on your Windows `PATH`.
Acceptance uses reviewed FFmpeg 9.0.2; other builds may differ.

**Do not publish from this branch.** Candidate ZIPs and checksums are CI
artifacts only. A future release requires an exact-source freeze, separate
Windows acceptance and a guarded publisher with narrow permissions.
Published `v0.2.2`, `v0.2.1` and earlier releases remain unchanged.
