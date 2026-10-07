# Panduan Pengguna — AI Automatic Video Composer

Panduan ini menjelaskan cara memakai AI Automatic Video Composer (AAVC) berdasarkan kemampuan yang dapat dibuktikan pada source `main` saat ini.

> **Batas versi:** panduan ini disiapkan untuk rilis stabil V2 `v0.2.0`. Rilis historis `v0.1.0` dan `v0.1.1` tetap frozen dan tidak diganti. Kemampuan yang dijelaskan di bawah telah masuk ke source final 0.2.0 dan melewati automated Windows user acceptance.

## 1. Menjalankan versi portable Windows

1. Unduh ZIP Windows portable dari GitHub Release resmi.
2. Ekstrak seluruh isi ZIP ke folder biasa. Jangan menjalankan aplikasi langsung dari dalam ZIP.
3. Pertahankan struktur folder portable.
4. Jalankan `AI Automatic Video Composer.exe`.

AAVC menggunakan distribusi **PyInstaller onedir portable**. File pendukung pada folder hasil ekstrak merupakan bagian dari aplikasi dan sebaiknya tidak dipindahkan satu per satu.

## 2. FFmpeg dan ffprobe

AAVC menggunakan FFmpeg/ffprobe untuk pipeline media dan render, tetapi binary FFmpeg tidak didistribusikan oleh proyek.

Slot aplikasi untuk binary tersebut adalah:

```text
tools/ffmpeg/
```

AAVC mencari FFmpeg pada slot app-local tersebut terlebih dahulu lalu pada system `PATH`. Jika FFmpeg tidak ditemukan, render dihentikan dengan pesan error; aplikasi tidak mengunduh FFmpeg secara otomatis.

## 3. Input proyek utama

Alur AAVC dirancang untuk video naratif/infografik berbasis Scene.

Input utama:

- Scene DOCX dengan daftar Scene dan mapping aset;
- aset gambar canonical dengan pola ID `Axxx`, misalnya `A001.png`, `A002.png`, dan seterusnya;
- media pendukung seperti narasi/audio dan subtitle SRT bila workflow membutuhkannya.

Scene mendukung layout **SINGLE** dan **DOUBLE** sesuai kontrak project. Asset binding menggunakan ID canonical agar source project, preview, validasi, dan render membaca identitas aset yang sama.

## 4. Membuat dan membuka project

### Membuat project baru

1. Pilih **Proyek Baru → Mulai**.
2. Pada layar **Pilih Scene DOCX**, klik **Pilih DOCX**.
3. Pilih file `.docx` sesuai kontrak Scene AAVC.
4. Klik **Lanjut** lalu pilih **Folder Aset** yang berisi file canonical.
5. AAVC membaca DOCX dan membangun `ProjectState` serta asset binding.
6. Pilih lokasi penyimpanan project `.aavcproj`.
7. Project disimpan terlebih dahulu; setelah berhasil, project menjadi sesi aktif dan editor dibuka.

Jika pemilihan folder/lokasi dibatalkan atau penyimpanan gagal, sesi project lama tidak diganti diam-diam.

### Membuka project yang sudah ada

1. Pilih **Buka Proyek** atau tombol **Buka**.
2. Pilih file `.aavcproj`.
3. AAVC memuatnya melalui `ProjectRepository`.
4. Sesi aktif baru hanya menggantikan sesi lama setelah load berhasil.
5. Editor kemudian dibangun dari `ProjectState` yang dimuat.

Jika file rusak atau tidak valid, sesi sebelumnya dipertahankan.

### Dirty state dan guard perubahan belum disimpan

Perubahan model yang belum disimpan membuat judul window menampilkan tanda `*`. Sebelum operasi yang dapat mengganti/menutup sesi, AAVC dapat meminta pilihan **Simpan / Abaikan / Batal**. Jika proses simpan gagal, aksi destruktif dibatalkan.

## 5. Navigasi aplikasi pada source `main`

Menu **Tampilan** sekarang merupakan navigasi runtime nyata, bukan placeholder. Tujuan yang tersedia:

- **Beranda** — dapat dibuka tanpa menghapus project aktif;
- **Editor Project** — aktif bila ada project dan me-refresh tampilan dari state project terbaru;
- **Subtitle** — membuka workflow subtitle project aktif;
- **Validation Center** — hanya dibuka sebagai data live bila ada project aktif.

