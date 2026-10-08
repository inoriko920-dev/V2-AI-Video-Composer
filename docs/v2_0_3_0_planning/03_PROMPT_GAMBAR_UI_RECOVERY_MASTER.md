# STEP 03 — Paket Prompt Gambar UI Autosave & Recovery v0.3.0

**Status:** PROMPT IMAGE AUTHORING ONLY — HARD STOP AFTER PROMPT PACKAGE. Bukan gambar final, bukan implementasi Qt, bukan perubahan aplikasi.
**Tanggal:** 8 Oktober 2026 WIB.
**Repo:** inoriko920-dev/V2-AI-Video-Composer.
**Baseline planning main:** d076a9bfe49c0fe47988fd815fd8fde36ab83c8a.
**Rilis stabil tidak boleh diubah:** v0.2.2 @ eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef.
**Sumber keputusan:** docs/UI_FREEZE.md (42 referensi UI-001..042), docs/v2_0_3_0_planning/01_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.md, 02_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.md.

## 1. Tujuan dan batas yang harus dibaca oleh generator gambar

Buat **13 gambar referensi UI statis yang terpisah**, masing-masing screenshot desktop utuh 1920x1080 16:9, satu state per gambar. Gambar hanya bahan review visual; GUI aplikasi produksi tetap harus berupa widget Qt native setelah tahap implementasi yang diizinkan. Tidak ada kode yang boleh ditulis pada STEP03.

Gaya harus **konsisten** dengan referensi beku V2 UI-001 hingga UI-042, khususnya UI-002/003 editor utama; jangan menciptakan desain aplikasi baru. Bahasa Indonesia; putih dan biru profesional; tipografi kecil namun terbaca; elemen rapi, rata, minimalis; seperti screenshot aplikasi Windows 11 profesional, bukan poster/pemasaran atau ilustrasi.

**Latar editor wajib identik secara konseptual di semua gambar:** menu dan toolbar atas; panel navigasi/media kiri kurang lebih 300 px; pratinjau video besar di tengah; panel properti/AI kanan sekitar 360 px; timeline horizontal di bawah minimal 180 px; judul proyek contoh "Proyek Dokumenter Suez"; daftar scene/properti netral tanpa gambar manusia/wajah; tidak ada fitur palsu. Dialog recovery menutup bagian tengah dengan scrim transparan biru-abu sangat tipis; jangan menggeser, menyembunyikan, atau merombak shell. Untuk gambar status nonmodal, **tanpa scrim**.

**Safe area:** seluruh elemen dialog/panel/action dan tulisan harus berjarak minimal 2% dari tepi canvas. Gunakan grid piksel, padding cukup, teks tidak terpotong. Resolusi yang diutamakan **1920x1080**. Detail desain berupa referensi; ukuran akhir akan dipastikan saat UI approval. Jangan pakai tombol lebih dari yang diminta atau nama produk lain.

**Syarat teks dan hierarki:** teks label di bawah diberikan verbatim sebisa mungkin; bila generator kesulitan merender tipografi, **pertahankan geometri dan urutan tombol, lalu koreksi teks secara manual saat UI final**, jangan menerima kata acak/typo sebagai final. Judul modal 18–20 px, body 13–14 px, label/status 11–13 px, tombol 13 px; tombol utama biru, Cancel/Batal berpenekanan aman, tombol berbahaya hanya beraksen peringatan yang tenang. Kontras teks WCAG-ish AA, area sentuh tombol ~36–40 px, fokus keyboard tampak, Escape selalu Batal. Jangan membentuk disclaimer klaim fitur yang belum ada.

**Kontrak perilaku yang tidak boleh diputarbalikkan:** autosave membuat snapshot, tidak sama dengan "Simpan" manual; judul tetap bertanda * jika dirty; dialog standar hanya tampil untuk calon cadangan yang valid; metadata lama/tidak lengkap dan perubahan file harus ditandai konflik; Pulihkan selalu menyimpan backup sebelum menimpa disk; Batal tidak mengubah proyek aktif/file; user guard "Perubahan belum disimpan" tampil **sebelum** modal recovery target. File invalid tidak boleh otomatis dibuang; Save As collision tidak boleh menimpa cadangan proyek lain; status pending/running/failed bukan modal spam.

