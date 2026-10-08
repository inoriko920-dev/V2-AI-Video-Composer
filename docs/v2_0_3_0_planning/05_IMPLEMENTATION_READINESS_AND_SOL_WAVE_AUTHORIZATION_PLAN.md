# STEP 05 — Audit Kesiapan Implementasi dan Rencana Otorisasi Gelombang SOL

**Proyek:** V2-AI-Video-Composer | **Siklus:** usulan v0.3.0 GAP-03A Autosave/Recovery | **Tanggal:** 8 Oktober 2026 WIB  
**Repo satu-satunya yang boleh diubah:** `inoriko920-dev/V2-AI-Video-Composer` | **Peran sekarang:** ASTRA / perencanaan dan audit source-of-truth, bukan implementasi.  
**Baseline terverifikasi sebelum STEP 05:** `main` = `395a5056f72b97189cd43ba8987bb9ff1d7cc57d`, setelah STEP04 PR #55 merged. **Tag stabil yang wajib tetap:** `v0.2.2` = `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.  
**Batas instruksi:** perintah "lanjutkan" ini berlaku hanya untuk STEP05. Tidak mengizinkan coding STEP06, versi/rilis baru, perubahan dependencies, penambahan UI di luar tiga dialog, atau sentuhan repo lama.

## 01. Keputusan eksekutif dan makna gate

STEP05 adalah **Definition of Ready (DoR)** sebelum implementasi SOL, bukan pelaksanaan kode. Tujuannya memastikan seluruh keputusan produk, kontrak arsitektur, teks/visual UI, rencana uji, rollback dan urutan penerapan siap diteruskan ke AI lain dengan bukti nyata. DoR dinyatakan PASS hanya bila sumber Markdown + DOCX STEP05 yang detail sudah ada di repo V2 `main`, DOCX benar-benar file Word dapat dibuka, seluruh persyaratan sumber tervalidasi, diff final hanya planning, pemeriksaan CI/CodeQL/backend/Windows PASS, dan PR sudah merged.

**Penting:** PASS STEP05 **tidak sama dengan coding yang telah dilakukan**, tidak otomatis membuat fitur autosave v0.3.0 aktif, serta **bukan izin melakukan W06-A dalam giliran ini**. Setelah STEP05 PASS, user harus memberi perintah baru untuk memulai STEP06/W06-A. Seluruh wave SOL mengikuti implementasi test-first RED → GREEN → REGRESSION, dengan satu wave risiko per giliran, bukan satu perubahan masif.

## 02. Verifikasi kelengkapan dokumen wajib (source of truth)

| Gate dokumen | Artefak wajib di repo V2 | Keputusan dan pemeriksaan |
|---|---|---|
| G-05-00 | `docx/00_V2_0.3.0_PRODUCT_GAP_AUDIT_AND_RECOVERY_SCOPE.docx` + Markdown STEP00 | Ada di `main`; audit GAP-03A dan baseline |
| G-05-01 | `docx/01_V2_0.3.0_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.docx` + Markdown STEP01 | Ada di `main`; RCV-01..24, Save/Undo/Cancel |
| G-05-02 | `docx/02_V2_0.3.0_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.docx` + Markdown STEP02 | Ada; satu coordinator, single IO, sidecar digest |
| G-05-03A | `docx/03_V2_0.3.0_DIALOG_ONLY_SCOPE_REVISION.docx` + Markdown revisi | Ada; membatasi perubahan hanya 3 dialog |
| G-05-03B | `docx/03_V2_0.3.0_FINAL_APPROVED_UI_DIALOG_REFERENCES.docx` | Ada; 3 gambar disetujui tertanam, PR #54 |
| G-05-03C | `ui_step03_approved/UI-REC-DLG-01.png`, `-02.png`, `-03.png`, `UI-013_ACTUAL_REFERENCE.png` | Empat PNG tersedia dan memiliki Git blob pada main |
| G-05-03D | `03_STEP03_APPROVAL_RECORD.md` | Tertulis persetujuan eksplisit pengguna |
| G-05-04 | `docx/04_V2_0.3.0_RECOVERY_FAILURE_INJECTION_WINDOWS_TEST_PLAN.docx` + Markdown STEP04 | Ada di main; PR #55 sudah merged |
| G-05-05 | `docx/05_V2_0.3.0_IMPLEMENTATION_READINESS_AND_SOL_WAVE_PLAN.docx` + Markdown STEP05 | Wajib diciptakan dan diverifikasi sebelum PASS |

