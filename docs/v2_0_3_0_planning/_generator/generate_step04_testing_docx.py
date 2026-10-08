"""Build v0.3.0 STEP04 planning DOCX from authoritative Markdown; planning-only.

Usage: python docs/v2_0_3_0_planning/_generator/generate_step04_testing_docx.py
Deterministic document content/layout. Binary ZIP metadata may vary across runs.
"""
from __future__ import annotations
import re
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '04_RECOVERY_FAILURE_INJECTION_WINDOWS_TEST_PLAN.md'
DEST = ROOT / 'docx' / '04_V2_0.3.0_RECOVERY_FAILURE_INJECTION_WINDOWS_TEST_PLAN.docx'

DARK=RGBColor(27,50,86)
BLUE=RGBColor(33,100,181)
GREY=RGBColor(81,96,112)

def shade(cell, fill='EAF2FA'):
    tcPr=cell._tc.get_or_add_tcPr()
    sh=OxmlElement('w:shd'); sh.set(qn('w:fill'),fill); tcPr.append(sh)

def set_repeat(row):
    trPr=row._tr.get_or_add_trPr(); e=OxmlElement('w:tblHeader'); e.set(qn('w:val'),'true');trPr.append(e)

def mark_cant_split(row):
    trPr=row._tr.get_or_add_trPr(); e=OxmlElement('w:cantSplit');trPr.append(e)

def add_inline(p, val):
    # Markdown inline formatting: preserve text and backtick/bold emphasis.
    for chunk in re.split(r'(`[^`]*`|\*\*[^*]+\*\*)',val):
        if not chunk:continue
        if chunk.startswith('`') and chunk.endswith('`'):
            t=p.add_run(chunk[1:-1]);t.font.name='Consolas';t.font.size=Pt(7.8);t.font.color.rgb=BLUE
        elif chunk.startswith('**') and chunk.endswith('**'):
            t=p.add_run(chunk[2:-2]);t.bold=True
        else:
            p.add_run(chunk)

def table_from_lines(doc, matrix):
    # Simple GFM tables, dynamic width distribution + generous repeat headers.
    parsed=[]
    for s in matrix:
        cells=[x.strip() for x in s.strip().strip('|').split('|')]
        if all(re.fullmatch(r':?-{3,}:?',c or '') for c in cells):continue
        parsed.append(cells)
    if not parsed:return
    n=max(map(len,parsed)); parsed=[r+['']*(n-len(r)) for r in parsed]
    table=doc.add_table(rows=1, cols=n)
    table.style='Table Grid';table.alignment=WD_TABLE_ALIGNMENT.CENTER
    table.autofit=True
    first=table.rows[0];set_repeat(first)
    for j,v in enumerate(parsed[0]):
        cell=first.cells[j];cell.text='';shade(cell,'DAE8F7')
        p=cell.paragraphs[0];add_inline(p,v)
        for run in p.runs:run.bold=True;run.font.color.rgb=DARK;run.font.size=Pt(8.3)
    mark_cant_split(first)
    for rowi,parts in enumerate(parsed[1:]):
        row=table.add_row();mark_cant_split(row)
        if rowi%2: [shade(cell,'F7FAFD') for cell in row.cells]
        for j,v in enumerate(parts):
            p=row.cells[j].paragraphs[0];p.style=doc.styles['Table Text'];add_inline(p,v)
    doc.add_paragraph().paragraph_format.space_after=Pt(0)

def main():
    text=SOURCE.read_text('utf-8')
    doc=Document();section=doc.sections[0]
    section.page_height=Cm(29.7);section.page_width=Cm(21)
    section.top_margin=Cm(2.0);section.bottom_margin=Cm(1.8)
    section.left_margin=Cm(2.1);section.right_margin=Cm(1.9)
    header=section.header.paragraphs[0]
    header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    h=header.add_run('V2 AI VIDEO COMPOSER  /  STEP 04  /  8 OKTOBER 2026 WIB')
    h.font.size=Pt(7.5);h.font.color.rgb=GREY
    footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    f=footer.add_run('ASTRA · PLANNING ONLY · NO APP CODING · v0.3.0 PROPOSED')
    f.font.size=Pt(7);f.font.color.rgb=GREY
    styles=doc.styles
    normal=styles['Normal'];normal.font.name='Aptos';normal.font.size=Pt(9.2)
    normal.font.color.rgb=RGBColor(45,58,73)
    normal.paragraph_format.space_after=Pt(6)
    normal.paragraph_format.line_spacing=1.12
    for name,size,before,after in [('Title',21,2,10),('Heading 1',15,14,7),('Heading 2',11.7,11,5),('Heading 3',10,8,3)]:
        s=styles[name];s.font.name='Aptos Display';s.font.size=Pt(size);s.font.color.rgb=DARK;s.font.bold=True
        s.paragraph_format.space_before=Pt(before);s.paragraph_format.space_after=Pt(after)
        s.paragraph_format.keep_with_next=True
    if 'Table Text' not in styles:
        ts=styles.add_style('Table Text', WD_STYLE_TYPE.PARAGRAPH)
    else:ts=styles['Table Text']
    ts.font.name='Aptos';ts.font.size=Pt(8)
    ts.paragraph_format.space_after=Pt(1);ts.paragraph_format.space_before=Pt(0)
    ts.paragraph_format.line_spacing=1.04
    buf=[];prev_title=False
    def flush():
        nonlocal buf
        if buf:table_from_lines(doc,buf);buf=[]
    for line in text.splitlines():
        if line.startswith('|'):
            buf.append(line);continue
        flush()
        stripped=line.strip()
        if not stripped:continue
        if stripped.startswith('# '):
            p=doc.add_paragraph(style='Title');add_inline(p,stripped[2:]);prev_title=True
        elif stripped.startswith('## '):
            p=doc.add_paragraph(style='Heading 1');add_inline(p,stripped[3:]);prev_title=False
        elif stripped.startswith('### '):
            p=doc.add_paragraph(style='Heading 2');add_inline(p,stripped[4:]);prev_title=False
        elif stripped.startswith('#### '):
            p=doc.add_paragraph(style='Heading 3');add_inline(p,stripped[5:]);prev_title=False
        elif stripped.startswith('- '):
            p=doc.add_paragraph(style='List Bullet');add_inline(p,stripped[2:]);prev_title=False
        elif re.match(r'^\d+\.\s',stripped):
            p=doc.add_paragraph(style='List Number');add_inline(p,re.sub(r'^\d+\.\s','',stripped));prev_title=False
        else:
            p=doc.add_paragraph();add_inline(p,stripped.rstrip('  '));prev_title=False
    flush()
    # avoid accidental editing rights assumptions; explicit metadata only
    props=doc.core_properties;props.title='V2 AI Video Composer - STEP04 Recovery Testing Plan'
    props.subject='Planning-only test-first specifications for v0.3.0 recovery'
    props.author='ASTRA Planning'
    DEST.parent.mkdir(parents=True,exist_ok=True)
    doc.save(DEST)
    print('CREATED', DEST)
    print('SIZE_BYTES', DEST.stat().st_size)
    print('TABLES',len(doc.tables),'PARAGRAPHS',len(doc.paragraphs))

if __name__=='__main__':main()