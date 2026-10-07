# AI Automatic Video Composer 0.2.0

Rilis stabil V2 untuk Windows 11 x64. Versi ini merupakan hasil dari release-candidate
0.2.0rc1 yang telah melewati automated Windows user acceptance, real FFmpeg rendering,
portable packaging, CI, dan CodeQL.

## Sorotan utama

- **21/21 efek animasi canonical** sekarang memiliki jalur native preview + FFmpeg render.
- Project schema v3 dengan migrasi eksplisit v1 -> v2 -> v3 dan backup sebelum migrasi.
- Keyframe production-ready untuk position X/Y, scale, dan rotation dengan easing dasar
  serta parity preview/final render.
- Timeline/editor lebih aman: Undo/Redo, reorder, resize duration, split Scene, marker,
  magnetic snap, zoom/navigator, In/Out, dan Selection render.
- Copy/Paste Animasi Scene memetakan slot aset secara aman dan melindungi assignment locked.
- Validation Center mendukung Relink, Buka Scene, dan Impor Media untuk issue yang relevan.
- Gemini Auto berjalan di background, dapat dibatalkan, mendukung failover sampai 100 slot
  credential, dan tidak menaruh raw API key di project/log/status.
- Render FFmpeg memakai staged-output validation, progress/cancellation, ffprobe verification,
  dan atomic replacement untuk mengurangi risiko output rusak.
- Windows portable dibangun dengan PyInstaller onedir dan diverifikasi melalui packaged-EXE
  smoke/UI launch.

## Bukti acceptance sebelum final

- Automated Windows User Acceptance: PASS.
- Full technical suite: **630 tests PASS**.
- Real FFmpeg render seluruh 21 efek: PASS.
- Real Selection In/Out render: PASS.
- Packaged EXE launch + UI capture: PASS.
- CI: PASS.
- CodeQL: PASS.

## Batas kemampuan yang tetap eksplisit

- FFmpeg/ffprobe binary tidak dibundel. Gunakan slot app-local `tools/ffmpeg/` atau PATH.
- Provider AI yang didukung saat ini adalah Gemini; credential disimpan melalui Windows
  Credential Manager.
- Keyframe opacity/crop/blur/shadow/glow/mask serta bezier/velocity/overshoot belum diklaim
  production-ready.
- AAVC tetap compositor berbasis Scene, bukan pengganti NLE multitrack umum.

## Kompatibilitas project

Project v1/v2 dimigrasikan menuju schema v3 melalui jalur migrasi yang tervalidasi.
Future schema yang tidak dikenali ditolak daripada ditulis ulang secara diam-diam.

## Keamanan dan integritas

Release bundle mencakup portable ZIP, exact-source ZIP, BUILD_INFO, SHA256SUMS,
release notes, maintenance policy, dan backup/recovery policy. Artifact tidak boleh
mengandung API key, private key, .env, cache/log runtime, atau recovery user.