Tombol Validation pada toolbar memakai guard sesi yang sama sehingga fixture STEP09 tidak tampil seolah-olah merupakan data project nyata.

Menu **Bantuan → Shortcut & Bantuan Cepat** juga sudah aktif dan menyusun daftar shortcut dari QAction yang benar-benar aktif pada build source tersebut.

### Menu AI, credential Gemini, dan Auto (AI)

Pada source `main` pasca-rilis, menu **AI** sudah menyediakan pengelolaan credential Gemini yang aman sekaligus workflow **Auto Animasi Gemini…** yang nyata dan dibatasi pada animasi native render-backed.

Aksi credential yang tersedia:

- **AI → Status Gemini…** — menampilkan jumlah serta nomor slot yang mempunyai credential, tanpa menampilkan isi API key;
- **AI → Simpan / Ganti API Key Gemini…** — memilih slot `1–100`, lalu memasukkan API key melalui field password;
- **AI → Hapus API Key Gemini…** — memilih slot lalu menghapus credential setelah konfirmasi.

Pada Windows, credential produksi disimpan melalui **Windows Credential Manager** dengan reference deterministik `gemini-slot-001` sampai `gemini-slot-100`. Nilai raw API key tidak dimasukkan ke `ProjectState`, file `.aavcproj`, log, status diagnostic, atau tampilan hasil. Saat request Gemini dikirim, key ditempatkan pada header `x-goog-api-key` dan tidak ditaruh di query URL.

**Auto Animasi Gemini…** dan mode toolbar **Auto (AI)** memakai pool credential tersebut untuk meminta Gemini memilih assignment animasi hanya dari efek native yang sudah didukung renderer. Assignment yang dikunci tidak boleh diganti. Hasil divalidasi penuh sebelum diterapkan sebagai satu transaksi history, sehingga satu Undo dapat mengembalikan keadaan sebelum Auto (AI).

Request Gemini berjalan melalui job background agar GUI tetap responsif. Bila project berubah saat request masih berjalan, hasil lama dibuang dan tidak dimutasi ke project.

Jika secure credential store tidak tersedia, aplikasi menolak memakai fallback plaintext.

Semua kemampuan pada paragraf ini merupakan bagian dari source final V2 `0.2.0`; binary historis `v0.1.1` tetap tidak berubah.

## 6. Kontrol project utama

Kontrol berikut sudah mempunyai perilaku live pada source `main`:

- **Baru** — membuka flow pembuatan project;
- **Buka** — memuat `.aavcproj`;
- **Simpan** — menyimpan `ProjectState` aktif secara atomic;
- **Simpan Sebagai** — menyimpan project ke target baru sesuai flow yang tersedia;
- **Undo / Redo** — bekerja melalui `ProjectHistory`;
- **Impor Media** — memasukkan subtitle SRT atau audio narasi yang didukung;
- **Tambah Teks** — membuka editor subtitle dari `subtitle_source` project aktif;
- **Rekam Narasi** — merekam mikrofon ke WAV, lalu memasang hasilnya ke `narration_audio` melalui history;
- **Mode Animasi Auto (AI)** — meminta Gemini memilih animasi native render-backed melalui credential pool yang aman;
- **Validasi** — menjalankan validasi terhadap project aktif;
- **Ekspor Video** — membuka pengaturan ekspor dan menjalankan render FFmpeg nyata di background;
- **Keluar** — mengikuti guard perubahan belum disimpan.

Editor juga mempertahankan Scene terpilih sebisa mungkin setelah perubahan history atau refresh UI.

## 7. Editor Overview dan preview Scene

Editor project aktif tidak memakai daftar Scene/Aset demo sebagai data project. Informasi berasal dari `ProjectState`, termasuk:

- judul project;
- resolusi dan FPS;
- durasi total dan jumlah Scene;
- status aset READY/MISSING;
- narasi dan subtitle yang terikat;
- daftar Scene, mode SINGLE/DOUBLE, durasi, dan Asset ID;
- asset binding dan source quote.

