# AI Automatic Video Composer v0.2.2 — Maintenance Release

**Platform:** Windows 11 x64 portable (PyInstaller onedir / ZIP).  
**Update line:** maintenance and reliability update from published v0.2.1.

## What changed in 0.2.2

- **Advanced Animation UI correctness (W06-B).** The existing Asset Motion dialog receives the correct project schema version. Applying a keyframe edit follows the canonical advanced-activation command, requires explicit acknowledgement where needed and keeps Undo/Redo atomic. A rejected activation does not mutate the project.
- **Project Save / Recovery file safety (W06-C).** Save and Save As refuse to overwrite malformed or unreadable existing projects. Repeated recovery preserves each pre-recovery version with numbered, exclusive backups rather than replacing an older backup. Failed backup/restore operations clean up temporary files.
- **Repository and build safety (W06-A).** Workflow permissions were constrained, active Actions SHA-pinned, historical generators made read-only and V2-only backup corrected with verified Git Bundle history.
- **Portable Windows packaging (W06-D).** Opportunistic UPX was disabled. Built portable files are inspected for supported credential patterns and forbidden runtime files. The FFmpeg/ffprobe 9.0.2 validation reference is enforced, PATH and app-local resolution are tested, and the ZIP does not bundle FFmpeg binaries.
- **RC regression (W06-E / STEP 07).** Cross-wave CI/CodeQL/Windows gates passed on the consolidated source. Frozen RC source `607fb5b59f6788892b60027d736cf99b8898c6a7` passed 795 nonvisual technical tests; portable EXE build/smoke, UI capture, artifact scan and checksum checks; five extracted-portable path cases (ASCII, spaces, apostrophe, Unicode and deeper paths) passed.

## Compatibility

- Maximum project schema: **v4**, with `animation_keyframe_contract=advanced-v1`.
- A legacy v3 project is not promoted simply by opening, previewing, rendering or saving without an actual advanced edit.
- The existing **21 native visual effects** remain supported and covered by the real FFmpeg acceptance suite.
- The current white/blue PySide6 interface, Gemini provider model and final FFmpeg rendering architecture are retained.
- No new runtime dependency was added.

## FFmpeg installation

AAVC **does not redistribute FFmpeg**. Place an approved `ffmpeg.exe` and `ffprobe.exe` in the portable folder's `tools/ffmpeg/` slot, or install them on Windows PATH. App-local copies take precedence. Automated qualification for this maintenance release used the **9.0.2** reference build; different builds may offer different codec/filter capabilities and require independent validation. See `tools/ffmpeg/README.md` in the ZIP.

## Important limitations

The underlying RecoveryManager supports safely creating/restoring snapshots, but **automatic scheduled autosave and the user-facing Restore/Discard/Cancel startup flow are not connected to the application**. That separate product feature (GAP-03A) remains deferred; this update specifically hardens file-level recovery safety.

Command-generation benchmarks for 10/100/500 scenes are not claims that 500-scene video rendering completed in real time. Final release qualification includes real render integration for the 21-effect path.

## Integrity and installation

Download the release's Windows portable ZIP and verify its SHA-256 against the supplied `SHA256SUMS.txt`. Extract the entire ZIP to a writable folder without renaming or deleting the `_internal` directory. Read `USER_GUIDE.md` for getting started.

A separate exact-source ZIP, `BUILD_INFO.txt`, release manifest, provenance and maintenance/backup guidance accompany the Windows archive. Published earlier v0.2.0 and v0.2.1 tags are immutable.
