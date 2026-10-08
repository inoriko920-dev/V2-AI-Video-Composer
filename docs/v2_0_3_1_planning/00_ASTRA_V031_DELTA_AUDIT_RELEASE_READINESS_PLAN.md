# STEP 00 — ASTRA Audit Delta dan Kesiapan Kandidat v0.3.1

**Tanggal:** 8 Oktober 2026 WIB. **Repo tunggal:** `inoriko920-dev/V2-AI-Video-Composer`.  
**Keputusan:** `PLANNING ONLY / NO RELEASE / NO VERSION BUMP / OWNER UAT PENDING`.  
**Sumber:** `main` = `22352787fef73c9fe54ef0e87cde3c53d6b2ea73`; tag rilis tetap `v0.3.0` → `d5a085fe239763e469ad30e91f526179fe8b2595`, `v0.2.2` → `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.  
**Artefak native:** `docs/v2_0_3_1_planning/docx/00_ASTRA_V031_DELTA_AUDIT_RELEASE_READINESS_PLAN.docx` wajib ada dan diverifikasi sebelum STEP 00 PASS.

## 1. Ringkasan keputusan

| Dimensi | Fakta / keputusan |
| --- | --- |
| Rilis publik | `v0.3.0`, sembilan aset publik dan SHA-256 resmi tetap immutable. |
| Source development | PR #64 dan #65 sudah merge. Tidak ada PR terbuka saat audit. |
| Perubahan fungsional | PR #65: `ensure_wav_suffix` menormalkan `.WAV`/`.WaV` menjadi `.wav`; regression test ditambahkan. |
| Perubahan nonfungsional | PR #64: Windows PR Acceptance memeriksa rilis publik lama alih-alih membuat ulang RC 0.3.0; README/status diperbarui. |
| Bukti teknis | PR #65: CI #37786338973 PASS, CodeQL #37786338948 PASS, backend #37786338942 PASS, Windows acceptance #37786338976 PASS. |
| Pasca-merge main | CI #37786988465 PASS dan CodeQL #37786988540 PASS. |
| UAT langsung | Belum ada bukti Windows 11 pada komputer pemilik; tetap PENDING. |
| Keputusan STEP 00 | Layak untuk *perencanaan* patch kandidat v0.3.1. Tidak cukup untuk publikasi atau status final. |

## 2. Masalah dan klasifikasi patch

Perubahan PR #65 memperbaiki kontrak penamaan rekaman WAV pada sistem file yang peka huruf: sebelumnya `candidate.suffix.lower() != ".wav"` menerima `take.WAV` tanpa mengubah nama, meskipun kontrak tes mengharuskan `take.wav`. Perbaikan membandingkan suffix terhadap literal `.wav`; tes memastikan input tanpa ekstensi, `.MP3`, `.WAV`, `.WaV`, dan `.wav`. Ini patch kecil dan layak menjadi perubahan produk v0.3.1.

PR #64 memperbaiki workflow pengujian pascarilis; perbaikan ini *bukan* perubahan pada EXE publik yang telah dirilis. Kedua PR menjadi basis source kandidat, tetapi paket v0.3.0 yang ada tetap mempertahankan source lamanya.

Mengganti versi saja tidak aman: `pyproject.toml`, `src/aavc/__init__.py`, `aavc.spec`, `scripts/verify_portable.ps1`, `scripts/build_v2_0_3_0_candidate.ps1`, workflow pengujian Windows, dan tes kontrak mengunci 0.3.0. Migrasi parsial dapat menciptakan ZIP yang identitas file/EXE/checksum/tag-nya bertentangan. Wajib desain test-first dan gate exact source baru.

## 3. Cakupan beku

| Diizinkan pada rencana v0.3.1 | Dilarang tanpa persetujuan baru |
| --- | --- |
| Perbaikan WAV PR #65, metadata versi 0.3.1, release notes dan pemeriksaan identitas sumber baru. | Fitur baru, perombakan UI, migrasi schema, perubahan provider Gemini, pembaruan dependencies spekulatif. |
| Builder dan workflow kandidat 0.3.1 **read-only** serta aset Actions yang belum publik. | Menimpa tag, asset, commit atau Release v0.3.0 maupun v0.2.2. |
| Tetap mempertahankan 42 referensi UI, tiga dialog pemulihan, autosave dan recovery. | Desain ulang tampilan atau menghapus backup pre-recovery. |
| FFmpeg/ffprobe eksternal; Python 3.12.10, PySide6 6.11.2, FFmpeg reference 9.0.2 tetap acuan. | Membundel binary FFmpeg atau menurunkan pengujian keamanan. |

## 4. Tahap implementasi dan hard gate

| STEP | Luaran | Gate |
| --- | --- | --- |
| 00 — Audit ini | Markdown + DOCX final native dengan laporan gap dan keputusan Go/No-Go; PR dokumentasi saja. | DOCX valid dan visual QA; final-head CI/CodeQL PASS, merge dan main verification. |
| 01 — Contract release patch | DOCX ASTRA detail tentang versi, builder, output, pemilik file, test RED/GREEN dan UAT. | DOCX lengkap di repo; review scope PASS sebelum coding. |
| 02 — Test-first & version metadata | Tes kontrak 0.3.1 baru, perubahan versi runtime/metadata, manifest, notes, tanpa touch published 0.3.0. | RED yang valid, GREEN setelah implementasi, Ruff dan mypy PASS. |
| 03 — Kandidat ZIP | Builder `build_v2_0_3_1_candidate.ps1`, ZIP portable/source exact SHA, SHA256SUMS, BUILD_INFO, workflow read-only. | Asset internal lengkap, ZIP CRC/SHA PASS, tidak ada tag/release baru. |
| 04 — Windows QA | Full CI, CodeQL, backend, 907+ regresi relevan, FFmpeg, screenshot asli, path matrix 5/5, EXE smoke. | Run final-head semua SUCCESS dan rilis lama immutable. |
| 05 — Freeze source | Merge PR kandidat hanya setelah gate PASS; exact-main acceptance dan source/hash freeze. | Main CI/CodeQL postmerge PASS, tag lama tidak bergerak. |
| 06 — UAT manual | Pemilik mencoba startup, DOCX+Axxx, audio, edit/save, autosave, konflik recovery, render. | UAT PASS atau waiver eksplisit; laporan bug dikaji. |
| 07 — Publikasi (TERPISAH) | Tag/release v0.3.1 dengan aset checksum final dan redownload. | HARUS ada instruksi publikasi baru dari pengguna; dilarang otomatis. |

STOP: STEP 00 tidak mengizinkan coding runtime, bump versi, build berlabel 0.3.1, membuat tag, atau menerbitkan aset publik. Tidak ada STEP gambar UI baru karena desain lama dipertahankan 1:1.

## 5. File ownership dan strategi tes

| File | Scope mendatang |
| --- | --- |
| `pyproject.toml` + `src/aavc/__init__.py` | Konsistensi versi 0.3.1 pada STEP 02. |
| `RELEASE_NOTES_0.3.1.md` + `V2_FINAL_RELEASE_MANIFEST_0.3.1.md` | File baru; jangan overwrite berkas 0.3.0. |
| `aavc.spec` + `scripts/verify_portable.ps1` | Bundled notes/user docs sesuai kandidat 0.3.1. |
| `scripts/build_v2_0_3_1_candidate.ps1` | Script baru; immutable tag 0.3.0 dan 0.2.2, menolak tag 0.3.1 eksisting. |
| `.github/workflows/v2-0.3.1-rc.yml` | Read-only, artifact expiring, Windows QA; bukan publisher. |
| `.github/workflows/v2-user-acceptance.yml` | Menjaga tes immutable 0.3.0 dan sekaligus tes runtime identitas kandidat 0.3.1. |
| `tests/unit/test_v2_0_3_1_rc_release_contract.py` | Kontrak baru; tes 0.3.0 historis tetap ada. |
| `docs/USER_GUIDE.md` dan `MAINTENANCE.md` | Pembedaan jelas kandidat tidak terbit versus stable, persyaratan FFmpeg. |
| Render/preview/timeline/autosave/recovery/provider | Dibekukan tanpa bug baru yang berbukti. |

## 6. Acceptance matrix

| ID | Syarat terukur |
| --- | --- |
| ID-01..03 | Metadata package/runtime/BUILD_INFO = 0.3.1 dan exact source commit. |
| HIS-01..02 | Tag v0.3.0/v0.2.2 dan seluruh aset publik 0.3.0 tetap sama. |
| AUDIO-01..05 | Ekstensi tanpa suffix, .MP3, .WAV, .WaV, .wav → hasil kanonis .wav. |
| Q-01..04 | Compile, Ruff, mypy, pytest, CodeQL, secret scan PASS. |
| UI-01..03 | Screenshot 42 UI referensi/frozen + tiga dialog recovery tetap. |
| REC-01..04 | Autosave/recovery nonclobber, konflik, backup pre-Restore, rollback PASS. |
| REN-01..04 | FFmpeg 9.0.2, render/subtitle, packaged EXE smoke PASS. |
| PKG-01..05 | Portable onedir, FFmpeg eksternal, 5 path variants, ZIP CRC, no secrets. |
| SHA-01..03 | Exact source ZIP, portable ZIP SHA256 dan BUILD_INFO benar. |
| GATE-01..04 | CI, CodeQL, backend, Windows acceptance final-head SUCCESS. |
| UAT-01..06 | Pengujian langsung pemilik terpisah; status PENDING sampai ada bukti. |
| PUB-01..03 | Tidak ada tag/release 0.3.1 sebelum persetujuan terpisah. |

## 7. Risiko, rollback, dan keamanan

- **Tes hard-coded 0.3.0:** jangan menghapus kontrak historis; buat kontrak baru dan tes pemisahan stable vs candidate.
- **Bukti CI kedaluwarsa:** jangan mengutip run-id branch lama sebagai PASS kandidat; periksa commit final-head yang tepat.
- **Source ZIP bukan full backup:** full disaster-recovery butuh Git bundle terpisah.
- **Tag dan rilis lama immutable:** gunakan v0.3.0 sebagai rollback jika patch berikut bermasalah.
- **Rahasia:** API key/provider credential tidak boleh masuk source, log, ZIP, atau artefak.
- **UAT belum ada:** jangan menyamakan Linux/offline dan CI Windows dengan uji di PC pengguna.
- **Pemilik repo dan cakupan:** jangan ubah `inoriko920-dev/AI-Automatic-Video-Composer` (repo legacy read-only).

## 8. Gate akhir dan handoff ASTRA → SOL

**GO STEP 00:** simpan Markdown + native DOCX dalam folder planning, visual QA Word semua halaman, PR docs-only, CI/CodeQL PASS, merge docs, verifikasi main dan tag lama.

**NO-GO:** bump versi, coding runtime, membuat ZIP bernama 0.3.1, membuat tag atau GitHub Release, mengklaim Windows owner UAT PASS. Pekerjaan selanjutnya **STEP 01 DOCX readiness** setelah STEP 00 benar-benar PASS dan perintah `lanjutkan` terpisah.

**Bukti / tautan:** https://github.com/inoriko920-dev/V2-AI-Video-Composer/pull/64 ; https://github.com/inoriko920-dev/V2-AI-Video-Composer/pull/65 ; https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/tag/v0.3.0

**FINAL STATUS:** PLANNING COMPLETE LOCALLY; GitHub gate belum dinyatakan PASS sampai PR ditutup dengan CI/CodeQL dan DOCX final terverifikasi.