Memilih Scene memperbarui preview dari aset project sebenarnya. Layout preview memakai solver canonical yang sama untuk SINGLE/DOUBLE sehingga posisi dasar konsisten dengan model render. Aset missing/corrupt ditampilkan sebagai placeholder yang jelas, bukan thumbnail demo.

Preview yang tersedia pada maintenance `main` juga sudah terhubung dengan playhead/timeline untuk interaksi seek dan playback yang didukung. Ini belum berarti AAVC sudah menjadi NLE audio/video penuh: waveform audio multi-track dan monitoring semua layer secara real-time masih bukan kontrak yang diklaim panduan ini.

## 8. Timeline live pada source `main`

Timeline sekarang **bukan lagi timeline read-only**. Track utama tetap berfokus pada Scene yang benar-benar ada di `ProjectState`, tetapi sejumlah manipulasi langsung sudah aktif dan dilindungi history.

### Memilih dan mencari posisi

- Klik blok Scene untuk memilih Scene dan memindahkan konteks editor ke Scene tersebut.
- Klik/drag ruler untuk seek/scrub playhead.
- Kontrol seek keyboard yang tersedia dapat menggeser posisi playhead.
- Memilih Scene dari panel kiri dan timeline tetap saling sinkron.

### Mengubah urutan Scene

Scene dapat diubah urutannya melalui dua jalur:

- **Edit → Pindah Scene ke Atas/Bawah** atau shortcut yang tersedia;
- drag blok Scene pada timeline ke posisi urutan baru.

Reorder dijalankan melalui model/history sehingga dapat di-Undo/Redo dan memengaruhi urutan yang dibaca `RenderPlan`.

### Mengubah durasi Scene

Durasi dapat diubah melalui:

- field **Durasi Scene** pada inspector lalu **Terapkan Durasi**;
- resize tepi kanan blok Scene pada timeline.

Perubahan durasi memakai command/history project, memperbarui total durasi serta geometri timeline, dan baru persisten setelah project disimpan.

### Split Scene

Timeline memiliki operasi split Scene pada posisi edit/playhead yang didukung. Split dibuat melalui command/history sehingga dapat di-Undo/Redo. AAVC tetap menjaga aturan durasi/struktur Scene agar operasi yang tidak valid tidak membuat state project rusak.

### In/Out dan selection playback/render

Timeline mendukung range **In/Out** untuk menentukan bagian pilihan. Pada source `main` tersedia perilaku untuk:

- menetapkan dan menghapus In/Out;
- menggeser handle In/Out pada timeline;
- memainkan selection;
- loop selection;
- memakai selection sebagai rentang render ketika workflow ekspor selection dipilih.

Jika range belum lengkap atau tidak valid, operasi selection tidak dipaksakan sebagai data palsu.

### Marker

Marker timeline dapat ditambahkan/dikelola pada posisi waktu yang didukung dan ikut divisualisasikan pada timeline/navigator. Marker adalah bantuan navigasi editor; keberadaannya tidak otomatis mengubah isi render kecuali fitur render secara eksplisit membacanya.

## 9. Magnetic snap dan guide

Editor memiliki sistem magnetic snap untuk operasi timeline yang didukung.

Kemampuan yang tersedia pada source `main` meliputi:

- toggle **Magnet**;
- snap ke target timeline yang didukung;
- pengaturan target snap;
- pengaturan kekuatan/threshold snap;
- visual snap guide/feedback;
- bypass sementara ketika modifier yang disediakan UI digunakan saat editing.

Magnetic behavior diterapkan pada operasi yang memang sudah didukung seperti edit posisi/range/resize terkait timeline; fitur ini tidak berarti track audio/video arbitrary sudah dapat diedit seperti NLE umum.

## 10. Zoom, Follow Playhead, dan Mini Navigator

Timeline memiliki navigasi horizontal yang lebih lengkap pada source `main`.

### Zoom

- zoom timeline dapat diubah pada rentang yang dibatasi UI;
- `Ctrl+Wheel` digunakan untuk zoom pada timeline;
- aksi **Zoom to Fit** menyesuaikan seluruh track ke viewport;
- aksi **100%** mengembalikan skala referensi yang ditentukan editor.

### Follow Playhead

- **Follow Playhead** dapat membuat viewport mengikuti playhead;
- **Smooth Follow** memberi pergerakan follow yang lebih halus;
- scroll/manual navigation pengguna dapat menahan follow sementara agar viewport tidak “melawan” interaksi manual.

