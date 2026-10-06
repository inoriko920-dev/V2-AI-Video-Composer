# Wave J — User-Test Build

Status: **NOT A PUBLIC FINAL RELEASE**

This package is the Windows 11 x64 user-acceptance build for the final V2 release gate.

## What to test

1. Launch `AI Automatic Video Composer.exe` directly from the extracted portable folder.
2. Create or open a real `.aavcproj`.
3. Confirm Scene selection, reorder, resize duration, split, In/Out, markers, zoom, and Undo/Redo.
4. Confirm **Salin Animasi Scene** / **Tempel Animasi Scene** on compatible Scene asset slots.
5. Open Validation Center and verify **Relink / Buka Scene / Impor Media** actions.
6. Save, close, reopen, and confirm project state persists.
7. If Gemini credentials are configured, run Auto (AI), observe progress, and test **Batalkan Pekerjaan Berjalan**.
8. For export, provide an approved FFmpeg/ffprobe build in `tools/ffmpeg/` or Windows PATH, then render a short real project.
9. During render, verify progress/cancel and confirm an existing valid output is not replaced by an invalid staged render.
10. Report any crash, frozen window, missing control, incorrect animation, corrupt project, or failed portable startup.

## Important packaging policy

- FFmpeg/ffprobe binaries are **not bundled** in this user-test ZIP.
- No API keys, `.env`, user cache, logs, recovery files, or credential secrets are included.
- This build does not create or overwrite a public GitHub Release.
- The exact source commit and SHA-256 hashes are included in the outer artifact bundle.

## Acceptance gate

Wave J cannot publish/promote a final V2 release until this user-test package passes the repository release gate **and** user acceptance is explicitly confirmed.
