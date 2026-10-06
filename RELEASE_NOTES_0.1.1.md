# AI Automatic Video Composer 0.1.1

Maintenance patch for the 0.1.x release line.

## Fixed

- Restored the documented app-local FFmpeg slot at `tools/ffmpeg/` beside `AI Automatic Video Composer.exe` in the portable Windows package.
- Portable verification now requires that exact root FFmpeg slot instead of accepting an internal PyInstaller data copy.
- Removed the redundant `_internal/tools/ffmpeg/README.md` packaging path.
- Aligned package/runtime version metadata with the maintenance release version.

## Compatibility

- No project-schema breaking change.
- No user-visible feature expansion.
- Existing 0.1.0 project files remain on the same compatible 0.1.x line.
- FFmpeg and ffprobe remain external dependencies and are not redistributed by AAVC. Users may place approved binaries in `tools/ffmpeg/` beside the portable app or provide them on system PATH.

## Validation

The release gate requires compileall, Ruff, strict mypy, cheap pytest, representative STEP 09 UI screenshot verification, Windows PyInstaller onedir packaging, portable smoke verification, release-content checks, and SHA-256 generation.

Primary maintenance issue: #9.