## 2. Negative prompt universal

JANGAN: dark mode, tema hitam/neon, bahasa Mandarin/Inggris pada kontrol, teks lorem ipsum/acak, watermark, brand asing, UI mobile, 3D isometrik, gambar poster, ilustrasi kartun, komik, foto orang, panel editor baru, redesign timeline, tombol Generate Video/Publish/Cloud Sync palsu, proses pemulihan otomatis tanpa konfirmasi, tulisan "Proyek disimpan" untuk snapshot otomatis, tampilkan API key/password/nomor akun, hapus cadangan tanpa izin, ikon bahaya besar yang dramatis, dialog melebar melampaui layar, elemen overlay bertumpuk atau terpotong.

## 3. Matrix gambar yang wajib dibuat dan direview

| ID | Nama file gambar akhir (nanti, belum dibuat) | Keadaan | Pilihan/tombol |
|---|---|---|---|
| UI-REC-01 | UI-REC-01_VALID_RECOVERY.png | Cadangan valid diketahui, berbeda dari disk | Pulihkan / Gunakan Proyek Tersimpan / Batal |
| UI-REC-02 | UI-REC-02_CONFLICT_WARNING.png | Snapshot valid tetapi disk berubah/metadata tidak lengkap | Pulihkan (perlu konfirmasi) / Gunakan Proyek Tersimpan / Batal |
| UI-REC-03 | UI-REC-03_CONFLICT_CONFIRMATION.png | Konfirmasi tambahan setelah memilih Pulihkan pada konflik | Ya, Pulihkan dengan Cadangan / Batal |
| UI-REC-04 | UI-REC-04_INVALID_SNAPSHOT.png | Snapshot rusak/tidak didukung | Buka Proyek Tersimpan / Batal |
| UI-REC-05 | UI-REC-05_SOURCE_CHANGED.png | Disk/cadangan berubah selama modal aktif | Periksa Ulang / Batal |
| UI-REC-06 | UI-REC-06_AUTOSAVE_PENDING.png | Dirty, timer belum jatuh tempo | Hanya status nonmodal |
| UI-REC-07 | UI-REC-07_AUTOSAVE_WORKING.png | Snapshot sedang dibuat | Hanya status nonmodal |
| UI-REC-08 | UI-REC-08_AUTOSAVE_SUCCESS.png | Cadangan otomatis berhasil | Hanya status nonmodal |
| UI-REC-09 | UI-REC-09_AUTOSAVE_ERROR.png | Snapshot gagal, Save manual tetap tersedia | Status nonmodal / lihat rincian |
| UI-REC-10 | UI-REC-10_UNSAVED_FIRST_PATH.png | Proyek baru tanpa lokasi penyimpanan | Status nonmodal / Simpan Proyek |
| UI-REC-11 | UI-REC-11_SAVE_AS_COLLISION.png | Tujuan Simpan Sebagai sudah memiliki cadangan lain | Pilih Lokasi Lain / Batal |
| UI-REC-12 | UI-REC-12_RESTORE_FAILURE.png | Pemulihan gagal sebelum/atau sesudah commit secara teridentifikasi | Tutup / Lihat Panduan |
| UI-REC-13 | UI-REC-13_EXISTING_UNSAVED_GUARD.png | Guard lama sebelum recovery; tidak didesain ulang | Simpan / Jangan Simpan / Batal |

## 4. Template umum untuk setiap TXT

Selalu gabungkan **A. MASTER DESAIN** di bawah dengan **B. PROMPT STATE** masing-masing UI-REC-XX. Buat **SATU GAMBAR** per TXT, jangan kolase, jangan bagi 13 state dalam 1 canvas. Nama file PNG keluaran harus mengikuti matrix; jangan masukkan label ID sebagai elemen UI yang terlihat.

### A. MASTER DESAIN

