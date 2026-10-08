# STEP 01 — ASTRA: Kontrak Implementasi Kandidat Patch v0.3.1

**Tanggal keputusan:** 8 Oktober 2026, WIB.  
**Repositori tunggal:** `inoriko920-dev/V2-AI-Video-Composer`  
**Role:** ASTRA perencana; SOL pelaksana hanya setelah gate STEP 01 PASS dan instruksi lanjut terpisah.  
**Status dokumen:** PLANNING / NO CODING / NO RELEASE / NO TAG / NO DISTRIBUTABLE.  
**Baseline** `main`: `01b7dd4437acc0482132e552b4f6199d03162ee4` (PR #66 STEP 00 sudah merge; post-merge CI #37790115871 dan CodeQL #37790115905 PASS).  
**Frozen public stable:** `v0.3.0` → `d5a085fe239763e469ad30e91f526179fe8b2595` (9 aset publik), `v0.2.2` → `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.

## 1. Ringkasan eksekutif dan keputusan

**Keputusan ASTRA: GO untuk kontrak perencanaan patch v0.3.1; NO-GO untuk coding selama STEP 01, penandaan versi final, dan publikasi.** Perubahan produk tunggal sejak stable adalah normalisasi ekstensi `.wav` setelah PR #65. PR #64 memperbaiki Windows acceptance sesudah rilis dan memperbarui dokumentasi; bukan fitur runtime baru. STEP 00 telah mengunci batas, risiko, dan urutan langkah; STEP 01 menjadikan batas tersebut sebagai instruksi yang dapat diuji SOL.

Alasan kandidat patch: pengguna Windows dapat menerima penamaan audio rekaman yang kanonis pada release minor pemeliharaan, sementara semua perilaku render, UI, Gemini, schema, backup/recovery, efek, dan dependencies dipertahankan. Uji Windows pada runner sudah lolos, tetapi **uji langsung di PC pemilik belum ada** dan harus tetap berstatus PENDING.

Satu risiko utama yang sudah terbukti dari pemeriksaan source: `tests/unit/test_v2_0_3_0_rc_release_contract.py::test_rc_01_package_runtime_and_release_notes_are_v030` sengaja mengharuskan `pyproject.toml` dan `__version__` bernilai 0.3.0. Saat source aktif diubah ke 0.3.1, tes itu tidak lagi merepresentasikan histori rilis beku. SOL wajib mengubah **cakupan pemeriksaan** tes lama (mengecek keberadaan artefak 0.3.0/immutability, bukan versi aktif) serta menambah tes kontrak 0.3.1. Jangan sekadar `skip`, menghapus, atau melemahkan tes keamanan.

## 2. Kontrak produk: boleh, tetap, dilarang

| Grup | Kebijakan FINAL untuk kandidat v0.3.1 | Bukti |
| --- | --- | --- |
| Perbaikan WAV | Pertahankan `ensure_wav_suffix`: `.WAV`, `.WaV`, `.wav`, input tanpa ekstensi, dan `.MP3` menghasilkan path akhir berakhiran `.wav`. | `tests/unit/test_narration_recording_window.py`; PR #65 |
| Rekaman atomik | Staging di direktori yang sama, penggantian file hanya setelah sukses, tidak menghilangkan rekaman lama saat gagal. | Unit dan Windows acceptance |
| UI | Semua 42 referensi editor dan 3 dialog recovery tetap 1:1. Tidak ada pekerjaan gambar UI baru. | Screenshot freeze/visual QA |
| Project | Schema v3/v4; kontrak `advanced-v1`, relink/dirty-state, Save/Open/Save As dan history tetap. | Regression |
| Autosave | Proyek harus pernah disimpan manual; backup pre-Restore, pembatalan aman, metadata SHA, tidak mengubah baseline Save secara diam-diam. | Failure injection + integration |
| Media/render | 21 efek, subtitle, timeline, FFmpeg/ffprobe eksternal, no embedded binaries. | Windows FFmpeg 9.0.2, render+probe |
| Gemini | Model kredensial Windows Credential Manager dan multi-slot tetap, tidak mengubah network/provider. | Secret/security tests |
| Dependensi | Python 3.12.10, PySide6 6.11.2, lock yang dipin, PyInstaller 6.22.3 tetap; jangan refresh spekulatif. | `requirements.lock` dan `pyproject.toml` |
| Rilis terdahulu | Tag, aset, URL, checksum dan release metadata `v0.3.0` dan `v0.2.2` tidak boleh dimutasi. | GitHub Release API + SHA |

**Out of scope:** fitur baru; GPU/export redesign; schema v5; mengganti FFmpeg; modifikasi repositori legacy `AI-Automatic-Video-Composer`; pembersihan massal file lama; mengaktifkan publish sebelum izin pengguna.

## 3. Urutan STEP yang mengikat

| Tahap | Pemilik | Kegiatan | STOP/PASS |
| --- | --- | --- | --- |
| 01 (SEKARANG) | ASTRA | Simpan Markdown + satu DOCX detail; review source, target kontrak, tes/gate, commit PR docs-only. | STOP setelah dokumen, final-head CI/CodeQL, merge dan post-merge PASS |
| 02 (LATER) | SOL | Tes kontrak 0.3.1 terlebih dulu (RED sah), lalu metadata runtime, dokumen paket, spec dan tes historis yang disesuaikan; GREEN. | Tidak boleh membangun release atau tag |
| 03 (LATER) | SOL | Builder read-only baru v0.3.1 dan workflow RC sementara + SHA/ZIP manifest exact-source. | Hanya Actions artifact kandidat nonpublik |
| 04 (LATER) | SOL/QA | CI, CodeQL, backend opsional, Windows acceptance, FFmpeg/GUI, path matrix, source diff. | Semua FINAL-HEAD SUCCESS |
| 05 (LATER) | SOL | Review/merge kandidat, exact-main source SHA, CI+CodeQL pasca-merge, freeze. | Bukan izin publish |
| 06 (LATER) | Pemilik | Uji Windows 11 lokal atau keputusan waiver tertulis yang menyebut cakupan dan risiko. | Manual UAT tetap PENDING tanpa bukti |
| 07 (LATER) | Publisher atas instruksi eksplisit | Publikasi v0.3.1 pada tag immutable, release asset ledger dan redownload. | Tanpa izin terpisah: STOP |

## 4. Inventaris file: pemilik, tindakan, dan tes terkait

| File / lokasi | STEP | Tindakan yang diizinkan SOL dan larangan |
| --- | --- | --- |
| `pyproject.toml` | 02 | `[project].version=0.3.1`; jangan naikkan dependency/required Python. |
| `src/aavc/__init__.py` | 02 | `__version__="0.3.1"`; harus identik dengan metadata distribusi Python. |
| `aavc.spec` | 02 | Ganti bundled `RELEASE_NOTES_0.3.0.md` dengan `RELEASE_NOTES_0.3.1.md`; pertahankan resources/schemas/Licenses/guides dan onedir. |
| `RELEASE_NOTES_0.3.1.md` (BARU) | 02 | Nyatakan hanya normalisasi WAV; bedakan kandidat belum dipublikasi dan hasil test; referensi stabil lama. |
| `V2_FINAL_RELEASE_MANIFEST_0.3.1.md` (BARU) | 02 | Detail source SHA, run IDs yang baru valid, schema 3/4, FFmpeg eksternal, penanda `NOT_PUBLISHED` sampai benar-benar dirilis. |
| `scripts/verify_portable.ps1` | 02 | Wajib cek embedded notes 0.3.1 dan artifact safety; tidak menghapus slot `tools/ffmpeg/README.md`. |
| `docs/USER_GUIDE.md`, `MAINTENANCE.md`, `BACKUP_AND_RECOVERY.md` | 02 | Revisi minimal penjelasan patch + status rilis, tidak menghapus historis, backup dan keterbatasan. |
| `tests/unit/test_v2_0_3_0_rc_release_contract.py` | 02 | Tetap memvalidasi script/workflow 0.3.0 historis dan frozen assets; **jangan** mensyaratkan versi source aktif harus 0.3.0. |
| `tests/unit/test_v2_0_3_1_rc_release_contract.py` (BARU) | 02 | Tambah kontrak test-first: metadata, notes/spec, no-publish workflow, dual frozen tags, source+ZIP identity dan denied overwrite. |
| `tests/unit/test_narration_recording_window.py` | 02 | Periksa lima case suffix sudah PASS; penambahan hanya bila membuktikan gap. |
| `scripts/build_v2_0_3_1_candidate.ps1` (BARU) | 03 | Berdasarkan pola 0.3.0 tapi unik; **jangan mengubah** builder historis. Source ZIP `git archive` commit yang sama dengan build; no existing release/tag overwrite. |
| `.github/workflows/v2-0.3.1-rc.yml` (BARU) | 03 | `contents: read` saja, Windows runner, versions pinned, artifact expiring, no `gh release create`, no `git push --tags`. |
| `.github/workflows/v2-user-acceptance.yml` | 02/03 | Pisahkan `Current candidate 0.3.1 identity` dari `Verify immutable PUBLIC v0.3.0` sehingga keduanya diuji. Wajib pertahankan FFmpeg/render/EXE dan asset digest stable. |
| `scripts/verify_v2_0_3_1_portable_paths.ps1` (BARU jika perlu) | 03 | Replikasi 5 path ASCII, spasi, apostrof, Unicode, nested; jangan ubah bukti historis 0.3.0. |
| `docs/v2_0_3_1_planning/` | 01 dst | Satu DOCX per STEP planning, Markdown pendamping, bukti dan gate. |

**Kontrak perubahan fungsi yang sudah merge:** `src/aavc/presentation/windows/narration_recording_window.py` tidak perlu dipatch ulang pada v0.3.1 jika tidak ada bukti bug baru. Jangan menduplikasi PR #65.

## 5. Spesifikasi test-first RED → GREEN untuk SOL

Sebelum mengubah `pyproject.toml`, tulis tes yang mendemonstrasikan kontrak 0.3.1 belum terpenuhi (RED). Bedakan RED yang diharapkan (versi/notes/RC baru belum ada) dari kegagalan lingkungan. Catat commit, command, stdout dan nama testcase; jangan menandai RED sebagai bug permanen. Setelah penyesuaian source, tes yang sama harus GREEN pada commit yang sama dengan kandidat.

| ID | Tes yang harus dibuktikan | Kriteria PASS |
| --- | --- | --- |
| VER-01 | `pyproject.toml`, package `__version__`, metadata `importlib.metadata.version` | Ketiganya tepat `0.3.1`, tidak hanya nama ZIP. |
| VER-02 | `aavc.spec`, `verify_portable.ps1` dan root `RELEASE_NOTES_0.3.1.md` | Distribusi memakai notes baru, notes historis utuh di repository. |
| HIST-01 | Historis test 0.3.0 | Builder tetap menjaga tag; tes tidak lagi mematok runtime aktif 0.3.0. |
| HIST-02 | `v0.2.2` dan `v0.3.0` refs | Kedua tag tetap SHA frozen persis; anti-rewrite berlaku. |
| WAV-01..05 | `take`, `take.MP3`, `take.WAV`, `take.WaV`, `take.wav` | Output suffix `.wav`; tidak ada klobber file pada failure. |
| META-01 | `BUILD_INFO.txt` kandidaat | `version=0.3.1`, `release_commit=<exact SHA>`, `publication_status=READY_FOR_PUBLICATION` bermakna **candidate only**, bukan published. |
| SAFE-01 | Check release/tag `v0.3.1` sudah ada | Fail-closed, tidak overwrite/tag force; `v0.3.0` tak berubah. |
| SAFE-02 | Coba bermasalah: ZIP corrupt/source mismatch | Fail-closed sebelum mengklaim READY; file sumber tidak ditimpa. |
| SHA-01 | Nested `win64.zip` dan `source.zip` | CRC valid, checksum setelah zip ulang dan rehash cocok, exact source SHA. |
| CI-01 | Workflow `v2-0.3.1-rc.yml` | Hanya `contents: read`, upload artifact, no publish. |
| CI-02 | Existing PR Windows acceptance | Tidak lagi mengharuskan runtime `0.3.0`; *tetap* periksa 9 aset + dua checksum public 0.3.0. |
| QA-01 | `compileall`, Ruff, mypy dan full `pytest -m "not visual"` | Semua PASS, kumpulkan count aktual; jangan mengarang angka tes. |
| QA-02 | UI screenshot baseline, 21 effects, autosave/recovery, FFmpeg | Tidak ada regresi; tes Windows yang sesuai PASS. |

Jangan membuat tes yang hanya mencari string dangkal tanpa mengeksekusi perilaku: kombinasikan test-contract statis dengan test runtime, test-binary, tes hash, dan negative-path.

## 6. Kontrak builder dan paket 0.3.1 (untuk STEP 03, BELUM DIKERJAKAN)

Nama yang ditargetkan:
- `AI-Automatic-Video-Composer-0.3.1-win64.zip` — onedir Windows 11 x64, EXE root, folder pendukung, `tools/ffmpeg/README.md` di root; **tanpa** ffmpeg.exe/ffprobe.exe.
- `AI-Automatic-Video-Composer-0.3.1-source.zip` — `git archive` dari sumber tepat; ini snapshot dan **bukan full-history Git backup**.
- `BUILD_INFO.txt`, `SHA256SUMS.txt`, `RELEASE_NOTES_0.3.1.md`, `V2_FINAL_RELEASE_MANIFEST_0.3.1.md`, `USER_GUIDE.md`, `MAINTENANCE.md`, `BACKUP_AND_RECOVERY.md`.

Prinsip builder: selalu mengacu commit sumber nyata (bukan label `main` bergerak); abort bila output directory telah ada; jangan melakukan publikasi; jangan mengizinkan dirty working tree atau source tree yang bukan commit yang diklaim; verifikasi file ZIP lengkap dan SHA-256, validasi metadata serta ZIP traversal/nama file sebelum dianggap PASS; cek tidak ada secrets/cache/autosave/credential. Bila file ZIP dibuat oleh Windows dan diverifikasi pada Linux, tangani CRLF/normalisasi serialization secara eksplisit tanpa mengubah konten sumber. Jangan menganggap `READY_FOR_PUBLICATION` sebagai `PUBLISHED`.

**Aturan calon versi**: versi runtime `0.3.1` baru dihasilkan pada STEP 02; *tidak* ada binary berlabel 0.3.1 yang sah di STEP 01. Ketersediaan RC di Actions tidak memberikan tautan rilis permanen.

## 7. Sistem gating GitHub dan persyaratan Windows

GitHub PR harus difokuskan pada perubahan yang disetujui. Jalankan empat gate pada **head SHA final PR**, bukan run sebelumnya: CI (quality/tests/screenshots), CodeQL, Optional Backend Spike, Windows Automated User Acceptance. Jika salah satu merah atau cancelled, perbaiki dan ulangi; jangan merge berdasarkan warna hijau commit yang lebih lama. Setelah merge, wajib CI dan CodeQL pada SHA `main` hasil merge PASS. Untuk candidate RC gunakan workflow Windows khusus read-only dan bukti nested SHA, path matrix 5/5.

Windows acceptance manual pemilik diperlukan untuk deklarasi kualitas pengguna: EXE launch, DOCX scene + Axxx, audio WAV (termasuk suffix mixed case), Save/Save As, autosave, recovery valid/rusak/baseline berubah, subtitle, render singkat, FFmpeg source dan pemeriksaan log. Jangan menghapus / corrupt satu-satunya salinan proyek pemilik; gunakan fixture contoh. **Hasil otomatis bukan bukti manual Windows 11 milik pemilik.**

## 8. Keamanan, immutability, backup, dan rollback

`v0.3.0` publik memiliki tepat 9 aset dan kedua ZIP frozen berikut:
- Windows: `066312fe6c983c797939fccf5682f5f4867c6ba528a099d18e67f33a8e1c7681`
- Source: `063c3fa88c03972fdcadcf6c3a7d7c7b183df07b146710cd209a59cbb11ca9df`

Tetap verifikasi `v0.2.2` source tag `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`; sumber v0.3.0 frozen `d5a085fe239763e469ad30e91f526179fe8b2595`. Dalam kandidat, larang workflow publikasi yang memiliki `contents: write` tanpa izin eksplisit terpisah. Semua API key/Windows Credential Manager dan data runtime tidak boleh masuk ZIP atau log. Jika v0.3.1 gagal kemudian, rollback dapat kembali menggunakan ZIP v0.3.0 yang tidak berubah; *source.zip* saja tidak dapat memulihkan seluruh history Git—full `git bundle` perlu dikelola terpisah.

## 9. Matriks risiko yang harus dimitigasi SOL

| Risiko | Probabilitas/dampak | Mitigasi dan gate |
| --- | --- | --- |
| Tes historis 0.3.0 memblokir bump | Tinggi / sedang | Isolasi metadata historis, ubah test expectation secara terbatas dan tambah kontrak baru; tes tidak boleh dibuang. |
| Windows workflow memeriksa runtime versi lama | Tinggi / tinggi | Dua langkah terpisah: candidate identity 0.3.1 dan immutability stable 0.3.0. |
| Builder 0.3.0 secara salah dipakai ulang | Tinggi / tinggi | Buat builder baru, nama artefak unik, keep read-only, anti tag-reuse. |
| Binary dan source berasal dari SHA berbeda | Sedang / kritis | BuildInfo exact SHA, comparison of ZIP/source/tree and checksums. |
| UI/recovery rusak akibat packaging | Rendah / tinggi | Fixture/screenshot/Windows real FFmpeg/restore tests. |
| Salah mengumumkan kandidat sebagai rilis | Sedang / tinggi | Hanya Actions artifact nonpublik, no tag/release, explicit publish authorization. |
| Data pengguna hilang saat uji recovery | Rendah / kritis | Salinan fixture terpisah, backup pra-Restore, pilihan Cancel no mutation. |

## 10. Kriteria sign-off dan protokol komunikasi

STEP 01 **PASS** hanya jika:
1. Markdown versi kanonis + **satu DOCX lengkap** ada di `docs/v2_0_3_1_planning/` repo yang sama.
2. DOCX bisa dibuka, semua tabel terlihat, visual QA render semua halaman PASS, tanpa halaman terpotong.
3. Diff PR hanya dokumen planning—tidak ada versi 0.3.1 pada runtime, perubahan workflow permanen, tag atau aset.
4. CI, CodeQL, backend, dan Windows PR final-head SUCCESS; setelah merge CI/CodeQL main terbaru PASS; frozen tag/API tetap sama.
5. Handoff menyebut file, acceptance, RED/GREEN, risiko, keputusan dan STOP jelas.

Handoff ASTRA → SOL berikutnya: **STEP 02 test-first + metadata release candidate**. SOL harus membaca STEP 00 dan STEP 01 dulu, melaksanakan hanya satu STEP pada satu giliran, laporkan SHA PR, test PASS/FAIL, apa yang berubah, apa yang dilarang, dan sebut STEP berikutnya. **Jangan mulai STEP 02 dalam giliran STEP 01 ini.**

## 11. Evidence referensi dan keputusan publikasi

- [PR #64 pascarilis](https://github.com/inoriko920-dev/V2-AI-Video-Composer/pull/64)
- [PR #65 WAV](https://github.com/inoriko920-dev/V2-AI-Video-Composer/pull/65)
- [PR #66 STEP 00](https://github.com/inoriko920-dev/V2-AI-Video-Composer/pull/66)
- [v0.3.0 public release](https://github.com/inoriko920-dev/V2-AI-Video-Composer/releases/tag/v0.3.0)
- [Main CI STEP00 #37790115871](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37790115871)
- [Main CodeQL STEP00 #37790115905](https://github.com/inoriko920-dev/V2-AI-Video-Composer/actions/runs/37790115905)

**FINAL PLANNING DECISION:** v0.3.1 is a candidate, not a published release. STEP 01 ends after this planning document is reviewed and merged.