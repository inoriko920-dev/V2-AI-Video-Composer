# STEP03 — UI Image Prompt Completion & Hard Stop Handoff (v0.3.0)

**PROMPTS COMPLETE / VISUAL REFERENCE GATE HOLD.** This document records only prompt output. There are NO approved UI pictures, no approved composite UI reference DOCX, no Qt implementation and no STEP04 authorization.

## Source of truth and version lock
- Repo: `inoriko920-dev/V2-AI-Video-Composer`.
- Published stable v0.2.2: `eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef` — immutable.
- STEP02 merged main baseline: `d076a9bfe49c0fe47988fd815fd8fde36ab83c8a`.
- UI freeze: `docs/UI_FREEZE.md` references 42 screens UI-001..UI-042, editor UI-002, 1920x1080 white-blue Indonesian Qt desktop.
- Master prompt: `docs/v2_0_3_0_planning/03_PROMPT_GAMBAR_UI_RECOVERY_MASTER.md`.
- Full prompt Word: `docs/v2_0_3_0_planning/docx/03_V2_0.3.0_STEP03_UI_IMAGE_PROMPTS_ONLY.docx` (a **prompt document**, not the future approved UI image reference document).
- Per-screen TXT: `docs/v2_0_3_0_planning/prompt_ui_step03/` — thirteen separately usable UI-REC-XX prompt files.
- Deterministic generator: `docs/v2_0_3_0_planning/_generator/generate_step03_prompt_docs.py`.
- Prompt-package Actions run: `37733837073` PASS; 13 TXT + Word, each TXT explicitly says HARD STOP. Initial run `37733751867` failed because the QA rule required a literal hard-stop token absent from individual TXT; this was corrected without any application changes.

## Visual asset list — ALL NOT YET GENERATED/APPROVED
1. `UI-REC-01_VALID_RECOVERY.png`
2. `UI-REC-02_CONFLICT_WARNING.png`
3. `UI-REC-03_CONFLICT_CONFIRMATION.png`
4. `UI-REC-04_INVALID_SNAPSHOT.png`
5. `UI-REC-05_SOURCE_CHANGED.png`
6. `UI-REC-06_AUTOSAVE_PENDING.png`
7. `UI-REC-07_AUTOSAVE_WORKING.png`
8. `UI-REC-08_AUTOSAVE_SUCCESS.png`
9. `UI-REC-09_AUTOSAVE_ERROR.png`
10. `UI-REC-10_UNSAVED_FIRST_PATH.png`
11. `UI-REC-11_SAVE_AS_COLLISION.png`
12. `UI-REC-12_RESTORE_FAILURE.png`
13. `UI-REC-13_EXISTING_UNSAVED_GUARD.png`

## Required image-production/review process BEFORE any further step
- Open each corresponding `UI-REC-XX_*.txt`, generate **one** 1920x1080 image for that state. Do not collage states. Maintain established UI-002 shell, professional white-blue design, Indonesian text, 2% safe zone, original 42 screenshots as style authority.
- Review against master and STEP01/02 safety contracts. Check legibility, every exact button/action, no inappropriate auto-restore, no false "saved" status, the preexisting dirty guard first, no credentials, no spurious controls. Track PASS/REVISE/REJECT with reasons; regenerate/revise only failed image.
- When **all thirteen images** are confirmed acceptable, build **ONE** new final UI reference DOCX containing the complete 13 images with caption/ID, design acceptance decisions, applicable wording/keyboard/focus notes, and revision evidence. Clearly label it `03_V2_0.3.0_APPROVED_FINAL_UI_IMAGE_REFERENCES.docx`. That DOCX must include images themselves, not just file paths or prompt text.
- Put all approved source PNGs, approval/QA notes and the ONE final UI image reference DOCX into the V2 GitHub repository as source of truth. Do not mark the UI gate PASS if any is absent, unreadable or not approved.
- Only after the visual gate is explicitly completed can a **new** user instruction authorize STEP04 testing-plan DOCX. STEP05 must independently require all planning DOCXs + this final UI reference; STEP06 coding stays blocked.

## Mandatory response to a premature "lanjutkan"
Tell the user the project is **waiting for 13 UI images and their review**, and keep the work stopped. A bare "lanjutkan" never waives this gate. If user explicitly directs generation or provides PNGs, perform only the necessary visual work, review and final UI reference assembly; do not start STEP04 in that same turn.

## Absolute forbidden during/after this STEP03 prompt package
- No Python/PySide6/QT source modification, no v0.3.0 schema/version bump, no FFmpeg/provider/animation changes.
- No release tags, no published v0.2.2 tag/artifact replacement.
- No creation of claimed final approved UI image DOCX using empty placeholders or AI prompt text alone.
- No marking STEP04 or STEP05 PASS, no SOL coding.

**Correct final STEP03 gate:** `PROMPTS COMPLETE / STOP — WAITING FOR 13 GENERATED, APPROVED UI IMAGES + SINGLE FINAL IMAGE REFERENCE DOCX`.
