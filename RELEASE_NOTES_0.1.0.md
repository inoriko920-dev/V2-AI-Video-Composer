# AI Automatic Video Composer 0.1.0

First portable Windows release of the AAVC implementation roadmap.

## Included
- white/blue Qt desktop shell with validated STEP 09 screenshot capture workflow
- DOCX scene import and canonical Axxx asset binding
- SINGLE / DOUBLE layout pipeline
- deterministic ProjectState persistence, undo/redo, autosave and recovery
- 21-effect animation registry with manual/random/AI-compatible selection boundary
- SRT -> ASS subtitle pipeline including style and animation support
- deterministic FFmpeg render plan with documentary-crisp quality settings
- Gemini provider boundary, API-key pool rotation/cooldown and Windows credential-store integration
- preflight validation, background job cancellation and redacted diagnostics bundle
- portable PyInstaller onedir packaging for Windows 11 x64

## FFmpeg policy
FFmpeg is not redistributed inside AAVC 0.1.0. Put an approved `ffmpeg.exe` and `ffprobe.exe` in `tools/ffmpeg/` beside the portable application, or provide them on Windows PATH. This keeps the third-party codec/license decision explicit.

## Security
- no real API key is committed or packaged
- provider/key diagnostics expose references and health state, not raw secrets
- diagnostics redact common API-key and Bearer-token patterns

## Release integrity
The final Windows workflow produces the portable ZIP, SHA256SUMS, release notes, and a source-backup archive from the exact release commit.