Render a single high-fidelity 1920x1080 16:9 Windows 11 desktop application screenshot, not code, not a marketing mockup, not a mobile app. Preserve the existing V2 AI Video Composer professional Filmora-inspired WHITE and calm BLUE PySide6/Qt visual language from UI-001 through UI-042; reference UI-002 editor layout: fixed top menu/toolbar; ~300px left navigation/assets rail; large central preview; ~360px right properties/AI panel; bottom multitrack timeline at least 180px tall. Indonesian controls, crisp small typography, subtle shadows and focus ring, consistent spacing, realistic native desktop elements. Example project name "Proyek Dokumenter Suez", neutral placeholders only. Protect all assets and text inside a 2% screen-margin safe area. No layout redesign, no English/Mandarin labels, no spurious generated text, no watermark, no developer debug text. Respect **B. PROMPT STATE** literally. Output one distinct PNG per scene only, no grid or montage.

## 5. Prompt per gambar — isi wajib lengkap, bukan ringkasan

### B. PROMPT STATE UI-REC-01 — Pemulihan cadangan valid

**ID:** UI-REC-01

**Output name:** UI-REC-01_VALID_RECOVERY.png

**Prompt:** Buat screenshot state dialog modal terpusat "Cadangan Proyek Ditemukan". Modal putih lebar sekitar 680px, tinggi proporsional 390–440px, rounded 10px, shadow tipis dan dim overlay pada editor asli. Ikon kecil perisai biru dan tanda centang, bukan centang "sudah disimpan". Teks di dalam dialog: judul "Cadangan Proyek Ditemukan"; intro "Ada perubahan proyek yang tersimpan dalam cadangan otomatis."; nama file "Proyek Dokumenter Suez.aavcproj"; dua baris status dengan label "Versi proyek tersimpan" dan "Cadangan otomatis — perubahan belum disimpan"; info strip biru muda "Memulihkan cadangan akan membuat salinan aman proyek sebelumnya terlebih dahulu."; tepat tiga tombol footer (dari kiri ke kanan) "Pulihkan Cadangan" biru utama, "Gunakan Proyek Tersimpan" sekunder outline, "Batal" neutral. Fokus keyboard awal pada "Batal" sebagai pilihan paling aman; jangan centang pilihan otomatis. Konten jelas membandingkan dua keadaan tanpa timestamp palsu, persen pemulihan atau janji backup cloud.

### B. PROMPT STATE UI-REC-02 — Peringatan konflik cadangan

**ID:** UI-REC-02

**Output name:** UI-REC-02_CONFLICT_WARNING.png

**Prompt:** Tampilkan modal warning state RECOVERABLE_UNCERTAIN di tengah editor identik. Judul "Perubahan Proyek Berbeda" dengan ikon peringatan amber kecil, warna latar putih bersih. Penjelasan: "Proyek tersimpan mungkin telah berubah setelah cadangan otomatis dibuat."; dua blok perbandingan "Versi proyek saat ini" dan "Cadangan otomatis ditemukan"; kolom kecil netral "Status: Perlu diperiksa", bukan indikator centang hijau. Teks kehati-hatian: "Jika dilanjutkan, versi proyek sekarang akan dicadangkan sebelum pemulihan." Tambah info "Cadangan dari versi sebelumnya atau data pemulihan tidak lengkap." Tiga tombol berjajar: "Pulihkan Cadangan" secondary/warning, "Gunakan Proyek Tersimpan" outline, "Batal" neutral dengan default/focus pada Batal. Jangan seolah metadata telah diverifikasi, jangan auto-replace, jangan menghapus versi proyek asli.

### B. PROMPT STATE UI-REC-03 — Konfirmasi ekstra untuk konflik

**ID:** UI-REC-03

**Output name:** UI-REC-03_CONFLICT_CONFIRMATION.png

