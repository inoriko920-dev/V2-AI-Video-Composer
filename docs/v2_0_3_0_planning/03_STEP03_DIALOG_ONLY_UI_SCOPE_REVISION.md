# STEP 03-R — Revisi Cakupan UI: Pertahankan UI Lama, Hanya 3 Referensi Dialog Baru

**Status: Revised planning/UI reference scope; implementation NOT authorized.**
**Authoritative effective decision:** User explicitly approved retaining the original UI 1:1 and reducing 13 new UI image concepts to **three dialog references**. This revision supersedes the STEP03 original 13-image mandate, not the underlying STEP01/02 recovery safety contracts.
**Date:** 8 Oktober 2026 WIB. **Repo:** `inoriko920-dev/V2-AI-Video-Composer`.
**Frozen stable:** `v0.2.2` @ `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef`.
**Read with:** `docs/UI_FREEZE.md`, `01_AUTOSAVE_RECOVERY_FUNCTIONAL_LIFECYCLE_SPEC.md`, `02_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.md`.

## 1. Alasan koreksi dan batas pekerjaan

UI aplikasi lama sudah tersedia, mempunyai 42 referensi `UI-001..UI-042` dan screenshot runtime pembanding. Membangun ulang UI utama atau meminta 13 desain layar baru untuk state kecil menambah risiko perubahan tampilan tanpa manfaat.

**Koreksi penting dari pemeriksaan bukti aktual:** `UI-002_ACTUAL.png` adalah **halaman awal "Mulai Proyek"**, bukan editor. `UI-013_ACTUAL.png` menunjukkan contoh editor dengan menu atas, panel aset kiri, area preview tengah, panel properti kanan dan timeline bawah. Gunakan screenshot **real CI STEP09** (artifact "step09-ui-actual", CI run 37734080472, artifact 11531031921) sebagai bukti layout saat mengulas desain; teks contoh pada screenshot UI-013 seperti `Auto-saved` adalah *screenshot reference sample*, bukan bukti fitur autosave baru telah diimplementasikan.

**Keputusan final lingkup STEP03-R:**
1. **Pertahankan UI utama 1:1** pada seluruh halaman beku; khususnya Home, toolbar, preview, panel aset/properti/AI, timeline, navigasi, shortcut. Tidak membuat ulang atau menyalin ulang 42 layar.
2. Referensi visual baru cukup **3 dialog recovery**, semuanya di atas shell lama: `UI-REC-DLG-01`, `UI-REC-DLG-02`, `UI-REC-DLG-03`.
3. **Status autosave tidak membutuhkan gambar baru**: gunakan `QStatusBar` dan ikon/teks yang sudah ada, pesan nonmodal. Guard Save/Discard/Cancel lama tetap `QMessageBox` persis sebagaimana adanya.
4. Semua failure/prompt minor lain seperti `RACE_CHANGED`, Save As collision, no path, retry adalah varian pesan dalam dialog 02/03 atau status `QMessageBox` asli. Tidak ada jendela khusus untuk tiap skenario.
5. **Retain 13 prompt legacy** dan DOCX lama sebagai **arsip sejarah, bukan daftar pekerjaan wajib**. Tidak menghapusnya agar riwayat keputusan auditable; file ini adalah source-of-truth baru dan didahulukan.

## 2. Pemetaan 13 state legacy menjadi tepat 3 dialog + komponen lama

| ID lama | Kebutuhan asli | Implementasi desain setelah revisi |
|---|---|---|
| UI-REC-01 | Found valid snapshot | DLG-01 new recovery choice modal |
| UI-REC-02 | Uncertain/changed disk | DLG-02 conflict modal |
| UI-REC-03 | Extra conflict acknowledgment | **Second step within DLG-02**, no separate new dialog design |
| UI-REC-04 | Corrupt/future snapshot | DLG-03 safe error message on standard Qt QMessageBox style |
| UI-REC-05 | Disk/snapshot race changed | DLG-02 or DLG-03 copy variant ("Periksa Ulang"), not a new screen |
| UI-REC-06 | Pending debounce | Existing status bar `Menunggu jeda perubahan` |
| UI-REC-07 | Snapshot worker running | Existing status bar `Membuat cadangan otomatis…` |
| UI-REC-08 | Snapshot success | Existing status bar `Cadangan otomatis dibuat`, **dirty * remains** |
| UI-REC-09 | Snapshot failed | Existing status bar `Cadangan otomatis gagal`; optional original QMessageBox on user click |
| UI-REC-10 | Unsaved first path | Existing status bar + already existing Save action |
| UI-REC-11 | Save As collision | Existing native warning QMessageBox; choose other path / Cancel |
| UI-REC-12 | Restore failure | DLG-03 message variant; no new window architecture |
| UI-REC-13 | Existing unsaved guard | **No change**, reuse current GuardedMainWindow Qt dialog before any new recovery dialog |

