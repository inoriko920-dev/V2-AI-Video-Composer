# AI Automatic Video Composer 0.2.0-rc1

Release Candidate V2 untuk Windows 11 x64. Build ini dibuat untuk user test sebelum
rilis final 0.2.0 dan **bukan** GitHub Release final.

## Sorotan V2

- project schema v3 dengan migrasi eksplisit v1 -> v2 -> v3 dan backup pre-migration;
- render FFmpeg lebih aman dengan staged-output validation, progress, cancellation,
  cached capability probe, dan benchmark coverage;
- keyframe production-ready untuk position X/Y, scale, dan rotation dengan preview /
  final-render parity;
- timeline/manual editing lebih aman melalui transaksi atomic, batch duration,
  animation copy/paste, Undo/Redo, In/Out, marker, snap, zoom, dan navigator;
- Validation Center dapat Relink, membuka Scene bermasalah, dan mengarahkan kembali
  ke impor media;
- Gemini Auto berjalan sebagai background job, dapat dibatalkan, dapat failover hingga
  100 credential slot, dan diagnostics key-pool tidak menyimpan secret;
- UI frozen-reference dipertahankan dengan action-state/focus/disabled polish;
- PyAV 19.0.1 sudah diuji sebagai dependency spike tetapi **tidak** dimasukkan ke runtime;
  FFmpeg/ffprobe CLI tetap menjadi reference/fallback media toolchain.

## User-test yang perlu diperiksa

1. aplikasi dapat dibuka dari folder portable tanpa Python terpasang;
2. buat/buka/simpan project lalu tutup dan buka kembali;
3. import DOCX Scene + aset, pilih Scene, ubah durasi, Undo/Redo;
4. copy/paste animasi antar Scene yang memiliki jumlah slot aset sama;
5. preview keyframe position/scale/rotation dan lakukan render pendek;
6. cek Validation Center pada file aset/media yang sengaja dipindahkan;
7. jalankan Auto (AI) bila Gemini credential tersedia, lalu uji cancel;
8. render full project dan Selection In/Out;
9. pastikan tidak ada crash ketika menutup app saat render/AI aktif.

## Batasan RC

- FFmpeg/ffprobe binary tidak dibundel; gunakan app-local `tools/ffmpeg/` atau PATH;
- provider AI hanya Gemini dan credential tetap disimpan melalui Windows Credential Manager;
- opacity/crop/blur/shadow/glow/mask keyframe serta bezier/velocity/overshoot belum
  diklaim production-ready;
- AAVC tetap compositor Scene-focused, bukan NLE multitrack umum.

## Keamanan

Portable/source bundle tidak boleh berisi API key, .env, private key, autosave/recovery
user, cache, atau log runtime. Release final 0.2.0 tidak boleh dipublikasikan sebelum
RC user-test dan final release gate dinyatakan PASS.