**Urutan otoritas:** `AGENTS.md` override terbaru → `V2_0.3.0_PLANNING_STATUS.md` paling atas → dokumen STEP05 ini → STEP04 (testing) → STEP03-R scope dan referensi final → STEP02 (arsitektur) → STEP01 (perilaku) → STEP00 (audit) → `docs/UI_FREEZE.md`, `docs/ARCHITECTURE.md`, `docs/PROJECT_STATE.md`. Teks lama yang mengatakan 13 PNG masih wajib / STEP03 belum disetujui merupakan arsip yang telah superseded; jangan menghidupkannya lagi.

**Persyaratan validasi lebih tinggi saat STEP06:** Git blob di main membuktikan adanya file, tetapi bukan pengganti pemeriksaan seluruh DOCX ter-render, tiga visual sesuai persetujuan, dan replay checksum bila artefak ditransfer. SOL wajib membaca dokumen ini dan referensi terkait sebelum mulai mengubah file.

## 03. Batas produk, komponen dan kontrak beku

1. **Satu proyek / satu history:** `ProjectSession` tetap satu-satunya pemilik ProjectState aktif, path, saved baseline dan Undo/Redo. Tidak membuat penyimpanan state paralel, serializer alternatif atau membenamkan autosave sebagai normal Save.
2. **Gunakan kembali komponen matang:** `src/aavc/persistence/recovery.py` (`RecoveryManager`) untuk snapshot/load/restore/clear, `persistence/serializer.py` untuk validasi/atomic replace, `GuardedMainWindow` untuk Save/Discard/Cancel, dan `FoundationServices` untuk dependency composition.
3. **Jadwal saat dirty tersimpan:** debounce 20 detik, eligibility cap 120 detik sejak dirty unsnapshotted pertama, dirty poll 60 detik, retry 30/120/≥300 detik; gunakan injected monotonic clock, tidak mengandalkan sleep-based unit test.
4. **File proyek tidak berubah karena autosave:** state tetap dirty, title `*` tetap sesuai keadaan, manual Save baseline tidak maju, undo/redo tidak bertambah, tidak mencipta proyek tanpa path disimpan.
5. **Snapshot dan descriptor sidecar:** `<project>.aavcproj.autosave` tetap serialized ProjectState (schema v3/v4), `.autosave.meta.json` memuat provenance versi 1 berukuran maks 16 KiB; SHA-256 adalah integritas bukan otentikasi/perlindungan dari penyerang.
6. **Operasi sensitif terserialisasi:** Save/Save As/Restore/Discard dan writer auto dibatasi fence/lease, epoch/generation; hash file dicek lagi tepat sebelum commit destruktif, bahkan jika jam file menunjukkan lebih baru.
7. **Restore aman:** preflight dan verifikasi ulang kandidat; backup unik `.pre-recovery[.N].bak` byte-identical, atomic replace dengan temp sibling, partial-commit ditampilkan jujur, tidak ada auto-restore.
8. **Cancel = zero mutation:** snapshot/proyek/metadata/Undo/Redo/current/path/selection/status terminal tetap aman; unsaved guard dijalankan *sebelum* recovery target.
9. **UI beku:** seluruh Home, editor, preview, timeline, panel AI/aset/properti, 42 referensi lama tetap 1:1. Hanya `UI-REC-DLG-01/02/03` baru; konflik memakai konfirmasi kedua *dalam komponen yang sama*; DLG-03 bergaya native QMessageBox. Autosave memakai QStatusBar lama dan unsaved dialog lama.
10. **Kesesuaian:** tidak membuat schema v5, mengubah 21 efek native, kontrak `advanced-v1`, Gemini credential model, subtitle, FFmpeg eksternal, Windows portable, release v0.2.2 atau repo asli.

## 04. Inventaris lokasi kode dan perubahan yang disyaratkan / dilarang

