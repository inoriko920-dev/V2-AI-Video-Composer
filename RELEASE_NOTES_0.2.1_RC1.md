# AI Automatic Video Composer 0.2.1-rc1

Release Candidate V2 untuk Windows 11 x64. Build ini menguji line advanced-animation
v0.2.1 dan **belum** merupakan GitHub Release final v0.2.1.

## Sorotan 0.2.1

- schema v4 + `animation_keyframe_contract=advanced-v1` untuk advanced animation,
  dengan schema v3 tetap kompatibel dan tidak dipromosikan otomatis;
- aktivasi advanced hanya saat edit advanced benar-benar diterapkan dan dikonfirmasi;
- backup `.pre-schema-v4.bak` dibuat pada overwrite v3→v4 pertama;
- advanced keyframe production path untuk Opacity, Crop, Blur, Shadow, Glow, dan
  Mask Progress;
- Bezier, velocity 0..4, dan overshoot 0..50% memakai evaluator canonical yang sama
  untuk preview/render scheduling;
- Position X/Y, Scale, dan Rotation tetap kompatibel dengan foundational keyframes
  dan memperoleh semantics Bezier hanya pada advanced-v1;
- modal `Animasi Aset…` yang sudah ada diperluas dengan tab Preset + Keyframe,
  tanpa redesign main window;
- Preset tidak menghapus track Keyframe;
- Apply advanced + aktivasi schema/marker adalah satu transaksi Undo/Redo;
- FFmpeg tetap final/reference renderer dan 21 efek native v0.2.0 tetap menjadi
  regression baseline.

## Kompatibilitas project

Project schema v3 tetap dapat dibuka, disimpan, dipreview, dan dirender sebagai v3
selama tidak ada edit advanced yang diterapkan. Membuka tab Keyframe, memilih property,
preview, render, Auto/AI, Copy Scene Animations, atau normal Save tidak boleh mempromosikan
v3 secara implisit.

Setelah project dipromosikan ke schema v4 / advanced-v1, v0.2.0 tidak dapat membuka
file tersebut. Gunakan backup `.pre-schema-v4.bak` bila perlu kembali ke source v3.

## Gate RC

K8 RC harus membuktikan:
- compile, Ruff, strict mypy, secret scan, dependency check;
- full technical Windows suite dengan FFmpeg nyata;
- advanced render/parity/performance/regression tests K1–K7;
- 21 native effects + Selection In/Out regression;
- 8 frozen STEP09 UI screenshots;
- 10/100/500 Scene command-build benchmark;
- Windows portable build + verification;
- packaged EXE launch + real UI capture;
- exact-source ZIP + portable ZIP + SHA-256 re-verification;
- tidak ada secret, autosave/recovery, cache/log, atau runtime-user data di artifact.

## Status publication

`0.2.1rc1` adalah kandidat pengujian. Tag/release final `v0.2.1` tidak boleh dibuat
sebelum K8 RC PASS dan final-release gate dijalankan lagi dari source final.
Tag/release `v0.2.0` tetap immutable.
