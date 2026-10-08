# STEP 06 / W06-B — Snapshot Provenance and Crash-Window Evidence

**Date:** 8 October 2026 WIB. **Repository:** `inoriko920-dev/V2-AI-Video-Composer` only.  
**Baseline main:** `3e6da05fcae5f38ddf3b0ed3dbf595f99c49dfaf` (W06-A PR #57 merged).  
**Stable immutable `v0.2.2` tag:** `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.  
**Current gate:** HOLD until final PR CI, CodeQL, backend and Windows acceptance PASS and merge to main is verified.

## Implementation delivered (bounded W06-B scope)

- New `src/aavc/persistence/snapshot_provenance.py` provides `ProvenanceStore`, fail-closed immutable `RecoveryCandidate` classification, `RecoveryRaceChanged`, and a checked quarantine/rollback/retirement staging helper.
- Writes use existing `RecoveryManager.write_snapshot`, existing `ProjectState` serializer and validator. No parallel serializer, no changes to `.aavcproj` schemas or pre-recovery backups.
- Sidecar path `<project>.aavcproj.autosave.meta.json`; format version 1; strict 16 KiB bound; strict digest/format/schema types, only path identity digest (not raw path), saved disk byte SHA-256, snapshot byte SHA-256, schema v3/v4, random per-write generation identifier. No project body or credentials are written to the sidecar.
- File-level publication order: preflight immutable baseline digest and validation → replace `.autosave` using existing atomic sibling → verify project baseline again → write/fsync temporary metadata and replace metadata last. There is NO two-file atomic transaction: interruptions between snapshot and metadata leave `UNCERTAIN` candidate.
- `inspect` is read-only: `ABSENT` / `VERIFIED` / `UNCERTAIN` / `INVALID`. Legacy missing metadata, stale metadata, unknown descriptor, schema mismatch and external baseline changes never become `VERIFIED` automatically.
- `revalidate` binds disk, snapshot, descriptor content hashes and classification before later destructive decisions; changed disk/snapshot/metadata invalidates stale preflight. Quarantine stages only the checked snapshot/descriptor; rollback or retirement fail if filenames are occupied or quarantined bytes differ. No automatic deletion is performed during inspection.
- A process-wide Python `RLock` serializes **this store's** operations, but **does not** synchronize with external processes or existing ProjectSession Save; physical coordination with W06-A and Save/Restore transactions remains W06-C.
- Simple known-key/known-format credential detection rejects suspicious ProjectState, without claiming comprehensive secret detection. Test inputs are synthetic only; no real tokens or private user files were used.
- Existing `RecoveryManager.restore_snapshot`, all Qt components, Save/Open transaction, background scheduler wiring, FFmpeg, 42 frozen UI screens and three user-approved dialogs remain unchanged.

## Test-first evidence (real GitHub Actions)

1. **RED run `37750055508`:** before module existed, new tests failed at collection with `ModuleNotFoundError: aavc.persistence.snapshot_provenance`.
2. Intermediate run `37750204762`: 22 passed and 1 failed solely because schema-v4 fixture omitted its required `animation_keyframe_contract=advanced-v1` marker. Corrected fixture; production serializer/contract was NOT weakened.
3. **GREEN run `37750579176`: 27 passed** with Python 3.12, isolated temp files and deterministic fault hooks. Coverage includes AT-01..11 aspects, AT-12 quarantine staging only, metadata crash gap, stale path/hash, symlink rejection, malformed/future snapshot, legacy metadata, v4 contract, secret canary, ownership-based quarantine rollback/retirement and modified metadata fingerprint.
4. The temporary standalone workflow is deleted before the actual PR diff. CI and Windows acceptance must be rerun on final PR head before W06-B PASS.

## Critical limits / next W06-C wave

- W06-B **does not** make automatic autosave functional in the editor: the W06-A coordinator is not connected to this adapter; QTimer, user dialog, Save/Save As/Open/Restore/Discard are not wired.
- AT-12's *two concurrent real Restore transactions* is NOT proven here: we only test exclusive quarantine staging. Actual Restore backup/replace, Save path fencing, post-commit session adopt, cross-process races, and crash-time recovery policy belong to W06-C, then Qt W06-D.
- No unconditional claim of power-loss durability on Windows: the sidecar temp is file-fsynced where supported, but directory-level durability, snapshot serializer fsync and true two-file atomicity are not guaranteed.
- SHA-256 detects accidental changes, not an authenticated signature. File-system hard links, network drives and adversarial writers are not proven safe by the in-process lock.
- `retire_quarantine` is a helper for W06-C **after** a successful disk session commitment; its existence does not authorize background cleanup of any user files.
- Stable `v0.2.2` tag and original legacy repo must remain untouched.

## Exit / rollback / handoff

Require final PR-head Ruff, strict mypy, all pytest tests, CodeQL, Windows 11 portable acceptance and backend green; merge to main; verify module, tests and this evidence file actually exist on main; old tag unchanged. If any gate fails, remain HOLD, fix W06-B only.

**NEXT only on later explicit `lanjutkan`: W06-C** — integrate Save/Open/Save As/Restore/Discard transaction/lease/fence and safe session adoption. Do not code W06-C now; no new DOCX per implementation wave unless an architectural contract decision changes.