**Prompt:** Gambar screenshot dengan modal konfirmasi kedua **bukan** dialog tiga tombol biasa. Modal bertajuk "Konfirmasi Pemulihan Berisiko"; dim background editor yang sama; judul tegas namun tenang, ikon amber berukuran kecil. Body "File proyek tersimpan berbeda dari versi yang digunakan cadangan."; ringkasan dua bullet teks pendek "Salinan proyek saat ini akan dibuat sebelum pemulihan." dan "Lanjutkan hanya jika Anda ingin menggunakan perubahan dari cadangan otomatis."; footer tepat dua tombol, "Ya, Pulihkan dengan Cadangan" warna peringatan outline, dan "Batal" biru utama/default dengan outline fokus. Tidak ada checkbox "jangan tanya lagi", tidak ada tombol "paksa", dan jangan tampilkan progres sukses sebelum user memilih.

### B. PROMPT STATE UI-REC-04 — Cadangan tidak valid

**ID:** UI-REC-04

**Output name:** UI-REC-04_INVALID_SNAPSHOT.png

**Prompt:** Gambar modal error-safe ketika cadangan otomatis rusak atau versinya tidak dikenali. Judul "Cadangan Tidak Dapat Dibaca" dengan ikon warning amber sederhana; isi "Cadangan otomatis tidak dapat dibuka dengan aman." dan "Proyek tersimpan tidak akan diubah. File cadangan tetap disimpan untuk pemeriksaan lebih lanjut."; detail yang aman seperti "Kode: AUTOSAVE_INVALID_SCHEMA", tanpa stack trace atau path absolut; footer dua tombol "Buka Proyek Tersimpan" sekunder biru dan "Batal" default/focus. Jangan tampilkan "Pulihkan", "Hapus Cadangan", "Reset Data" atau operasi destruktif. Modal tidak mengunci aplikasi secara teatrikal.

### B. PROMPT STATE UI-REC-05 — File berubah saat keputusan terbuka

**ID:** UI-REC-05

**Output name:** UI-REC-05_SOURCE_CHANGED.png

**Prompt:** Screenshot layar editor yang sama dengan modal warning kecil 610x330: judul "Data Proyek Berubah"; body "Proyek atau cadangan berubah saat jendela pemulihan terbuka." lanjut "Periksa ulang sebelum memilih versi yang digunakan."; info strip biru "Tidak ada file yang diubah."; footer dua tombol "Periksa Ulang" outline biru, "Batal" biru utama/default dengan fokus. Tidak ada tombol Pulihkan aktif; tidak ada angka persen atau timestamp rekaan. State ini muncul jika SHA-256 candidate/disk tidak sama lagi ketika tombol dipilih.

### B. PROMPT STATE UI-REC-06 — Autosave menunggu jeda

**ID:** UI-REC-06

**Output name:** UI-REC-06_AUTOSAVE_PENDING.png

**Prompt:** Tidak ada modal dan tidak ada scrim. Screenshot editor normal utuh dengan title bar "Proyek Dokumenter Suez * — V2 AI Video Composer" (tanda * jelas artinya belum tersimpan manual). Di status bar bagian bawah kanan tampil ikon jam sederhana dan teks "Cadangan otomatis menunggu jeda perubahan"; tooltip kecil muncul halus di atas: "Perubahan belum disimpan. Cadangan dibuat setelah jeda aktivitas."; simpan manual masih tersedia pada toolbar atas. Jangan tampilkan toast "Tersimpan" atau progress ring. Tekankan indikator tidak mengganggu timeline dan preview.

### B. PROMPT STATE UI-REC-07 — Autosave sedang berjalan

**ID:** UI-REC-07

**Output name:** UI-REC-07_AUTOSAVE_WORKING.png

**Prompt:** Tidak ada modal atau scrim; editor utuh identik REC-06, judul proyek masih "Proyek Dokumenter Suez *". Status bar kanan memiliki ikon putar/progres kecil biru dan teks persis "Membuat cadangan otomatis…"; di dekatnya label sekunder "Proyek belum disimpan manual" bila muat. Jangan tampilkan 100%, progress bar fiktif, spinner besar atau menggantikan tombol Simpan. Tidak ada aksi destructive; bagian pratinjau, panel AI kanan, timeline tidak berubah.

### B. PROMPT STATE UI-REC-08 — Autosave berhasil tanpa menyimpan proyek manual

