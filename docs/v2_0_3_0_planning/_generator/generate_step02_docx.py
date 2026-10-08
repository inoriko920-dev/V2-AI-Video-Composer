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
SOURCE = ROOT / "02_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.md"
OUTPUT = ROOT / "docx" / "02_V2_0.3.0_RECOVERY_ARCHITECTURE_ATOMICITY_SCHEDULER_PLAN.docx"
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

def build():
    content = SOURCE.read_text(encoding="utf-8")
    if "SnapshotProvenanceStore" not in content or "STEP03" not in content or "120 seconds" not in content:
        raise ValueError("Incorrect/incomplete source Markdown")
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
        ("STEP 02 | v0.3.0 ARCHITECTURE PLAN", 16),
        ("Atomicity, Coordinator & Scheduler Design", 12),
        ("ASTRA Planning • 8 Oktober 2026 • WIB", 9),
    ]:
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(value).font.size = Pt(size)
    meta = d.add_table(rows=0, cols=2)
    meta.style = "Table Grid"
    for key, val in [
        ("Repository", "inoriko920-dev/V2-AI-Video-Composer"),
        ("STEP02 baseline main", "fc587f82ce61c2f5438cc32c6f315c232e80c091"),
        ("Frozen stable", "v0.2.2 @ eeabf1ffbfac6cbb6cafc82116fc3599bdbc2bef"),
        ("Main goal", "Coordinator; provenance; 20s/120s/60s scheduling"),
        ("Authorization", "STEP02 planning only; no coding or UI changes"),
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
    header.add_run("V2 0.3.0 / STEP02 PLANNING").font.size = Pt(8)
    foot = section.footer.paragraphs[0]
    foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    foot.add_run("Planning only  |  Page ").font.size = Pt(8)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    foot._p.append(field)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    d.save(OUTPUT)
    proof = Document(OUTPUT)
    if len(proof.paragraphs) < 70 or len(proof.tables) < 7:
        raise ValueError("Generated DOCX is incomplete")
    print("STEP02_DOCX_PASS", OUTPUT, len(proof.paragraphs), len(proof.tables))

if __name__ == "__main__":
    build()