### Mini Navigator

Mini Navigator memberikan overview seluruh durasi timeline dan viewport aktif. Pada source `main`:

- handle navigator menggambarkan bagian timeline yang sedang terlihat;
- drag handle mem-pan viewport utama;
- resize tepi handle mengubah zoom timeline;
- marker dan range In/Out ditampilkan sebagai anchor/indikator pada navigator;
- anchor dapat diklik untuk menuju posisi terkait;
- hover anchor menampilkan timecode presisi untuk membantu navigasi.

## 11. Validasi project dan relink aset

Tombol **Validasi** menghitung issue dari `ProjectState` aktif.

Validasi yang didukung antara lain mendeteksi:

- asset yang belum READY atau file canonical yang belum terikat dengan benar;
- durasi Scene yang melanggar rule validasi yang tersedia.

Badge validasi mengikuti state project:

- merah bila ada error;
- kuning bila hanya ada warning;
- hijau / **Validasi OK** bila tidak ada issue.

Di Validation Center, pengguna dapat menjalankan **Validasi Ulang**. Untuk issue aset yang dapat direlink, **Relink** memilih file pengganti dan perubahan dijalankan melalui `ProjectHistory`, sehingga dapat di-Undo sebelum disimpan.

Fixture validasi STEP09 hanya dipertahankan untuk visual-reference capture tanpa sesi; penggunaan runtime normal dengan project aktif memakai data validasi project nyata.

## 12. Impor Media

Tombol **Impor Media** menerima tipe yang sudah terhubung ke model/render saat ini:

- subtitle `.srt`;
- audio narasi `.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`.

`.srt` disimpan sebagai `subtitle_source`, sedangkan audio yang didukung disimpan sebagai `narration_audio`. Import dijalankan melalui session/history dan dapat di-Undo/Redo sebelum disimpan permanen.

`background_source` belum diaktifkan melalui tombol ini jika pipeline runtime belum menggunakannya. Format yang tidak didukung ditolak dengan pesan jelas.

## 13. Editor subtitle

Jika project memiliki `subtitle_source`, **Tambah Teks** membuka editor yang membaca cue/timing SRT sebenarnya.

### Cue SRT

Editor dapat:

- membaca cue dari source project;
- menampilkan timing dan teks;
- menandai overlap;
- memilih cue;
- memuat ulang SRT;
- menggunakan working-copy/history/guard untuk operasi edit SRT yang memang sudah didukung oleh source terbaru.

Bila source hilang atau tidak dapat diparse, aplikasi menampilkan error dan tidak menggantinya dengan data demo.

### Gaya subtitle

Tab **Gaya** mengubah `ProjectState.subtitle_style` melalui history. Preset dan field yang tersedia dapat mengatur font, ukuran, fill, outline, shadow, background box, alignment, dan margin sesuai validasi UI.

Tekan **Terapkan Gaya** untuk memasukkan perubahan ke state/history, kemudian **Simpan** agar perubahan persisten ke `.aavcproj`.

### Animasi subtitle

Tab **Animasi** mengubah `ProjectState.subtitle_animation` melalui history. Preset yang didukung compiler ASS, durasi masuk/keluar, dan warna highlight diteruskan ke pipeline subtitle ketika render dengan subtitle diaktifkan.

Preview subtitle pada editor tidak boleh dianggap sebagai jaminan WYSIWYG frame-per-frame terhadap burn-in FFmpeg. Hasil final mengikuti compiler ASS dan render pipeline.

## 14. Ekspor video nyata

Dialog ekspor hanya menampilkan opsi yang memang didukung render engine saat ini:

- **MP4 H.264** (`libx264`);
- **MP4 H.265** (`libx265`);
- preset encoder yang tersedia;
- resolusi 1920×1080, 2560×1440, atau 3840×2160;
- 30 atau 60 fps;
- kualitas yang dipetakan ke CRF;
- ketajaman/sharpen amount;
- burn-in subtitle bila dipilih dan source subtitle tersedia;
- narasi project bila tersedia;
- selection In/Out ketika workflow render-selection digunakan.