**ID:** UI-REC-08

**Output name:** UI-REC-08_AUTOSAVE_SUCCESS.png

**Prompt:** Tidak ada modal. Editor yang sama dengan proyek tetap dirty ("Proyek Dokumenter Suez *"), status bar kanan menampilkan ikon check lingkar biru kecil dan teks "Cadangan otomatis dibuat"; tooltip/tulisan pembantu "Perubahan belum disimpan ke proyek utama"; tombol "Simpan" tetap aktif. Visual harus bisa membedakan snapshot backup dari manual save. Jangan membuat judul kehilangan tanda *; jangan menulis "Semua perubahan sudah disimpan".

### B. PROMPT STATE UI-REC-09 — Autosave gagal tanpa spam modal

**ID:** UI-REC-09

**Output name:** UI-REC-09_AUTOSAVE_ERROR.png

**Prompt:** Tidak ada modal; editor tetap dapat dipakai. Status bar kanan memuat ikon peringatan amber kecil, teks "Cadangan otomatis gagal", link teks halus "Lihat rincian". Tooltip melayang yang rapi berisi "Proyek asli tidak diubah." dan "Simpan secara manual untuk menjaga perubahan." serta kode "AUTOSAVE_WRITE_FAILED". Tanda * tetap ada di judul, tombol "Simpan" tetap tersedia. Jangan mengklaim data hilang atau menunjukkan path sensitif, izin administrator, log panjang, retry timer palsu. Jadikan panel pesan ringkas dan tidak menutupi alat editor.

### B. PROMPT STATE UI-REC-10 — Proyek belum memiliki lokasi simpan

**ID:** UI-REC-10

**Output name:** UI-REC-10_UNSAVED_FIRST_PATH.png

**Prompt:** Satu screenshot editor tanpa modal dengan state proyek baru yang belum pernah di-Save, judul "Proyek Baru *". Status bar kanan ikon info biru dan pesan "Simpan proyek dulu untuk mengaktifkan cadangan otomatis"; toolbar atas tombol "Simpan Proyek" beraksen biru lembut dan dapat dilihat jelas. Tooltip singkat "Cadangan otomatis memerlukan lokasi proyek." Tidak ada path yang ditebak, tombol "Simpan otomatis" palsu, atau janji melindungi proyek yang belum diberi path.

### B. PROMPT STATE UI-REC-11 — Benturan cadangan pada Save As

**ID:** UI-REC-11

**Output name:** UI-REC-11_SAVE_AS_COLLISION.png

**Prompt:** Screenshot modal putih dipusatkan pada editor dengan judul "Lokasi Penyimpanan Memiliki Cadangan"; ikon warning amber kecil; nama tujuan hanya nama file contoh "Dokumenter Suez Final.aavcproj" tanpa lokasi user. Body tepat: "Folder tujuan sudah berisi cadangan otomatis yang mungkin milik proyek lain." lalu "Untuk melindungi data, pilih lokasi penyimpanan berbeda."; footer dua tombol "Pilih Lokasi Lain" biru utama, "Batal" neutral/default dengan fokus awal. Tidak ada "Timpa Semua", "Hapus Cadangan", checkbox force overwrite, atau wizard tambahan. Ini state penolakan fail-closed.

### B. PROMPT STATE UI-REC-12 — Pemulihan gagal secara aman

**ID:** UI-REC-12

**Output name:** UI-REC-12_RESTORE_FAILURE.png

**Prompt:** Modal recovery error terpusat, judul "Pemulihan Belum Selesai" (bukan "Berhasil"), ikon amber kecil dan pesan berbeda status jelas: "Pemulihan tidak dapat diselesaikan. Cadangan otomatis tetap tersedia."; bawahnya info "Proyek asli atau salinan pra-pemulihan tetap disimpan sesuai tahap yang berhasil." serta kode kecil "RESTORE_BACKUP_FAILED" sebagai contoh jalur gagal sebelum penggantian. Tombol "Lihat Panduan" sekunder dan "Tutup" default biru; tanpa tombol langsung menimpa file. Opsional baris aman "Jangan hapus berkas cadangan." Jangan mengklaim rollback berhasil jika tidak ada buktinya dan jangan memperlihatkan path absolut.

