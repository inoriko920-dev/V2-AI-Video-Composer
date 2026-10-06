# STEP 14 — Release Candidate & Packaging

Tujuan STEP 14 adalah menghasilkan paket Windows portable yang dapat diuji sebagai release candidate, bukan menambah fitur kreatif baru.

## Gate wajib
1. source compile PASS
2. Ruff PASS
3. strict mypy PASS
4. cheap pytest PASS
5. PyInstaller onedir build PASS
6. packaged EXE foundation smoke PASS tanpa membutuhkan Python terpasang
7. schema dan release notes ikut terbawa ke artifact
8. artifact bebas `.env`, key/pem, cache/log/recovery user
9. ZIP release candidate dan SHA-256 dibuat otomatis
10. artifact GitHub Actions berhasil diunggah

## Packaging decision
- target: Windows 11 x64
- format: portable ZIP multi-file
- app version: `0.1.0rc1`
- executable: `AI Automatic Video Composer.exe`
- packaging: PyInstaller onedir
- FFmpeg binary: belum dibundel sampai audit lisensi/distribusi final selesai

## Handoff
Setelah artifact RC berhasil dibuat dan diverifikasi, STEP 14 dapat ditutup PASS dan proyek masuk STEP 15 — Final Release / Backup / Maintenance.