AAVC membangun `RenderPlan` dan menjalankan preflight sebelum FFmpeg. Missing asset, media yang dibutuhkan tetapi hilang, konfigurasi invalid, atau error render menghentikan proses dengan feedback UI.

Full-project render dan render Selection In/Out dijalankan melalui **JobManager** di luar Qt GUI thread. Selama render berjalan, UI tetap dapat memproses event. AAVC menolak memulai pekerjaan render/AI kedua sampai hasil pekerjaan aktif sudah diproses oleh GUI.

Kontrol GPU encoder dan **Pengaturan Lanjutan** yang belum mempunyai implementasi tidak lagi ditampilkan pada dialog ekspor runtime.

## 15. Kontrol yang masih dibatasi

Source `main` sudah mengaktifkan Rekam Narasi, Auto (AI), render background, dan editor/timeline utama. Batas produk yang masih sengaja dipertahankan:

- waveform dan editing audio multi-track bukan workflow live AAVC;
- media background arbitrary belum menjadi track editor penuh;
- preview subtitle tidak dijanjikan WYSIWYG frame-per-frame terhadap burn-in FFmpeg;
- GPU export encoder dan panel advanced export belum menjadi kemampuan produk, sehingga kontrolnya tidak diiklankan pada dialog runtime;
- AI saat ini dibatasi pada perencanaan animasi native yang tervalidasi, bukan agen bebas yang dapat mengubah semua bagian project;
- AAVC tetap compositor naratif/infografik berbasis Scene, bukan pengganti NLE multitrack umum.

Permukaan runtime live juga tidak menampilkan tab **AI Agent** atau tab kosong yang hanya berasal dari reference shell. Fixture STEP09 tetap boleh mempertahankan elemen referensi untuk kebutuhan regression visual, tetapi fixture tersebut bukan kontrak fitur runtime.

## 16. Sebelum ekspor

Periksa minimal:

- Scene DOCX/project dapat dibaca;
- Asset ID canonical tersedia dan status aset sudah benar;
- urutan serta durasi Scene sesuai;
- range In/Out benar bila memakai render selection;
- media/audio yang diperlukan tersedia;
- Validation Center tidak menunjukkan error yang belum diperbaiki;
- FFmpeg tersedia di `tools/ffmpeg/` atau system `PATH`;
- subtitle source valid bila burn-in dipakai;
- perubahan gaya/animasi/subtitle sudah diterapkan dan project sudah disimpan;
- resolusi, FPS, codec, kualitas, dan ketajaman sesuai kebutuhan.

## 17. Recovery

Jangan menghapus file project asli ketika melakukan recovery.

Repo menyediakan versioned project state dan recovery snapshot. Jika aset berpindah folder, gunakan workflow validation/relink daripada mengganti ID canonical secara acak.

Untuk kebijakan lebih teknis lihat `BACKUP_AND_RECOVERY.md`.

## 18. Untuk developer

Baseline pengembangan aktif:

- Python 3.12.10 pada toolchain Windows yang dipin repo;
- PySide6 / Qt Widgets;
- FFmpeg / ffprobe sebagai external dependency;
- PyInstaller onedir;
- CI Windows dengan compile, Ruff, strict mypy, pytest, serta verifikasi screenshot STEP09;
- CodeQL untuk pemeriksaan keamanan source.

Perintah PowerShell utama:

```powershell
./scripts/dev.ps1
./scripts/test.ps1
./scripts/package.ps1
./scripts/verify_portable.ps1
```

## 19. STEP09 dan fixture visual

STEP09 tetap frozen sebagai kontrak visual regression. Fixture no-session yang dipakai untuk screenshot regression bukan sumber data project runtime. Maintenance editor di `main` harus mempertahankan jalur fixture tersebut agar CI dapat membandingkan visual reference tanpa membuat fixture tampil sebagai data project nyata kepada pengguna.

## 20. Batas dokumen ini

Panduan ini mendokumentasikan kemampuan yang dapat dibuktikan dari source dan test repo, bukan janji bahwa semua konsep editor sudah setara dengan NLE komersial.

Untuk status rilis lihat `README.md` dan `RELEASE_NOTES_0.2.0.md`. Untuk kebijakan maintenance lihat `MAINTENANCE.md`. Untuk detail arsitektur dan factory evidence, lihat dokumen lain di `docs/` dan file STEP status di root repo.