No feature/safety case from STEP01/02 is waived by reducing the number of visuals.

## 3. Three reference dialogs; exact safe copy and behavior

### UI-REC-DLG-01 — Cadangan proyek ditemukan (normal valid candidate)

- **Trigger:** target disk ProjectState and autosave both valid; candidate differs, baseline hash matches; `RECOVERABLE_VERIFIED`.
- **Modal container:** existing editor/Home host; native Windows 11/PySide6 style, white surface, restrained blue focus/action; centered, approx 600–670 px wide at 1920x1080; do not replace shell.
- **Title:** `Cadangan Proyek Ditemukan`.
- **Description:** `Ada perubahan proyek yang ditemukan dalam cadangan otomatis.`
- **Project label:** `Proyek Dokumenter Suez.aavcproj` (example filename only; no real user path).
- **Body rows:** `Proyek tersimpan — versi terakhir yang Anda simpan secara manual` and `Cadangan otomatis — perubahan yang belum disimpan manual`.
- **Notice:** `Jika dipulihkan, salinan proyek tersimpan dibuat terlebih dahulu.`
- **Buttons:** `Pulihkan Cadangan`, `Gunakan Proyek Tersimpan`, `Batal`. Focus/default `Batal`; Escape cancels, Cancel leaves previous session/file unchanged. Restore must revalidate and create unique backup first. Discard must quarantine/retire exactly its own snapshot only after safe commit.
- **Not allowed:** invented timestamps, automatic Restore, false "Tersimpan" or credentials.

### UI-REC-DLG-02 — Cadangan perlu diperiksa (uncertain, changed disk, legacy)

- **Trigger:** `RECOVERABLE_UNCERTAIN` for valid differing snapshot with legacy/missing provenance, baseline changed, or hash/ownership doubt.
- **Title:** `Cadangan Perlu Diperiksa`.
- **Description:** `Versi proyek tersimpan mungkin berbeda dari versi saat cadangan dibuat.`
- **Info warning:** `Pemulihan hanya dilakukan setelah Anda menyetujuinya. Proyek tersimpan akan dicadangkan terlebih dahulu.`
- **Three choice buttons:** `Periksa dan Pulihkan` (warning-style secondary), `Gunakan Proyek Tersimpan`, `Batal` (default).
- **Secondary confirmation state** of *same modal component*, not a newly designed window: `Yakin ingin memulihkan cadangan meskipun data proyek berbeda?`; buttons `Ya, Pulihkan Cadangan` and `Batal` (default). A stale hash at action time yields `Data proyek berubah. Periksa ulang.` without writing.
- **Not allowed:** green "verified" badge, unconditional overwrite, assuming timestamp proves freshness, permanent "Don't show again" checkbox.

### UI-REC-DLG-03 — Cadangan tidak dapat dibaca (safe failure)

- **Trigger:** `INVALID_SNAPSHOT`, restore backup failure, partial-commit failure, uncertain or invalid target requiring safe user action.
- **Visual:** reuse the **already available native QMessageBox** look; screenshot reference only, no custom Qt framework. Same blue-white Windows theme.
- **Main title on invalid candidate:** `Cadangan Tidak Dapat Dibaca`.
- **Description:** `Cadangan otomatis tidak dapat dibuka dengan aman. File proyek tersimpan tidak diubah.`
- **Secondary line:** `File cadangan tetap disimpan untuk pemeriksaan.`
- **Buttons:** `Buka Proyek Tersimpan` and `Batal` (default). Never offer Restore for unreadable candidate.
- **Safe error variant:** `Pemulihan belum selesai. Jangan hapus berkas cadangan.` For partial-commit after durable replace, do **not** falsely say original disk was never modified; show accurate explicit state and backup availability.
- **Not allowed:** stack traces/API keys/full file paths; no destructive shortcut `Hapus Cadangan`.

