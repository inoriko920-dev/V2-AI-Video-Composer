# AI Automatic Video Composer 0.2.1

Rilis stabil V2 untuk Windows 11 x64. Versi 0.2.1 mempromosikan advanced animation
yang telah melewati RC 0.2.1rc1, Windows acceptance, real FFmpeg rendering, parity /
performance gates, portable packaging, CI, CodeQL, dan release reproducibility checks.

## Sorotan utama

- **Advanced Animation schema v4 / advanced-v1** dengan aktivasi eksplisit; project schema
  v3 tetap kompatibel dan tidak dipromosikan hanya karena dibuka, dipreview, dirender,
  Auto/AI, Copy Scene Animations, atau normal Save.
- Keyframe advanced production-ready untuk **Opacity, Crop 4 sisi, Blur, Shadow, Glow,
  dan Mask Progress**.
- Position X/Y, Scale, dan Rotation mendukung semantics advanced **Bezier, velocity,
  dan overshoot** saat advanced-v1 aktif.
- Modal **Animasi Aset** mempertahankan jalur Preset dan menambahkan tab Keyframe tanpa
  redesign main window.
- Preset tidak menghapus keyframe yang sudah tersimpan.
- Aktivasi v3→v4 + marker advanced-v1 + edit aset diterapkan sebagai satu transaksi
  Undo/Redo.
- First overwrite v3→v4 membuat backup non-clobbering `.pre-schema-v4.bak`.
- Normal Save tidak boleh menurunkan project v4 menjadi v3.
- FFmpeg tetap final/reference renderer; 21 efek native v0.2.0 tetap lolos regression.

## Advanced property set

- Transform: Position X, Position Y, Scale, Rotation
- Visibility / framing: Opacity, Crop Left/Top/Right/Bottom, Mask Progress
- Effects: Blur, Shadow, Glow
- Segment interpolation: Hold, Linear, Bezier
- Easing, velocity 0..4, overshoot 0..50%

Preview ringan menggunakan evaluator canonical. Blur/Shadow/Glow tetap ditandai Approx
saat interaksi; hasil FFmpeg adalah sumber kebenaran final.

## Kompatibilitas project

- Project schema v1/v2 tetap mengikuti migrasi tervalidasi menuju v3.
- Project v3 tetap v3 selama tidak ada advanced edit yang benar-benar diterapkan.
- Saat advanced edit pertama disetujui, project menjadi schema v4 dengan
  `animation_keyframe_contract=advanced-v1`.
- Setelah disimpan sebagai v4, project tersebut tidak dapat dibuka oleh AAVC v0.2.0.
  Backup `.pre-schema-v4.bak` mempertahankan source v3 sebelum promosi pertama.
- Future schema atau mismatch schema/marker ditolak daripada ditulis ulang diam-diam.

## Bukti RC yang diterima

- RC source: `603039156a46d34935f5092b477b58eb74042e28`
- RC Gate: `37640176055` — PASS
- Automated User Acceptance: `37640175991` — PASS
- Full technical Windows suite: **761 tests PASS**
- CI: `37640175933` — PASS
- CodeQL: `37640175822` — PASS
- Optional Backend Spike: `37640175960` — PASS
- FFmpeg 9.0.2 real Windows runtime: PASS
- 10/100/500 Scene benchmark: PASS
- 8 frozen STEP09 UI captures: PASS
- Windows portable + packaged EXE launch: PASS

## Distribusi dan keamanan

- Windows portable memakai PyInstaller onedir yang dikemas menjadi ZIP.
- FFmpeg/ffprobe binary tidak dibundel; gunakan app-local `tools/ffmpeg/` atau PATH.
- Provider AI tetap Gemini dan raw API key tidak disimpan di project/release bundle.
- Release bundle tidak boleh berisi `.env`, private key, autosave/recovery user,
  cache, log runtime, atau user-data runtime.
- Final bundle mencakup exact-source ZIP, portable ZIP, BUILD_INFO, SHA256SUMS,
  release notes, user guide, maintenance policy, backup/recovery policy, dan final
  release manifest.

## Integritas release

Tag `v0.2.1` bersifat immutable setelah diterbitkan. Workflow publication menolak
memindahkan atau menimpa tag/release yang sudah ada. Published `v0.2.0`, `v0.1.1`,
dan `v0.1.0` tetap immutable.
