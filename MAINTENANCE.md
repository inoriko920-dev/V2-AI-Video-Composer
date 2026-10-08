# Maintenance Policy — AAVC v0.3.0

## Jalur patch kandidat v0.3.1 — source saja

`0.3.1` saat ini adalah identitas **source development**, bukan rilis baru. Scope perubahan hanya nama rekaman WAV kanonis dan sinkronisasi paket/tes; `v0.3.0` tetap stable publik. Pengemasan release-candidate, checksum dari build baru, pengujian PC pemilik, dan publikasi adalah tahap terpisah. Jangan gunakan ZIP lama sebagai bukti v0.3.1. Tag dan aset v0.3.0/v0.2.2 wajib tetap immutable.

## Pemeliharaan v0.3.0

Versi **0.3.0** menambahkan autosave dan dialog pemulihan lokal melalui satu ProjectSession, tanpa skema proyek v5 atau perubahan 21 efek native. Paket distribusi harus lulus checksum arsip Windows+source, FFmpeg eksternal versi referensi 9.0.2, tes Windows, dan verifikasi screenshot UI. Status publikasi dan tag harus diperiksa langsung pada GitHub Releases; versi terdahulu tidak ditimpa.

---


## Stable line
`0.2.x` is the preceding maintained V2 Windows desktop line. Version 0.2.1 can read schema v3 and v4; schema v4 is activated only by explicit advanced edits and uses `animation_keyframe_contract=advanced-v1`. Published `v0.2.0`, `v0.1.1`, and `v0.1.0` remain frozen and are never moved or overwritten.

## Change classes
- Patch (`0.2.x`): bug fixes, UI collision fixes, provider compatibility, security hardening, packaging fixes.
- Minor (`0.x.0`): new user-visible capability or compatible schema expansion.
- Major (`x.0.0`): intentional breaking project/schema/workflow change.

## Required gate before every release
1. compileall passes;
2. Ruff passes;
3. strict mypy passes;
4. cheap pytest passes;
5. representative STEP 09 Qt screenshot capture/verification passes;
6. portable PyInstaller build passes foundation smoke;
7. no secret/user runtime file appears in artifact;
8. SHA-256 is generated for the portable ZIP.

## External compatibility watch
Review before a patch release when any of these change:
- Gemini authentication/API behavior or provider error semantics;
- PySide6 / Qt version;
- Python 3.12 support window;
- FFmpeg build, codec set or license profile;
- Windows 11 packaging/runtime behavior.

## Security handling
Never request users to commit API keys. Reproduction bundles must use redacted diagnostics. Credential-store and provider changes require dedicated tests for raw-secret leakage.

## Project files
Keep versioned JSON migrations additive when possible. Never silently rewrite an unknown future schema version.

For the 0.2.1 line:
- schema v3 remains the legacy-compatible default until an advanced edit is committed;
- schema v4 requires `animation_keyframe_contract=advanced-v1`;
- no open/preview/render/normal-save path may implicitly promote v3;
- normal Save must not downgrade v4 to v3;
- the first successful v3→v4 overwrite creates a non-clobbering `.pre-schema-v4.bak`;
- future schema or schema/marker mismatches must fail closed before live-session mutation.