## 4. Nonmodal status bar and legacy guard (zero custom UI screenshots)

Preserve existing QStatusBar geometry, size and colors. Wording:
- Dirty, deadline pending: `Cadangan otomatis menunggu jeda`.
- Writing: `Membuat cadangan otomatis…`.
- Success: `Cadangan otomatis dibuat`.
- Failed: `Cadangan otomatis gagal — simpan manual tersedia`.
- No saved location: `Simpan proyek untuk mengaktifkan cadangan otomatis`.
- Manual successful Save: `Proyek disimpan` (may clear title *).
**Crucial:** autosave success must *not* call normal Save, clear dirty marker, or add Undo/Redo. Status appears in existing bar, does not cover preview/timeline. Preserve `GuardedMainWindow` Save/Discard/Cancel before target recovery decision; legacy guard is **not** a new UI screen.

## 5. Visual reference acceptance and revised HARD STOP

**Required visual inputs now ONLY THREE**:
- `UI-REC-DLG-01.png`, `UI-REC-DLG-02.png`, `UI-REC-DLG-03.png`.
- Use `UI-013_ACTUAL.png` real editor screenshot for overlay comparison. Do not regenerate the editor shell, even in mockups.
- Prompt text lives in `docs/v2_0_3_0_planning/prompt_ui_step03_revised/` and this MD; the old 13 prompt files remain archived.
- Each visual must be inspected for Indonesian wording, correct buttons, clearly safe Cancel, no unnecessary timestamp, no image distortion of inherited UI. The design is approved **only by user's actual review**, not by successful build checks.
- After all **three images** are generated, reviewed/revised, and user-approved, create **one single final image-filled UI reference DOCX** under `docs/v2_0_3_0_planning/docx/03_V2_0.3.0_FINAL_APPROVED_UI_DIALOG_REFERENCES.docx` and commit it alongside images and signoff evidence.
- The prompt-planning DOCX `03_V2_0.3.0_DIALOG_ONLY_SCOPE_REVISION.docx` is **not** the final image reference DOCX. Do not confuse these documents.
- **Until these three images and final approved image reference DOCX are committed, STEP03 visual gate is still HOLD and STEP04–06 forbidden.** A generic `lanjutkan` cannot waive these requirements. Explicit consent to adjust from 13 to 3 is already granted and replaces the old quantity requirement.

## 6. Acceptance checklist and handoff

| Gate | Evidence | Passing rule |
|---|---|---|
| G-03-R1 | Main UI freeze | No app source, original repo, images UI-001..042, or version tag changed |
| G-03-R2 | Revised DOCX + Markdown | Complete scoped plan authored/visual QA; actual DOCX in V2 |
| G-03-R3 | Three distinct TXT prompts | 3 files, all exact Indonesian labels, no fake autosave save |
| G-03-R4 | Older prompts archival | 13 original prompts kept untouched, clearly superseded at index |
| G-03-R5 | PR gate | PR docs-only final-head CI, CodeQL, Windows, backend PASS before merge |
| G-03-R6 | Actual visual images | **HOLD** until 3 reviewed and approved PNGs |
| G-03-R7 | Final UI Reference DOCX | **HOLD** until one real image-filled, signed-off DOCX |
| G-03-R8 | STEP04 permission | Only after G-03-R6 and G-03-R7 PASS and separate user command |

**Stop here on planning revision after PR/Word QA. Do not code Qt, timers, persistence, tests, build release or create extra UI screens in this turn.**

## 7. AI handoff and rollback

Prioritize: `V2_0.3.0_PLANNING_STATUS.md` latest top section -> this revision `03_STEP03_DIALOG_ONLY_UI_SCOPE_REVISION.md` -> final Word of this revision -> original STEP01/02 safety contracts -> `docs/UI_FREEZE.md`. The original `03_PROMPT_GAMBAR_UI_RECOVERY_MASTER.md`, thirteen TXT and prompt DOCX are **historical only**.

Source branch `v2/0.3.0-step03-dialog-only-scope-revision`, founded on `bdc6680c6599eae8ef56b1a02c8431b6a56054fd`. Reverting only this docs PR restores 13-prompt instruction; **do not** restore application UI or change stable v0.2.2 as part of rollback.