| Lokasi nyata di repo | Keputusan STEP05 untuk gelombang SOL | Guard terhadap perluasan tak sah |
|---|---|---|
| `src/aavc/application/services/project_session.py` | Tambah notifikasi revisi/proyek hanya bila terbukti perlu; jangan pecah history | Tidak mengubah semantik save/undo yang sudah tested |
| `src/aavc/persistence/recovery.py` | Extension terkecil untuk file/backup safe behaviors; reuse method lama | Tidak mengganti serializer atau menghapus backup lama |
| `src/aavc/persistence/serializer.py` | Reuse validasi/transaksi; perubahan hanya bila tes baru membuktikan missing seam | Schema max v4 tetap |
| `src/aavc/bootstrap/composition_root.py` | Komposisi satu coordinator/adapter tanpa instans ganda | Tidak membuat pekerjaan background lintas proyek tanpa owner |
| `src/aavc/bootstrap/startup.py` | Lifecycle start/teardown adapter bila perlu | Tidak memperlebar scope startup unrelated |
| `src/aavc/presentation/windows/guarded_main_window.py` | Urutan guard dan target preflight/Cancel regresi | Dialog lama tetap, tidak bypass guard |
| `src/aavc/presentation/windows/main_window.py` | Routing pilihan restore/discard, sambung status bar | Tidak rebuild shell / panel/timeline |
| `src/aavc/presentation/windows/background_work_window.py` | Integrasi aman dengan busy-close/background polling hanya jika perlu | Tidak memodifikasi render/AI job backend |
| `src/aavc/application/services/recovery_coordinator.py` (USULAN BARU) | Pure application orchestration, state, deadlines, epoch, choice token | Belum ada; wajib search-before-create dan ports jelas |
| `src/aavc/persistence/snapshot_provenance.py` (USULAN BARU) | Descriptor v1, validated hash, quarantine helper / atomic sidecar | Belum ada; must not persist secrets/raw body |
| `src/aavc/presentation/...` dialog/Qt timer adapter (USULAN) | Desain tiga dialog dan timer tipis; exact path diputuskan SOL setelah inspeksi struktur | Jangan menambah dialog 4–13 atau framework baru |
| `tests/unit/`, `tests/integration/` (path disesuaikan pola nyata repo) | Tambahkan test-first `RCV/SCH/AT/UI/COMP` secara berlapis | Jangan menghapus tes existing / menipu fake-clock |

Penamaan modul usulan bukan mandat mutlak; SOL wajib `search-before-create`, membandingkan helper yang tersedia dan mencatat alasan perubahan pada PR wave. Kode production dan tes runtime tidak boleh dibuat di STEP05.

## 05. Gelombang implementasi SOL — satu wave tiap giliran

| Wave | Modul fokus dan perilaku selesai | Gerbang penerimaan minimum | Dependency |
|---|---|---|---|
| W06-A | Coordinator murni aplikasi + jam monotonic injectable + dirty events/epoch, debouncer, cap, retry, single writer abstraction | `RCV-01..03,15,21,22`, `SCH-01..12` RED→GREEN, tidak import Qt di core | STEP05 PASS + instruksi STEP06 eksplisit |
| W06-B | Sidecar provenance, safe atomic snapshot/quarantine, schema validation, hash baseline, backup helpers | `RCV-11,12,14,17..20`, `AT-01..12`, canonical bytehash, secret scan | W06-A PASS |
| W06-C | Transaksi ProjectSession Save/Save As/Open/Restore/Discard, epoch fences, rollback/partial-commit, old guard precedence | `RCV-04..10,17,19,20,23,24`, `AT-13..20` dan error-code oracle | W06-B PASS |
| W06-D | Sambungan QTimer / status bar / tiga dialog Qt yang disetujui, guard dan keyboard/focus/Cancel | `RCV-07,10,15,16`, `UI-01..12`, offscreen actual screenshot parity | W06-C PASS |
| W06-E | Windows 11 portable, paket EXE, FFmpeg eksternal, path/credential/schema regression dan seluruh matriks | `COMP-01..10`, semua RCV/SCH/AT/UI, CI+CodeQL+Windows+backend | W06-D PASS |

**Setiap wave, wajib:** (i) cek head main/pra-syarat dan git diff wave sebelum mulai; (ii) buat tes yang secara jujur RED sebelum code baru (tanpa mematikan existing suite); (iii) implement minimum untuk GREEN; (iv) full relevant regression; (v) jalankan Windows acceptance yang tepat serta CodeQL sebelum merge; (vi) PR satu wave, merge hanya pada final-head green; (vii) bukti changed paths / rollback SHA dan ringkasan PASS/FAIL; (viii) BERHENTI sampai user berkata 'lanjutkan' untuk wave berikutnya. Status baru dianggap COMPLETE setelah merge ke main, bukan setelah commit branch.

