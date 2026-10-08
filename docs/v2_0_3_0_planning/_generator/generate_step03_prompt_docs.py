"""Deterministic STEP00 Markdown -> DOCX, planning only. No application imports."""
from __future__ import annotations
import re
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "03_PROMPT_GAMBAR_UI_RECOVERY_MASTER.md"
OUTPUT = ROOT / "docx" / "03_V2_0.3.0_STEP03_UI_IMAGE_PROMPTS_ONLY.docx"
NAVY = RGBColor(22, 63, 110)
TICK = chr(96)

def inline(p, text):
    pattern = r"(\*\*[^*]+\*\*|" + TICK + "[^" + TICK + "]+" + TICK + ")"
    for part in re.split(pattern, text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            p.add_run(part[2:-2]).bold = True
        elif part.startswith(TICK) and part.endswith(TICK):
            run = p.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(8.4)
            run.font.color.rgb = NAVY
        else:
            p.add_run(part)

def no_split(row):
    props = row._tr.get_or_add_trPr()
    props.append(OxmlElement("w:cantSplit"))

PROMPT_DIR = ROOT / "prompt_ui_step03"
NEGATIVE = "JANGAN: dark mode, tema hitam/neon, bahasa Mandarin/Inggris pada kontrol, teks lorem ipsum/acak, watermark, brand asing, UI mobile, 3D isometrik, gambar poster, ilustrasi kartun, komik, foto orang, panel editor baru, redesign timeline, tombol Generate Video/Publish/Cloud Sync palsu, proses pemulihan otomatis tanpa konfirmasi, tulisan 'Proyek disimpan' untuk snapshot otomatis, tampilkan API key/password/nomor akun, hapus cadangan tanpa izin, ikon bahaya besar yang dramatis, dialog melebar melampaui layar, elemen overlay bertumpuk atau terpotong."

def write_txts(content: str) -> int:
    import re
    lines = content.splitlines()
    master_start = next(i for i,x in enumerate(lines) if x.strip()=="### A. MASTER DESAIN")
    first_state = next(i for i,x in enumerate(lines) if x.startswith("### B. PROMPT STATE UI-REC-01"))
    master = "\n".join(lines[master_start+1:first_state]).strip()
    if len(master)<350:
        raise ValueError("Master design prompt missing")
    starts=[i for i,x in enumerate(lines) if x.startswith("### B. PROMPT STATE UI-REC-")]
    if len(starts)!=13:
        raise ValueError(f"Expected 13 distinct states; found {len(starts)}")
    PROMPT_DIR.mkdir(parents=True,exist_ok=True)
    seen=set()
    for idx,start in enumerate(starts):
        header=lines[start]
        m=re.search(r"(UI-REC-\d{2})",header)
        if not m:
            raise ValueError("Missing UI-REC id")
        ident=m.group(1)
        if ident in seen:
            raise ValueError("Duplicate prompt")
        seen.add(ident)
        end=starts[idx+1] if idx+1<len(starts) else next(i for i in range(start+1,len(lines)) if lines[i].startswith("## 6."))
        block="\n".join(lines[start+1:end]).strip()
        out_match=re.search(r"\*\*Output name:\*\* (UI-REC-\d{2}_[A-Z_]+)\.png",block)
        if not out_match:
            raise ValueError(f"Output name is missing for {ident}")
        stem=out_match.group(1)
        actual=re.search(r"\*\*Prompt:\*\* (.*)",block,re.DOTALL)
        if not actual:
            raise ValueError(f"Prompt absent {ident}")
        unique=actual.group(1).strip()
        if len(unique)<250:
            raise ValueError(f"Prompt too short: {ident}")
        text_data=(
            "AAVC V2 0.3.0 — STEP03 UI PROMPT (REFERENCE ONLY)\n"
            + f"State ID: {ident}\nOutput: {stem}.png\n"
            + "DO NOT IMPLEMENT QT OR MOVE TO STEP04 FROM THIS PROMPT.\n\n"
            + "A. MASTER DESIGN\n" + master
            + "\n\nB. NEGATIVE REQUIREMENTS\n" + NEGATIVE
            + "\n\nC. UNIQUE IMAGE STATE\n" + unique
            + "\n\nD. OUTPUT RULE\nOne single 1920x1080 PNG per file; existing frozen UI preserved, no watermark, all text legible and Indonesian. Final visual still needs user review/approval.\n"
        )
        (PROMPT_DIR / (stem+".txt")).write_text(text_data,encoding="utf-8")
    print("STEP03_PER_IMAGE_TXT_PASS",len(seen))
    return len(seen)

def build():
    content = SOURCE.read_text(encoding="utf-8")
    if "UI-REC-13" not in content or "HARD STOP" not in content or "MASTER DESAIN" not in content:
        raise ValueError("Incorrect/incomplete source Markdown")
    count=write_txts(content)
    if count!=13:
        raise ValueError('Prompts incomplete')
    d = Document()
    section = d.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21)
    section.top_margin = Cm(1.62)
    section.bottom_margin = Cm(1.52)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)
    normal = d.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(9.3)
    normal.paragraph_format.space_after = Pt(3.5)
    for sty, size in (("Heading 1", 13), ("Heading 2", 10.7)):
        style = d.styles[sty]
        style.font.color.rgb = NAVY
        style.font.size = Pt(size)
        style.font.bold = True
        style.paragraph_format.keep_with_next = True

    title = d.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("V2 AI VIDEO COMPOSER")
    run.bold = True
    run.font.size = Pt(23)
    run.font.color.rgb = NAVY
    for value, size in [
        ("STEP 03 | v0.3.0 UI PROMPT HARD STOP", 16),
        ("13 Recovery UI Image Prompts • Reference Only", 12),
        ("ASTRA Planning • 8 Oktober 2026 • WIB", 9),
    ]:
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(value).font.size = Pt(size)
    meta = d.add_table(rows=0, cols=2)
    meta.style = "Table Grid"
    for key, val in [
        ("Repository", "inoriko920-dev/V2-AI-Video-Composer"),
        ("STEP03 baseline main", "d076a9bfe49c0fe47988fd815fd8fde36ab83c8a"),
        ("Frozen stable", "v0.2.2 @ eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef"),
        ("Main goal", "13 static UI mockup prompts, one per screen"),
        ("Authorization", "STEP03 prompts only; no coding or UI changes"),
        ("UI hard stop", "Required at future UI-prompt STEP"),
    ]:
        row = meta.add_row()
        row.cells[0].text = key
        row.cells[1].text = val
        no_split(row)
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs:
                    run.font.size = Pt(7.5)
        for run in row.cells[0].paragraphs[0].runs:
            run.bold = True
    d.add_paragraph()

    buffer = []
    table = []
    def flush():
        if buffer:
            p = d.add_paragraph()
            inline(p, " ".join(buffer))
            buffer.clear()
    def flush_table():
        if not table:
            return
        records = [[c.strip() for c in line.strip("|").split("|")] for line in table]
        table.clear()
        records = [cells for cells in records if not all(re.fullmatch(r"[:\-\s]*", cell) for cell in cells)]
        if not records:
            return
        colcount = max(len(cells) for cells in records)
        out = d.add_table(rows=0, cols=colcount)
        out.style = "Table Grid"
        for index, cells in enumerate(records):
            row = out.add_row()
            no_split(row)
            if index == 0:
                heading_prop = OxmlElement("w:tblHeader")
                heading_prop.set(qn("w:val"), "1")
                row._tr.get_or_add_trPr().append(heading_prop)
            for ci, cell in enumerate(row.cells):
                p = cell.paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                inline(p, cells[ci] if ci < len(cells) else "")
                for run in p.runs:
                    run.font.size = Pt(7.5)
                    if index == 0:
                        run.bold = True
                        run.font.color.rgb = NAVY
        d.add_paragraph()
    for raw in content.splitlines():
        line = raw.strip()
        if line.startswith("|") and line.endswith("|"):
            flush()
            table.append(line)
            continue
        if table:
            flush_table()
        if not line:
            flush()
            continue
        if line.startswith("# "):
            flush()
            continue
        if line.startswith("## "):
            flush()
            p = d.add_heading(level=1)
            inline(p, line[3:])
            continue
        if line.startswith("### "):
            flush()
            p = d.add_heading(level=2)
            inline(p, line[4:])
            continue
        if line.startswith("- "):
            flush()
            inline(d.add_paragraph(style="List Bullet"), line[2:])
            continue
        if re.match(r"^\d+\.\s+", line):
            flush()
            inline(d.add_paragraph(style="List Number"), re.sub(r"^\d+\.\s+", "", line))
            continue
        buffer.append(line)
    flush()
    flush_table()

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header.add_run("V2 0.3.0 / STEP03 PROMPT HARD STOP").font.size = Pt(8)
    foot = section.footer.paragraphs[0]
    foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    foot.add_run("Planning only  |  Page ").font.size = Pt(8)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    foot._p.append(field)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    d.save(OUTPUT)
    proof = Document(OUTPUT)
    if len(proof.paragraphs) < 55 or len(proof.tables) < 2:
        raise ValueError("Generated DOCX is incomplete")
    print("STEP03_DOCX_PASS", OUTPUT, len(proof.paragraphs), len(proof.tables), 'txt_count',count)

if __name__ == "__main__":
    build()
