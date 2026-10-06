# AI Automatic Video Composer 0.1.0-rc1

Release Candidate 1 untuk Windows 11 x64.

## Yang sudah tersedia
- UI desktop PySide6 dengan workflow Home, proyek baru, editor, SINGLE/DOUBLE, subtitle, ekspor dan validation center.
- Import scene DOCX dan binding Asset ID `Axxx`.
- ProjectState versioned JSON, autosave/recovery, undo/redo dan relink aset.
- Layout SINGLE/DOUBLE dan timeline dasar.
- Registry 21 animasi visual dengan Manual / Random deterministic / AI-ready contract.
- Subtitle SRT ke ASS/libass, style dan animasi subtitle.
- Render FFmpeg 1920x1080 dengan preset Documentary Crisp.
- Gemini provider boundary, key pool hingga 100 credential references, cooldown/failover dan Windows Credential Manager boundary.
- Render preflight, background job cancellation dan diagnostic redaction.

## Batasan RC1
- Binary FFmpeg belum dibundel ke ZIP ini; `tools/ffmpeg/README.md` tetap menjadi gate lisensi/distribusi. Runtime render membutuhkan FFmpeg yang tersedia sesuai konfigurasi sampai keputusan bundling final ditutup.
- Live Gemini smoke test tidak dijalankan di CI karena CI tidak menyimpan API key pengguna.
- Ini Release Candidate, bukan release final. STEP 15 masih menangani final release, backup dan maintenance.

## Keamanan
Tidak ada API key, `.env`, recovery user, cache user, atau log user yang boleh berada di artifact portable.