Jika wave pertama masih menyisakan kontrak/semantik ambigu, **STOP dan naikkan kembali ke ASTRA** untuk keputusan DOCX architecture; jangan mengambil jalan pintas implementasi. Jangan klaim Windows portable telah menjalankan fitur sebelum tes wave memang ada.

## 06. Definisi acceptance, cakupan dan keterlacakan uji

| Kelompok STEP04 | Jumlah kasus | Oracle/hasil untuk SOL | Wave utama |
|---|---|---|---|
| RCV-01..24 | 24 | Alur fungsional simpan, snapshot, restore, discard, Cancel, konflik, schema | Semua sesuai case map |
| SCH-01..12 | 12 | Fake clock 20/120/60, retry, no overlap, stale epoch; tanpa sleep | W06-A |
| AT-01..20 | 20 | Bytehash BEFORE/AFTER; crash split sidecar; backup; rollback; race | W06-B dan C |
| UI-01..12 | 12 | Guard order, focus Escape/Enter, string Indonesia, frozen UI parity | W06-D |
| COMP-01..10 | 10 | v3/v4, advanced-v1, Windows deep/Unicode paths, portable, FFmpeg, secrets | W06-E |

**Proof record per case:** `case_id`, fixture sintetis, deterministic seed, fake-clock ticks, injected fault point, operating system/build, session fingerprint before/after, project/sidecar/snapshot/backup SHA-256 before/after, writer and dialog counts, sanitized error ID, RED/GREEN status, affected commit, execution log/artifact URL, final PASS/FAIL. Tidak unggah proyek pribadi, API key nyata, isi narasi atau path home Windows yang sensitif.

**Trigger failure classes:** write/read fsync, atomic replace/rename, data truncated, Windows exclusive lock, permission denied, destination collision, AV interference, process abort between autosave and metadata, after durable Restore but before session adopt, stale callbacks after Save/Save As, hash changed during modal, future-schema candidate and symlink/junction alias. Expected fail-closed evidence must explicitly cover which files *might* have changed in a partial commit.

**Stop rules:** any failed cancellation-zero-mutation, silent disk overwrite, key leakage, backup overwritten, schema migration, Undo stack lost, failed Restore misreported success, dirty cleared by autosave, duplicate open decision, UI frozen-screen regression, or missing `RCV` evidence blocks merge. Do not downgrade to warning to force a green status.

## 07. Kebijakan keamanan, crash consistency dan keterbatasan yang jujur

- SHA-256 on disk and sidecar protects against accidental mismatch only. Path hashes are neither secret nor authenticated; symlink/junction aliases and cross-process edits need conservative compare-and-swap immediately before commit.
- Snapshot + metadata is two-file protocol; interrupted metadata publication must lead to `RECOVERABLE_UNCERTAIN`, never Verified solely from modified timestamps.
- Windows fsync/directory durability differs from POSIX; **jangan klaim tahan terhadap semua power loss** tanpa pengujian daya dan Windows-native durability evidence.
- Abort hard after disk replace can legitimately leave durable replaced disk and prior live session in memory; report `RESTORE_COMMIT_PARTIAL`, backup still accessible and never claim disk unchanged.
- Unsupported/readonly/cloud-synced/network paths require documented limitations. Do not silently retry writing to unrelated path.
- Zero real API keys/tokens in `.aavcproj`, autosave, metadata, logs, screenshots, CI artifacts or portable ZIP. Tests use synthetic canary only.
- Never delete arbitrary temp/sidecar files; only files proved as current transaction ownership. Save As must not delete another project's candidate or old-path autosave.

## 08. Checklist gerbang DoR STEP05

| ID | Syarat PASS | Bukti minimum |
|---|---|---|
| DOR-01 | Semua DOCX 00/01/02/03 scope/03 final UI/04/05 ada dan valid di main | Tree Git blob, ukuran nonzero; DOCX valid OOXML; render QA dokumen baru |
| DOR-02 | 3 PNG final dan editor reference + record user approval ada | 4 PNG, record file, PR #54 merged |
| DOR-03 | Keselarasan STEP01–04, tanpa kontrak 13 PNG lama | STEP05 precedence index / review keputusan |
| DOR-04 | Wave plan dan exact test traceability | W06-A..E + RCV/SCH/AT/UI/COMP |
| DOR-05 | Baseline/preservation | stable `v0.2.2` tag unchanged, legacy repo untouched |
| DOR-06 | Tidak ada kode selama STEP05 | diff hanya Markdown/DOCX / generator documentation-only; no tests, source, package/workflow permanent changed |
| DOR-07 | DOCX STEP05 selesai dan dapat dibuka | render visual tiap halaman; layout/word-archive QA |
| DOR-08 | PR STEP05 full green & merged | CI, CodeQL, Windows acceptance, backend; PR head SHA dan main merge SHA |
| DOR-09 | Gate STEP06 tetap terkunci | User instruction baru diperlukan sesudah STEP05 PASS |