### B. PROMPT STATE UI-REC-13 — Guard perubahan belum disimpan yang sudah ada

**ID:** UI-REC-13

**Output name:** UI-REC-13_EXISTING_UNSAVED_GUARD.png

**Prompt:** Referensi untuk dialog existing, **bukan** pengganti UI baru. Screenshot editor saat membuka proyek lain ketika proyek aktif masih dirty. Tampilkan QMessageBox Qt sederhana seperti layar saat ini: judul "Perubahan belum disimpan"; teks "Proyek Dokumenter Suez memiliki perubahan yang belum disimpan."; teks pendukung "Simpan perubahan sebelum membuka project lain?"; 3 tombol pada footer "Simpan", "Jangan Simpan", "Batal" dengan fokus awal "Simpan" sesuai guard v0.2.2. Jangan tampilkan modal recovery target di belakang/bersamaan, jangan menata ulang shell, jangan menambahkan autosave modal. Alur visual menunjukkan existing unsaved guard **muncul lebih dulu**; setelah Save/Discard, barulah prompt recovery target dapat dipertimbangkan.

## 6. Checklist QA visual setiap gambar (wajib)

- Ukuran benar 1920x1080 (16:9); satu gambar per state; tidak menjadi kolase.
- Latar yang sama dengan UI-002 lama, bukan redesign. Ruang utama preview, panel aset kiri, panel AI/properti kanan, timeline bawah tetap terjaga.
- Warna putih + biru profesional, aksen kuning hanya warning, tanpa neon/dark theme.
- Semua label Bahasa Indonesia bisa dibaca; **tidak ada teks acak, tombol tambahan, atau istilah yang salah**.
- Kontrol tidak terpotong/bertumpuk; margin aman 2%; dialog tidak lebih besar dari area pratinjau wajar.
- Tombol Cancel/Batal aman dan tampak; conflict konfirmasi ekstra bukan dialog pertama yang hilang.
- Tidak ada Restore sukses otomatis, Auto Save mengubah dirty marker, hapus cadangan otomatis atau klaim cloud.
- Titik fokus keyboard dan urutan tombol masuk akal, icon warning tidak menyeramkan.
- Gambar UI-REC-13 mereplikasi dialog lama, tidak menggantikannya.
- Nama file output sesuai matrix; satu gambar PNG bukan kode/wireframe.
- Jika satu gambar salah, revisi hanya gambar tersebut dengan tetap memakai master desain.

## 7. Gate penghentian mutlak (HARD STOP)

**Setelah paket prompt UI di atas dan 13 TXT per gambar serta DOCX prompt tersimpan: STOP TOTAL.** STEP03 prompt-writing merupakan satu-satunya pekerjaan yang diizinkan pada giliran ini. Jangan mulai STEP04, jangan buat widget Qt, jangan mengubah branch kode, jangan merilis v0.3.0.

Tahap gambar dilakukan **sesudah** prompt terkunci: hasilkan semua 13 PNG terpisah; pemeriksaan satu demi satu dengan pengguna; revisi yang tidak sesuai; setelah seluruh gambar disetujui, satukan **semua gambar UI final dan keputusan/revisi** dalam satu DOCX referensi UI v0.3.0. DOCX visual tersebut harus dimasukkan ke repo bersama seluruh DOCX planning sebelum STEP04/05 dan terutama sebelum STEP06 coding.

**Khusus aturan pengguna:** Bahkan jika pesan berikutnya hanya "lanjutkan", STOP tetap berlaku selama gambar/review/DOCX final belum selesai. Jawab kebutuhan menyelesaikan gambar dulu; jangan melompati gate.

**Status yang benar untuk penutupan STEP03:** PROMPT COMPLETE / WAITING UI IMAGES AND APPROVAL. Bukan UI APPROVED, bukan CODING AUTHORIZED. Gambar final **belum dibuat oleh paket ini**.
