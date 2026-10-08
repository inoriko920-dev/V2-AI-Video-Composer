# Backup & Recovery — AAVC

## Autosave dan pemulihan proyek v0.3.0

Rangkaian W06-A–E menyambungkan autosave lokal, provenance SHA-256, pilihan dialog pemulihan, backup pra-Restore bernomor, dan serialisasi operasi Save/Open. File cadangan, metadata dan backup proyek adalah **data milik pengguna**, bukan bagian dari ZIP aplikasi; jangan dibundel dalam GitHub Release.

Pemulihan hanya tersedia untuk proyek yang pernah disimpan manual. Snapshot yang valid tidak selalu dapat dipulihkan otomatis: metadata yang hilang/rusak atau baseline yang telah berubah membutuhkan pemeriksaan lebih lanjut dan persetujuan eksplisit. Setelah Restore sukses, file snapshot yang identik boleh tetap tersimpan tanpa memunculkan konflik ulang.

ZIP source rilis adalah snapshot `git archive HEAD`, **bukan** seluruh branch, tag dan riwayat Git. Untuk pemulihan repo 100% tetap gunakan Git Bundle backup satu aplikasi secara terpisah. Tag `v0.2.2` tetap beku. Status publikasi v0.3.0 harus diperiksa langsung pada halaman GitHub Releases.

---


## Canonical source
Git history is the canonical source. A final release must also preserve a source snapshot generated from the exact release commit.

## Release backup set
Keep these together for every final release:
- portable Windows ZIP;
- SHA256SUMS.txt;
- release notes;
- source-backup ZIP from the same commit;
- dependency/license records under `LICENSES/`;
- status files STEP09–STEP15 and architecture documentation.

## User-project recovery
Project documents use versioned `.aavcproj` JSON. AAVC 0.2.1 reads schema v3 and v4. Schema v4 is used only with `animation_keyframe_contract=advanced-v1`.

On the first successful overwrite that promotes a saved v3 project to v4, AAVC creates a non-clobbering `.pre-schema-v4.bak` beside the project. Keep that file if rollback to a v0.2.0-readable v3 source may be needed.

Autosave/recovery files are runtime data and must never be packaged into a release artifact. Recovery preserves the schema carried by the validated snapshot and must not silently promote or demote it.

## Disaster recovery sequence
1. verify the source-backup checksum;
2. restore the repository at the recorded release commit;
3. install the pinned Python/dev dependencies;
4. run compile, Ruff, strict mypy and cheap pytest;
5. rebuild the Windows onedir package;
6. run portable verification and compare generated checksums;
7. restore user projects separately from their own backups.

## Secrets
API keys are not part of source or release backups. Windows Credential Manager entries must be recreated by the user after a machine/account migration.