**Aturan jika gagal:** status `STEP05 HOLD/FAIL`, catat masalah, perbaiki hanya dokumen/PR STEP05 yang diizinkan, periksa ulang. Jangan pernah menganggap dokumen di chat atau artifact Actions (tanpa file commit main) sebagai bukti cukup. Jika satu dari enam DOCX utama rusak/hilang atau UI final tidak cocok, stop dan lakukan pemulihan sumber plan terlebih dahulu.

## 09. Rencana handoff ke SOL dan formulir status wave

Perintah kerja SOL yang **baru boleh dipakai di STEP06** (setelah DoR PASS + user memerintah lanjutkan): "Kerjakan W06-A pada repo V2-AI-Video-Composer berdasarkan STEP05, STEP04 dan kontrak STEP01–03. Pertama tulis tests RED scheduler/coordinator; pertahankan ProjectSession/RecoveryManager, tanpa perubahan UI; tampilkan diff, jalankan pengujian, PR, dan laporkan PASS/FAIL. Jangan mengerjakan W06-B sebelum perintah baru." Jangan kirim perintah itu secara otomatis pada giliran STEP05.

**Template laporan wave:** `Wave ID`, `baseline SHA`, `files changed`, `tests RED evidence`, `GREEN evidence`, `full regression`, `Windows/CodeQL`, `PR URL and merged SHA`, `rollback SHA`, `remaining risks`, `GATE PASS/FAIL`, `NEXT wave but not started`. DOCX baru tidak wajib per wave implementasi kecuali keputusan besar arsitektur, kontrak keselamatan atau UI beku berubah.

**Berita acara sumber otoritatif pada awal STEP06:** setelah user memerintah, SOL mengambil `main` terbaru, memastikan `v0.2.2` immutable, membuka gambar final/DOCX STEP03, memeriksa semua DOCX STEP00–05, menginventarisir tes existing (termasuk `tests/unit/test_step11_persistence_recovery.py`, `tests/unit/test_project_session.py`, `tests/unit/test_v2_0_2_2_persistence_recovery_safety.py`), dan menulis perintah acceptance W06-A sebelum kode.

## 10. Keputusan akhir STEP05 / gerbang berhenti

**Target hasil:** `STEP05 COMPLETE / PASS — READY FOR SEPARATELY AUTHORIZED STEP06 W06-A`. Ini hanya boleh dilaporkan setelah artefak DOCX benar-benar ada dalam `main`, PR final-head checks PASS, dan tag stabil tidak berubah. Sampai syarat itu terbukti, statusnya `STEP05 IN PROGRESS` atau `HOLD`.

**HARD STOP:** Tidak membuat/mengedit source produksi/tes runtime atau Qt pada STEP05. Tidak memulai STEP06 meskipun PR STEP05 berhasil; instruksi `lanjutkan` yang diberikan saat mulai STEP05 tidak mengizinkan STEP06 dalam giliran yang sama. W06-B–E tetap blokir hingga wave sebelumnya green/merged dan perintah berikutnya.

**Referensi internal:** PR #54 (approved UI), PR #55 (STEP04), `AGENTS.md`, `V2_0.3.0_PLANNING_STATUS.md`, `docs/v2_0_3_0_planning/00_PRODUCT_GAP_AUDIT_AND_RECOVERY_SCOPE.md`, `01_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.md`, `02_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.md`, `03_STEP03_DIALOG_ONLY_UI_SCOPE_REVISION.md`, `03_STEP03_APPROVAL_RECORD.md`, `04_RECOVERY_FAILURE_INJECTION_WINDOWS_TEST_PLAN.md`, plus frozen docs (`UI_FREEZE`, `PROJECT_STATE`, `CODE_CONSTITUTION`, `ARCHITECTURE`).