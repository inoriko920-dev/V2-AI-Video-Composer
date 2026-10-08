# STEP 04 — Rencana Pengujian Recovery, Failure-Injection, Windows dan Kompatibilitas

**Proyek:** V2 AI Video Composer • **Siklus:** v0.3.0 (rencana, bukan versi rilis) • **Tanggal:** 8 Oktober 2026 WIB  
**Repositori tunggal:** `inoriko920-dev/V2-AI-Video-Composer` • **Peran:** ASTRA / perencanaan saja  
**Baseline sebelum STEP 04:** `main` commit `180a05068572505540ba17a09c6b9c666d6a8ebe` (PR #54 merged); stable `v0.2.2` commit `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef` (wajib tidak berubah).  
**Status dokumen:** SPECIFICATION ONLY. Belum ada test baru, mock fault atau kode aplikasi yang diimplementasikan. STEP 05 memerlukan perintah terpisah; STEP 06/SOL coding tetap terlarang.

## 1. Ringkasan keputusan dan ruang lingkup

STEP 04 mengubah kontrak fungsional STEP 01 dan arsitektur STEP 02 menjadi rencana pengujian deterministik, dengan penekanan pada **tidak kehilangan data, fail closed, kemampuan rollback, pembuktian satu penulis, dan UX tetap identik dengan referensi yang disetujui**. Tiga dialog final `UI-REC-DLG-01/02/03`, screenshot editor asli `UI-013_ACTUAL_REFERENCE.png`, dan DOCX final `03_V2_0.3.0_FINAL_APPROVED_UI_DIALOG_REFERENCES.docx` dari PR #54 adalah sumber otoritatif. Tidak boleh menggambar ulang 42 UI lama; status autosave memakai `QStatusBar` lama dan guard Save/Discard/Cancel memakai `GuardedMainWindow`/`QMessageBox` lama.

Rencana ini **bukan** hasil eksekusi pengujian fitur baru. Setiap kasus di bawah ini ditulis sebagai tes masa depan dengan urutan RED (gagal sebelum implementasi), GREEN (setelah implementasi), dan REGRESSION (setelah refaktor). Hanya pemeriksaan kualitas dokumen/perubahan docs yang boleh dijalankan di STEP 04. Tidak mengubah sumber Python/PySide6, serializer, schema, animasi, FFmpeg, CI permanen, dependensi runtime, tag atau release.

### 1.1 Referensi otoritatif dan cara menangani pertentangan

1. `AGENTS.md` bagian v0.3.0 override, lalu `V2_0.3.0_PLANNING_STATUS.md` bagian paling atas yang terbaru.
2. `00_PRODUCT_GAP_AUDIT_AND_RECOVERY_SCOPE.md` — tujuan GAP-03A; `01_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.md` — perilaku Save/Restore dan RCV-01..24.
3. `02_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.md` — coordinator, serial IO, format sidecar metadata, commit/fence/rollback.
4. `03_STEP03_DIALOG_ONLY_UI_SCOPE_REVISION.md`, approval record dan satu DOCX UI final yang sudah digabung melalui PR #54.
5. `docs/UI_FREEZE.md`, `docs/PROJECT_STATE.md`, `docs/ARCHITECTURE.md`, `docs/CODE_CONSTITUTION.md` dan pengujian v0.2.2 yang telah ada.

Jika teks arsip lama mengatakan memerlukan 13 PNG atau STEP03 belum disetujui, **abaikan untuk keputusan terkini**: PR #53 mengganti jumlah menjadi 3, PR #54 menutup persetujuan. Jika satu kontrak pengujian tidak jelas, tandai keputusan terbuka untuk STEP05; jangan mengubah spesifikasi dengan dugaan tester.

## 2. Peta kode yang sudah ada dan batas implementasi

| Lokasi sumber yang sudah diverifikasi | Tanggung jawab saat ini | Apa yang diuji nanti; jangan ubah di STEP04 |
|---|---|---|
| `src/aavc/persistence/recovery.py` | `RecoveryManager`: write/load/restore/clear snapshot; exclusive numbered pre-recovery backup | Validasi sebelum replace, backup tidak tertimpa, temp dibersihkan, kegagalan izin/copy/replace |
| `src/aavc/application/services/project_session.py` | Satu project aktif; `path`, saved baseline, `is_dirty`, `execute`, `undo`, `redo`, `save`, `open` | Autosave tidak mengganti baseline/dirty/history; Save/Save As baru rebind setelah sukses |
| `src/aavc/presentation/windows/guarded_main_window.py` | Guard perubahan belum disimpan dan busy-close | Precedence guard sebelum probe recovery; Cancel zero-mutation |
| `src/aavc/bootstrap/composition_root.py` dan `startup.py` | Pemilik lifecycle aplikasi dan service | Satu coordinator, worker/timer ditutup bersih, tak ada callback orphan |
| `src/aavc/presentation/windows/main_window.py` | Aksi proyek dan shell editor | Dialog sesuai approved PNG tanpa mengubah shell |
| `src/aavc/persistence/serializer.py` | Validasi project, temp sibling dan atomic replace | Byte-compare, schema v3/v4, future-schema reject, corrupt destination guard |

Prinsip yang harus dibuktikan: **presentation → application coordinator → persistence adapters**. `RecoveryCoordinator`, `SnapshotProvenanceStore`, scheduler dan fault seam adalah rancangan STEP02 untuk tahap implementasi mendatang, **belum boleh dianggap sudah dibuat**. Tidak boleh membuat history kedua, serializer lain, provider baru atau skema v5.

## 3. Model keselamatan dan oracle pemeriksaan

Setiap pengujian yang berpotensi memodifikasi disk mengambil `BEFORE` dan `AFTER` untuk: (A) byte SHA-256 proyek target; (B) autosave; (C) `.autosave.meta.json`; (D) semua `.pre-recovery[.N].bak`; (E) file karantina; (F) daftar temp sibling; (G) current/path/is_dirty/saved-baseline/Undo/Redo, pilihan scene dan window title; (H) generasi/epoch, revisi captured, status scheduler, jumlah writer dan dialog aktif. **Tidak cukup hanya memeriksa pesan UI atau jumlah file**.

### 3.1 Hasil yang diharapkan per tindakan

- **Probe saja:** 0 perubahan pada file dan sesi; tidak memanggil Save/Restore/Discard.
- **Cancel/Escape:** semua hash, sesi aktif, history dan pemilihan tetap sama; cancel menutup dialog dan kembali ke fokus yang tepat.
- **Snapshot berhasil:** proyek asli identik byte-for-byte; dirty tetap true; Undo/Redo tidak bertambah; `last_success_revision` hanya naik untuk epoch yang masih cocok.
- **Restore berhasil:** candidate valid dan disk direvalidasi; backup unik menyimpan proyek lama **byte-for-byte**; disk berisi isi snapshot valid; history sesi proyek target segar; aksi hanya sekali.
- **Restore gagal sebelum `replace`:** disk lama sama persis, candidate dan backup sah bertahan, temp milik operasi dibersihkan.
- **Restore gagal setelah replace:** tidak boleh mengklaim disk belum berubah; kondisi `RESTORE_COMMIT_PARTIAL` dan backup asli harus terlapor jelas.
- **Discard berhasil:** proyek tersimpan dibuka setelah pemindahan snapshot milik target ke karantina dengan aman; tidak menyentuh snapshot lain.
- **Save sukses:** saved baseline maju, tidak ada kandidat lama yang ditawarkan sebagai verified setelah save; kegagalan pembersihan dilaporkan tanpa membatalkan Save.
- **Save gagal:** path/baseline/dirty/proyek asli/candidate tetap; tidak ada status 'Tersimpan'.

### 3.2 Fixture dan jejak bukti

Gunakan proyek sintetis nonpribadi: proyek kecil v3, v4 advanced-v1 dengan beberapa assignment, edit yang Undo ke v3, proyek 10/100/500 scene untuk **ukuran serialized-state/perencanaan**, kandidat valid/equal/legacy-without-meta/corrupt/future, file eksisting read-only, nama Unicode, apostrof/spasi, serta sidecar palsu. Isi fixture **tidak boleh** mengandung API key asli, token nyata, dokumen pengguna, footage berhak cipta, atau direktori pribadi. Beri fixture ID eksplisit seperti `FX-V3-BASE`, `FX-V4-ADV`, `FX-LEGACY-AUTOSAVE`, `FX-CORRUPT-PROJECT`, `FX-UNTRUSTED-META`, `FX-UNICODE-PATH`.

Artifact bukti minimal tiap tes: `case_id`, fixture ID, seed, fake-clock ticks, fault-point, target OS, hash BEFORE/AFTER, exception/error code yang disanitasi, jumlah writer, final session fingerprint, hasil PASS/FAIL, serta lokasi screenshot jika terkait UI. **Jangan** unggah raw proyek pengguna, absolute path rumah pengguna, token atau file sementara berisi data sensitif ke Actions artifacts. Untuk jalur yang bisa dibaca pihak lain, gunakan project path sintetis terpotong/terhash.

## 4. Kebijakan jadwal dan pengujian fake clock

Kontrak STEP01/02: debounce satu kali **20 detik** setelah edit bermakna terakhir; batas kelayakan sejak dirty pertama **120 detik**, poll kotor **60 detik**; retry setelah gagal **30 s**, berikut **120 s**, kemudian **minimal 300 s**. Deadline `min(last_edit+20, first_dirty+120)` adalah batas *eligible* untuk menjadwalkan, **bukan janji bahwa disk IO selesai 120 detik**. Ada satu global snapshot writer dan satu path lease aktif per target. Edit Undo/Redo mengubah revision, sedangkan hover, selection, playback tick, repaint dan no-op tidak.

Fake clock wajib diinjeksi melalui port monotonic dari STEP02, tanpa `time.sleep` untuk tes deterministik. Event queue harus bisa dijalankan urut dan dimajukan ke `t=19.999`, `t=20.000`, `t=119.999`, `t=120.000`, `t=60` dan retry ke `30/120/300`; timer callback membawa epoch dan revision. Clock wall time yang lompat tidak boleh memicu snapshot baru, melewati retry atau menganggap snapshot lebih baru.

| ID | Jadwal/situasi | Oracle deterministik |
|---|---|---|
| SCH-01 | Satu edit dirty pada t=0 | Tidak ada write sebelum due; tepat satu eligible pada t=20 |
| SCH-02 | Edit beruntun t=0, 10, 18 | Debounce bergeser; tidak 3 write; eligible pada t=38 kecuali cap |
| SCH-03 | Edit terus-menerus setiap 5 detik >120 | Eligible pada t=120; tanpa starvation; tetap satu writer |
| SCH-04 | Tidak ada edit saat clean atau path None | Nol serialisasi/disk write/timer progress palsu |
| SCH-05 | Undo mengembalikan state = saved baseline | Pending snapshot dibatalkan; tak ada write |
| SCH-06 | Write aktif; muncul revisi baru | Revisi baru tidak hilang, last-success lama tidak menghapus dirty baru |
| SCH-07 | Callback epoch A selesai setelah ganti proyek B | Tidak mengubah status B/tulis B; callback A dianggap stale |
| SCH-08 | Gagal 3 kali, lanjut idle | Retry 30/120/≥300; tidak loop cepat atau spam modal |
| SCH-09 | Wall clock mundur/maju ekstrem | Monotonic due tetap benar; timestamp tidak jadi sumber freshness |
| SCH-10 | Modal open/restore/close atau writer busy | Timer tidak memulai operasi terlarang; due tertunda secara aman |
| SCH-11 | Housekeeping 60 detik saat dirty, namun digest sama | Tidak membuat file duplikat atau menyatakan progress palsu |
| SCH-12 | Retry success setelah failure lalu edit baru | Backoff reset, deadline baru dihitung sesuai revisi terbaru |

## 5. Matriks penerimaan wajib RCV-01 sampai RCV-24

Kolom 'Test seam' adalah **usulan antarmuka injeksi yang baru boleh dikodekan STEP06 setelah izin STEP05**, bukan API yang sudah ada. Setiap case wajib punya fixture, setup, aksi, assertion, teardown, dan hasil RED→GREEN.

| ID | Kasus / stimuli | Assertion utama | Jenis bukti |
|---|---|---|---|
| RCV-01 | Proyek tersimpan dirty, snapshot eligible | Autosave valid; manual project hash sama; dirty+Undo tidak berubah | fake-clock + hash |
| RCV-02 | Clean / no path / no project | Tidak ada file baru, no-op callback | FS spy |
| RCV-03 | Debounce 20, cap 120, poll 60, serial single writer | Tick deterministik dan max active writer=1 | scheduler trace |
| RCV-04 | Save manual sukses dengan kandidat lama | Kandidat tidak muncul sebagai verified sesudah Save | crash-window |
| RCV-05 | Save gagal / permission | Disk dan candidate aman; saved baseline tak berubah | injected repository error |
| RCV-06 | Save As rebind saat ada sidecar lain | Target sidecar lain aman; path berubah hanya sesudah sukses | collision matrix |
| RCV-07 | Proyek dan autosave valid berbeda | Tepat satu DLG-01; tak ada write sebelum user memilih | Qt offscreen + hash |
| RCV-08 | Restore valid | Pre-recovery backup unik; disk setara candidate; history sesi segar | byte diff |
| RCV-09 | Discard target valid | Hanya sidecar target dikarantina; proyek tersimpan utuh | quarantine fault |
| RCV-10 | Cancel dari proyek lama dirty | path, state, history, disk dan pilihan scene identik | fingerprint |
| RCV-11 | Autosave corrupt / future / tak bisa dibaca | Tidak auto-restore; kandidat tak dihapus | schema/fault |
| RCV-12 | v3/v4 dan Undo dormant advanced tracks | Skema tidak promosi diam-diam; advanced-v1 utuh | schema fixture |
| RCV-13 | Unicode, apostrof, spasi, path dalam, lock/full | Fail closed, byte safe di Windows | Windows integration |
| RCV-14 | Canary token Gemini sintetis | Tidak masuk snapshot/meta/log/artifact | scan canary |
| RCV-15 | 2+ dialog, shutdown, switch, delayed events | Max satu dialog; tak ada callback orphan/race | Qt lifecycle |
| RCV-16 | Qt offscreen + packaged portable EXE | Build/launch/smoke dan full CI PASS setelah implementasi | Actions artifacts |
| RCV-17 | Disk/snapshot hash berubah antara prompt dan klik | Token invalid; `RECOVERY_RACE_CHANGED`; no mutation | race barrier |
| RCV-18 | Autosave v0.2.2 tanpa metadata | `RECOVERABLE_UNCERTAIN`; DLG-02, bukan verified | legacy fixture |
| RCV-19 | Save berhasil tapi crash sebelum snapshot cleanup | Stale candidate tidak dipulihkan otomatis | killpoint/save |
| RCV-20 | Proses lain ubah disk sebelum restore | No overwrite; dialog konflik/re-probe | external writer |
| RCV-21 | No-op edit, paint/playback, state equal | Tidak memicu write | scheduler event audit |
| RCV-22 | Snapshot in-flight setelah Save fence | Tidak membangkitkan kembali kandidat 'baru' | interleaving barrier |
| RCV-23 | Open target dari sesi lama dirty | Guard Save/Discard/Cancel selalu mendahului dialog target | Qt interaction |
| RCV-24 | Save As ke target baru/occupied, old snapshot | Tidak menghapus/mengganti snapshot proyek lain | path ownership |

**Exit RCV:** Setiap ID wajib ada tes parametrik terpisah atau subcase eksplisit dengan nama mudah dicari, laporan Oracle BEFORE/AFTER, dan hasil RED yang membuktikan kekosongan fungsi sebelum implementasi. Jangan menulis PASS v0.3.0 berdasarkan tes engine v0.2.2 yang ada.

## 6. Matriks atomicity, metadata dan crash window

Format yang direncanakan STEP02: `<project>.aavcproj.autosave` tetap JSON `ProjectState`; sidecar `<project>.aavcproj.autosave.meta.json` adalah JSON terpisah, maksimal **16 KiB**, dengan `format_version=1`, path identity berupa digest, `saved_baseline_sha256`, `snapshot_sha256`, `schema_version` dan penanda operasi non-secret. Dua file tersebut **tidak mempunyai atomicity lintas dua-file**. Digest mencegah mismatch tidak sengaja, **bukan bukti autentikasi melawan pihak yang dapat menulis keduanya**. Kandidat dengan sidecar hilang, stale, atau rusak harus *uncertain* atau *invalid*, tidak pernah verified otomatis.

| ID | Fault / momen injeksi | Ekspektasi yang boleh diklaim |
|---|---|---|
| AT-01 | Sebelum snapshot temp dibuat | Original project dan kandidat valid terdahulu tetap |
| AT-02 | Saat menulis sebagian temp `.autosave` | Tidak pernah terpublikasi sebagai valid; temp dapat dibersihkan |
| AT-03 | Snapshot replace sukses, sidecar belum ditulis lalu kill | Snapshot baru vs meta lama = uncertain, bukan verified |
| AT-04 | Meta temp menulis parsial | Descriptor parsial tak dipakai; snapshot tetap ditandai uncertain |
| AT-05 | Meta replace selesai, project disk baseline berbeda | Baseline mismatch => conflict meski candidate digest cocok |
| AT-06 | Descriptor >16 KiB/format_version tidak dikenal/jenis salah | Fail closed, tidak menghapus autosave |
| AT-07 | Snapshot JSON future schema v5 atau korup | Tidak mengubah original/backup, pesan DLG-03 |
| AT-08 | Legacy autosave tanpa meta | DLG-02 dan konfirmasi ekstra; Cancel default |
| AT-09 | Descriptor cocok tetapi path alias/symlink/junction | Ownership recheck; tidak menimpa proyek lain |
| AT-10 | Disk berubah setelah preflight sebelum confirm | Digest recheck menolak token lama |
| AT-11 | Snapshot berubah setelah preflight sebelum confirm | Hasil sama: `RACE_CHANGED`, tidak memproses stale choice |
| AT-12 | Dua restore bersamaan melawan satu path | Paling banyak satu durable replace dan backup; kedua gagal/re-probe |
| AT-13 | Backup `.pre-recovery.bak` sudah ada | Backup bernomor baru, backup lama SHA256 identik |
| AT-14 | Backup copy gagal tengah jalan | Backup parsial milik operasi dibersihkan; disk tidak diganti |
| AT-15 | `temp.replace(project)` gagal setelah backup sukses | Disk lama identik; backup valid tidak hilang; candidate tetap |
| AT-16 | Disk sudah diganti, ProjectSession.open gagal | `RESTORE_COMMIT_PARTIAL`; jujur bahwa disk mungkin berubah |
| AT-17 | Quarantine rename sukses, sesi target gagal diadopsi | Rollback quarantine bila aman; jika gagal, lokasi aman dilaporkan |
| AT-18 | Save As target memiliki descriptor milik proyek lain | Abort dengan `SAVE_AS_RECOVERY_COLLISION` |
| AT-19 | Success Save lalu stale worker selesai | Fence mencegah resurrected verified candidate |
| AT-20 | Power loss sebelum data/dir fsync pada Windows | Klaim sebatas evidence hasil tes; **tidak** menjanjikan ketahanan listrik mutlak |

### 6.1 Titik fault seam yang dibutuhkan, bukan patch sekarang

Rancang fault seam pada operasi port filesystem yang nanti diimplementasikan: `read_project_bytes`, `read_snapshot_bytes`, `open_temp`, `write_some`, `flush`, `fsync_file`, `replace`, `exclusive_backup_create`, `backup_copy`, `meta_replace`, `quarantine_rename`, `retire_snapshot`, `load_after_restore` dan `session_commit`. Satu fault per kasus dan kombinasi bergilir untuk rollback; exception sintetis berlabel, tidak memakai monkeypatch global `Path.unlink` untuk seluruh disk. Untuk race, gunakan `threading.Event` / controlled executor barrier, tidak mengandalkan sleep dan probabilitas timing.

## 7. Matriks session transaction, guard dan UI yang disetujui

| ID | Prosedur | Hasil yang harus terlihat |
|---|---|---|
| UI-01 | Open A dengan autosave verified dari sesi clean | DLG-01 berbahasa Indonesia, Batal default, tiga pilihan tepat |
| UI-02 | Open A metadata invalid/legacy/baseline beda | DLG-02 dan peringatan; 'Periksa dan Pulihkan' harus memerlukan konfirmasi kedua dalam komponen yang sama |
| UI-03 | Open A autosave corrupt | DLG-03, hanya 'Buka Proyek Tersimpan' + Batal; tidak ada Restore |
| UI-04 | Tekan Escape dan tombol Batal pada ketiga dialog | Identik dengan preflight fingerprint; tidak ada write |
| UI-05 | Enter saat fokus default pada DLG-02 | Tidak memicu Restore langsung; default aman Batal |
| UI-06 | Keyboard Tab/Shift-Tab, Alt+F4, layar kecil/DPI scaling | Fokus jelas, dialog tidak terpotong/menyembunyikan aksi aman |
| UI-07 | Guard sesi B dirty lalu pilih Open A | Guard lama muncul dulu; Cancel guard berarti dialog A tidak pernah ditampilkan |
| UI-08 | Status 'Cadangan otomatis dibuat' saat proyek dirty | Judul dirty `*` tetap; bukan 'Proyek disimpan'; Undo tak berubah |
| UI-09 | Status gagal/menunggu/menulis tanpa saved path | QStatusBar lama, nonmodal dan tidak menggeser preview/timeline |
| UI-10 | Dua klik Open bersamaan / dialog berulang | Satu transaksi; tidak ada pemulihan dua kali |
| UI-11 | Backdrop perbandingan di UI-013 asli | Tidak mengubah toolbar, kiri/tengah/kanan/timeline; visual-diff hanya modal/scrim |
| UI-12 | Cancel close dengan render/job busy | Busy guard lebih dulu; tidak lahir timer/dialog baru setelah close |

Setiap screenshot acceptance dibandingkan dengan **reference yang benar**: `UI-002_ACTUAL.png` adalah Home, sedangkan `UI-013_ACTUAL.png` adalah editor. Perbandingan piksel tidak boleh menganggap anti-aliasing, DPI atau sistem font sebagai perubahan fungsional; bedakan hard requirement (layout/shell unchanged, exact text/button/focus) dari minor platform variation. Visual PNG adalah otoritas desain, sedangkan tes Qt interaktif membuktikan perilaku, bukan gambar statis.

## 8. Kompatibilitas data dan perlindungan versi

| ID | Masukan | Harus dipertahankan |
|---|---|---|
| COMP-01 | ProjectState v3 normal | Tetap v3 setelah autosave; no schema promotion |
| COMP-02 | Advanced v4 `animation_keyframe_contract=advanced-v1` | Semua keyframe dan 21 efek native tetap sama |
| COMP-03 | Undo state advanced-v4 kembali valid-v3 | Snapshot v3 diperbolehkan tanpa menulis proyek v4 secara diam-diam |
| COMP-04 | Autosave v3 terhadap disk v4 | Restore hanya setelah user consent dan backup byte-v4 dibuat |
| COMP-05 | Snapshot future schema / corrupted advanced markers | Reject, preserve source, no implicit migration |
| COMP-06 | API/model settings, Gemini key store, render defaults | Tak disalin ke project/autosave/meta jika sebelumnya terpisah |
| COMP-07 | Buka file disimpan v0.2.2, tanpa sidecar | Backward compatible; kandidat autosave lama = uncertain |
| COMP-08 | Save As ke path project v4 ketika in-memory v3 | Existing schema downgrade guard aktif; tidak auto-overwrite |
| COMP-09 | Project dengan scene/subtitle/font Unicode | Unicode parse/re-serialize dan identity tidak rusak |
| COMP-10 | Snapshot user project banyak scene | Waktu serialisasi diukur, status UI responsif; tidak klaim render selesai |

## 9. Windows 11 portable, filesystem dan performa

**Lingkungan bukti:** Windows runner untuk automasi, lalu acceptance Windows 11 nyata untuk area yang tidak terwakili oleh runner. Gunakan Python/Qt build portable `onedir` dari sumber commit PR yang sama; EXE smoke, app-local configuration, FFmpeg/ffprobe **eksternal** tetap baseline v0.2.2. Tidak menambahkan `ffmpeg.exe` ke ZIP, tidak memodifikasi rilis stabil.

**Path matrix:** direktori dengan `C:\QA\Video Projek\`, `D:\Pekerjaan O'Neil\`, `C:\QA\Bojonegoro_汉字_é_日本語\`, nama lebih panjang dari MAX_PATH bila OS mendukung, Windows `\?\` prefix, share UNC jaringan, folder bersifat read-only dan folder yang disinkronkan. **Klaim dukungan hanya untuk kombinasi yang benar-benar diuji**; network/symlink/junction/reparse point dan AV interference bisa menjadi limitasi terdokumentasi, bukan janji otomatis.

**Kegagalan OS:** sharing violation/lock, ransomware-protected folder, disk-full/quota, permission-denied, rename/copy interrupted, read-only metadata, modifikasi eksternal saat dialog, symlink/junction pointing outside fixture, serta shutdown/cancel saat writer aktif. Test harus bekerja dalam folder sandbox/fixture, tidak pernah sengaja memenuhi disk utama atau menyasar data nyata pengguna.

**Kinerja yang harus dicatat (benchmark bukan limit belum disetujui):** `autosave_capture_ms`, `serialize_ms`, `write_ms`, `metadata_ms`, `restore_ms`, `dialog_latency_ms`, `ui_heartbeat_gap_ms`, `snapshot_bytes` untuk proyek 10/100/500 scene, 3 repetisi atau lebih, mesin/runner tercatat, median dan p95 bila sampel cukup. Jika langkah besar membuat UI macet, status **FAIL/NEEDS DESIGN** tanpa otomatis memperlonggar 20/120/60 detik. Tes konstruksi perintah 500 scene bukan bukti render 500 scene.

## 10. Keamanan, privasi, rahasia dan provenance

- Canary sintetis dengan pola `AIza...` palsu dan `TEST-ONLY-NOT-A-SECRET` diuji pada project, autosave, metadata, JSON logger, screenshot test, diagnostic ZIP, CI logs, serta binary distribution. Tidak gunakan token real.
- Sidecar path identity digest tidak memberikan anonimitas absolut atau autentikasi kriptografis; tahapan threat model memeriksa risiko path brute-force dan forged two-file pair. Kontrol utama di tahap ini adalah fail-closed baseline/identity recheck, bukan enkripsi baru.
- Batas descriptor 16 KiB; JSON type/UTF-8/schema_version/input length dijaga. Hindari path traversal ketika quarantine/backup; hanya path turunan dari target yang sudah divalidasi.
- Semua fault message ditangkap sebagai error code seperti `BASELINE_CHANGED`, `AUTOSAVE_META_UNCERTAIN`, `RECOVERY_RACE_CHANGED`, `RESTORE_BACKUP_FAILED`, `RESTORE_COMMIT_PARTIAL`, `DISCARD_QUARANTINE_FAILED`; UI tidak menampilkan raw exception/stack trace/absolute private path.
- Jangan melaporkan 'snapshot tersimpan ke cloud', 'pasti dapat dipulihkan', atau 'selamat dari pemadaman listrik' tanpa implementasi dan bukti terpisah.
- Scan artefak Windows ZIP dan source output untuk secret canary; build rilis hanya setelah STEP07 disetujui. Stable v0.2.2 checksum/tag tidak boleh berubah.

## 11. Urutan pengerjaan test-first yang direkomendasikan untuk STEP06 (belum dijalankan)

| Wave rencana | RED awal dan seam minimal | GREEN paling sempit | Bukti wajib sebelum wave berikutnya |
|---|---|---|---|
| W06-A | SCH-01..12, RCV-01..03, 21..22 | Coordinator + fake clock, epoch, single writer | Pure unit, coverage branch, no Qt IO |
| W06-B | AT-01..11, RCV-11..12,18..20 | Metadata store dan recovery validation | Hash byte/sidecar/crash consistency; secret scan |
| W06-C | AT-12..19, RCV-04..10,17,23..24 | Serialize Save/Open/Restore/Discard/Save As | No-data-loss session fingerprints dan rollback |
| W06-D | UI-01..12, RCV-07,10,15 | Dialog asli approved + QStatusBar + guarded wiring | Qt offscreen+actual screenshot parity |
| W06-E | RCV-13..16, COMP, Windows OS matrix | Portable integration tanpa ubah FFmpeg/provider | Windows build/EXE, CodeQL, canary, SHA256 |

Wave ini **hanya usulan urutan pengujian**. STEP05 harus memilih file nyata, pemilik setiap seam, perubahan arsitektur minimal, definisi DoR/DoD, dan batas izin SOL per wave. Tindakan implementasi tidak dimulai dalam STEP04.

## 12. Pelaporan evidensi dan gate PASS/FAIL

### 12.1 Standar tiap case sebelum mengklaim GREEN

1. Tes membuktikan perilaku yang **belum ada** dengan RED sebelum production patch. Catat commit RED, nama tes, reproduksi dan expected/actual.
2. Implementasikan solusi paling sempit hanya saat STEP06 diizinkan; uji GREEN berulang dengan seed deterministik yang sama.
3. Catat SHA-256 file sebelum/sesudah, metadata jumlah writer, tidak ada temp orphan, dialog focus dan byte-backup bila relevan.
4. Jalankan pengujian regresi terkait schema, project session, render, subtitle, Gemini isolation dan all tests, tanpa melemahkan assert.
5. Run Windows compile, Ruff, strict mypy, pytest, Qt offscreen, portable `onedir` EXE smoke, CodeQL, secret scan, SHA256; lampirkan URL run dan commit SHA yang sama.
6. Tiap gagal test menghasilkan CASE-ID, defect ID, owner (STEP05), reproduksi, risiko dan rollback; jangan ditandai PASS karena diabaikan.

### 12.2 Definisi hasil gate STEP04 (planning ini)

**STEP04 PASS hanya jika semua kondisi ini dipenuhi:** dokumen Markdown asli dan **DOCX native detail yang sudah dirender+ditinjau** berada dalam repositori V2; matriks RCV-01..24/SCH/AT/UI/COMP tersedia; manifest handoff diperbarui; perubahan hanya docs dan generator aman; PR branch-head CI/backend/CodeQL/Windows PASS; PR sudah merged ke `main`; tag v0.2.2 tetap pada SHA lama. Saat itu **yang PASS hanya kualitas planning**. Tidak ada klaim fitur atau tes baru sudah dijalankan.

**STEP04 FAIL/HOLD jika** DOCX belum ter-commit atau ternyata placeholder; ada file app Python/Qt/test produksi/release yang berubah; pemeriksaan gagal; PR belum merge; checksum/tag v0.2.2 bergerak; ada kontradiksi dengan UI final tiga dialog; atau perlindungan Cancel/backup/revalidation tidak tercakup.

### 12.3 STOP dan handoff yang tepat

Setelah STEP04 plan/docs merged, **BERHENTI**. Tahap berikutnya **STEP05 — Readiness dan Authorization SOL** hanya atas perintah user baru. STEP05 harus memeriksa semua DOCX STEP00–04 + satu final UI DOCX di repo, prioritas mitigasi, daftar file dan gelombang, DoR, rollback, dan keputusan terbuka. STEP06 programming ditahan sampai STEP05 secara eksplisit PASS. Tidak ada pekerjaan pada repositori `AI-Automatic-Video-Composer` versi lama.

## 13. Risiko yang masih terbuka dan keputusan ditunda ke STEP05

| Risiko / keputusan | Mengapa belum boleh dianggap selesai | Keputusan wajib sebelum coding |
|---|---|---|
| Cross-process lock | Lock aplikasi satu proses tidak melindungi penulis lain | CAS hash, kebijakan revalidate, advisory lock hanya setelah riset Windows |
| Durability power loss | Fsync file+directory dan filesystem Windows berbeda-beda | Klaim terbatas pada bukti yang dapat diuji |
| Quarantine rollback | Dua sidecar/fail setelah sebagian rename | Urutan operasi dan per-file safe rollback eksplisit |
| Legacy metadata | JSON snapshot valid bukan bukti asal | Selalu uncertain dengan DLG-02 dan konfirmasi kedua |
| Race sesudah disk replace | UI commit bisa gagal walau file telah durable | Kode `RESTORE_COMMIT_PARTIAL`, backup yang dilaporkan aman |
| Managed/cloud folder | Permission, sync, rename dapat tidak stabil | Limitasi terdokumentasi, jangan auto fallback path |
| Performance besar | Capture immutable bisa mahal; worker starvation | Profiling nyata 10/100/500, UI responsiveness budget ditetapkan setelah bukti |
| Path identity digest | Bukan autentikasi, collision/reparse risk | Review threat-model, identitas byte/canonical path guard |
| Exit with writer | Durasi penutupan dibatasi, dapat ada snapshot lama | Prioritas data integrity, tidak paksa save implisit |

## 14. Dokumen penyerahan ke SOL dan pemeriksaan lintas AI

**Berkas STEP04 yang harus di-commit**: `docs/v2_0_3_0_planning/04_RECOVERY_FAILURE_INJECTION_WINDOWS_TEST_PLAN.md`, `docs/v2_0_3_0_planning/docx/04_V2_0.3.0_RECOVERY_FAILURE_INJECTION_WINDOWS_TEST_PLAN.docx`, revisi bagian teratas `V2_0.3.0_PLANNING_STATUS.md` dan `IMPLEMENTATION_READINESS_INDEX.md`, serta generator DOCX jika diperlukan untuk reproduksibilitas. Tidak boleh ada workflow sementara yang tersisa di diff final.

**Urutan baca AI berikutnya:** STEP04 Markdown dan DOCX ini; RCV-01..24 STEP01; koordinasi/sidecar/fence STEP02; UI-REC-DLG-01..03 dan final UI DOCX STEP03; source code baseline; rencana STEP05 nanti. Jika salah satu gagal ditemukan/terbaca, tahan coding. Semua kasus dalam dokumen ini bersifat **TO BE IMPLEMENTED/TO BE TESTED**, bukan hasil eksperimen saat STEP04.

**Keputusan akhir STEP04:** Rencana dapat dipakai sebagai checklist implementasi test-first yang kuat, tetapi lulusnya gate dokumen belum otomatis mengizinkan menulis satu baris source aplikasi.