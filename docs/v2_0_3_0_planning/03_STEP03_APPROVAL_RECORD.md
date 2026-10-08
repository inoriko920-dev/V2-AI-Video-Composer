# STEP 03-R — Persetujuan Final Tiga Gambar UI

**Repo:** `inoriko920-dev/V2-AI-Video-Composer` (hanya repositori V2).  
**Tanggal persetujuan:** 8 Oktober 2026 WIB (jam tidak dinyatakan).  
**Bukti persetujuan:** pengguna memberikan pernyataan eksplisit dalam percakapan ChatGPT:
> Saya secara eksplisit menyetujui ketiga gambar UI STEP 03-R V2-AI-Video-Composer sebagai desain final. Buat DOCX referensi UI final berisi gambar, masukkan dokumen dan ketiga PNG ke GitHub V2, lalu lakukan pemeriksaan. Jangan mulai coding.

## Ruang lingkup persetujuan
Persetujuan hanya mencakup tiga PNG berikut. Seluruh UI utama aplikasi lama tetap 1:1, berdasarkan `UI-013_ACTUAL.png` yang diambil dari GitHub Actions run `37734080472`, artifact `11531031921`.

| ID | Kegunaan | SHA-256 PNG yang disetujui |
|---|---|---|
| UI-REC-DLG-01 | Cadangan Proyek Ditemukan | `3c8cae008c762f13539ba367dff332930993e4883f79d0411666bc465c1c9cf0` |
| UI-REC-DLG-02 | Cadangan Perlu Diperiksa | `c0fe7738e2af1c1b45f0acbe54b3d2aef83f8eb90daeaa29bc5e01c7b3bd4d01` |
| UI-REC-DLG-03 | Cadangan Tidak Dapat Dibaca | `84955b4cc9c2df8691905112c6fde8f7cde7599657836aed005b6a8840662cec` |

**Screenshot acuan:** `UI-013_ACTUAL_REFERENCE.png`, SHA-256 `729ee1fcdf40dc07ec9a1f399b1bc98f303960c72e7d700239b4cf9306fd630c`.

**DOCX final yang disyaratkan:** `docs/v2_0_3_0_planning/docx/03_V2_0.3.0_FINAL_APPROVED_UI_DIALOG_REFERENCES.docx`. Dokumen harus menanam ketiga gambar di dalam file; referensi editor asli dapat disertakan sebagai bukti. Renderer lokal menampilkan tujuh halaman tanpa pemotongan halaman.

## Gate wajib
1. Pastikan keempat PNG ada dalam `docs/v2_0_3_0_planning/ui_step03_approved/` dan SHA-256 cocok persis.
2. Pastikan DOCX final benar-benar ter-commit sebagai file biner DOCX dan mempunyai minimal tiga gambar tertanam.
3. Diff akhir hanya dokumentasi / referensi gambar. Workflow/generator sementara harus dibersihkan sebelum PR digabung.
4. Seluruh pemeriksaan CI, backend, CodeQL, dan Windows acceptance pada PR harus PASS sebelum merge.
5. STEP 04 masih **tidak boleh dijalankan** pada giliran persetujuan UI ini; instruksi baru diperlukan. STEP 05/06 coding tetap terblokir sampai planning lengkap.

**Status awal catatan ini:** persetujuan gambar diterima; materialisasi file pada cabang PR masih harus diverifikasi. Jangan menyebut visual gate PASS sampai seluruh file hadir pada main dan semua pemeriksaan selesai.

## Keputusan yang tetap
UI lama dan 42 referensi dibekukan; 13 prompt recovery lama hanya arsip. Dialog konflik menggunakan konfirmasi kedua di komponen sama; tidak memerlukan gambar keempat. QStatusBar autosave dan QMessageBox perubahan belum disimpan tetap memakai komponen lama. Snapshot autosave bukan Save manual dan tidak boleh membersihkan dirty state.
