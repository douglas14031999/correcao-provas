import io
import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from .base_report import ReportData

def set_cell_background(cell, hex_color: str):
    """Sets background shading of a docx table cell."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color.replace("#", ""))
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets internal cell margins in twips."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m_name, m_val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m_name}')
        node.set(qn('w:w'), str(m_val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_border(cell, **kwargs):
    """Sets borders on a docx cell. kwargs: top, bottom, left, right dict(val='single', sz='4', color='CBD5E1')"""
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = OxmlElement(tag)
            for key, val in edge_data.items():
                element.set(qn(f'w:{key}'), str(val))
            tcBorders.append(element)
    tcPr.append(tcBorders)

def set_table_borders_none(table):
    """Removes all borders from a table."""
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        tblBorders = OxmlElement('w:tblBorders')
        for b_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            b = OxmlElement(f'w:{b_name}')
            b.set(qn('w:val'), 'none')
            tblBorders.append(b)
        tblPr[0].append(tblBorders)

def build_docx_report(data: ReportData) -> bytes:
    """Builds an official formatted Microsoft Word (.docx) report."""
    doc = Document()

    # Configure A4 page with 12mm margins
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)

    # 1. INSTITUTIONAL HEADER TABLE (Logo on Left + Left-aligned Hierarchy on Right)
    hdr_table = doc.add_table(rows=1, cols=2)
    hdr_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders_none(hdr_table)

    cell_logo = hdr_table.cell(0, 0)
    cell_text = hdr_table.cell(0, 1)

    cell_logo.width = Inches(0.95)
    cell_text.width = Inches(6.32)
    cell_logo.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    cell_text.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_margins(cell_logo, top=0, bottom=40, left=0, right=30)
    set_cell_margins(cell_text, top=0, bottom=40, left=30, right=0)

    # Insert logo
    p_logo = cell_logo.paragraphs[0]
    p_logo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_logo.paragraph_format.space_after = Pt(0)
    if data.metadata.logo_path and os.path.exists(data.metadata.logo_path):
        try:
            r_img = p_logo.add_run()
            r_img.add_picture(data.metadata.logo_path, width=Inches(0.78))
        except Exception:
            pass

    # Insert text hierarchy
    p_text = cell_text.paragraphs[0]
    p_text.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_text.paragraph_format.space_after = Pt(0)
    p_text.paragraph_format.line_spacing = 1.15

    r_pref = p_text.add_run(f"{data.metadata.prefeitura.upper()}\n")
    r_pref.font.name = "Segoe UI"
    r_pref.font.size = Pt(11)
    r_pref.font.bold = True
    r_pref.font.color.rgb = RGBColor(15, 23, 42)

    r_sec = p_text.add_run(f"{data.metadata.secretaria.upper()}\n")
    r_sec.font.name = "Segoe UI"
    r_sec.font.size = Pt(9.5)
    r_sec.font.color.rgb = RGBColor(51, 65, 85)

    school_name_display = data.metadata.school_name.upper() if data.metadata.school_name else ""
    if data.metadata.inep_code:
        school_name_display += f" — INEP: {data.metadata.inep_code}"
    r_esc = p_text.add_run(school_name_display)
    r_esc.font.name = "Segoe UI"
    r_esc.font.size = Pt(9.5)
    r_esc.font.bold = True
    r_esc.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # 2. DOCUMENT TITLE BANNER TABLE
    title_table = doc.add_table(rows=1, cols=1)
    title_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders_none(title_table)
    cell = title_table.cell(0, 0)
    set_cell_background(cell, "1E293B")
    set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
    
    p_t = cell.paragraphs[0]
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = p_t.add_run(data.title.upper())
    r_t.font.name = "Segoe UI"
    r_t.font.size = Pt(10.5)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(255, 255, 255)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # 3. METADATA TABLE (2 rows x 3 columns)
    meta_table = doc.add_table(rows=2, cols=3)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders_none(meta_table)
    m = data.metadata

    meta_cols_width = [Inches(3.20), Inches(2.30), Inches(1.77)]
    for row in meta_table.rows:
        for idx, w in enumerate(meta_cols_width):
            row.cells[idx].width = w

    meta_cells = [
        (0, 0, "Turma: ", m.classroom_name or "-"),
        (0, 1, "Turno: ", m.shift or "( ) MANHÃ       ( ) TARDE"),
        (0, 2, "Ano Letivo: ", m.school_year or "2026"),
        (1, 0, "Avaliação: ", m.exam_title or "Geral"),
        (1, 1, "Série/Ano: ", m.grade_year or "-"),
        (1, 2, "Total Alunos: ", str(len(data.rows))),
    ]

    border_spec = {'val': 'single', 'sz': '4', 'color': 'CBD5E1'}
    for r_idx, c_idx, lbl, val in meta_cells:
        c = meta_table.cell(r_idx, c_idx)
        set_cell_background(c, "F8FAFC")
        set_cell_margins(c, top=80, bottom=80, left=120, right=120)
        set_cell_border(c, top=border_spec, bottom=border_spec, left=border_spec, right=border_spec)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        
        r_lbl = p.add_run(lbl)
        r_lbl.font.name = "Segoe UI"
        r_lbl.font.size = Pt(8.5)
        r_lbl.font.bold = True
        r_lbl.font.color.rgb = RGBColor(15, 23, 42)

        r_v = p.add_run(val)
        r_v.font.name = "Segoe UI"
        r_v.font.size = Pt(8.5)
        r_v.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 4. SUMMARY CARDS
    if data.summary_cards:
        cards_table = doc.add_table(rows=1, cols=len(data.summary_cards))
        cards_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for idx, card in enumerate(data.summary_cards):
            c = cards_table.cell(0, idx)
            set_cell_background(c, "F1F5F9")
            set_cell_margins(c, top=100, bottom=100, left=120, right=120)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            r_l = p.add_run(f"{card.get('label', '').upper()}\n")
            r_l.font.name = "Segoe UI"
            r_l.font.size = Pt(7)
            r_l.font.bold = True
            r_l.font.color.rgb = RGBColor(100, 116, 139)
            
            r_v = p.add_run(str(card.get('value', '')))
            r_v.font.name = "Segoe UI"
            r_v.font.size = Pt(10)
            r_v.font.bold = True
            r_v.font.color.rgb = RGBColor(15, 23, 42)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 5. DATA TABLES (Supports single table or multiple sections)
    def render_docx_table(cols, rows, sec_title=None, sec_subtitle=None):
        if sec_title:
            p_sec = doc.add_paragraph()
            p_sec.paragraph_format.space_before = Pt(6)
            p_sec.paragraph_format.space_after = Pt(2)
            r_title = p_sec.add_run(sec_title.upper())
            r_title.font.name = "Segoe UI"
            r_title.font.size = Pt(9.5)
            r_title.font.bold = True
            r_title.font.color.rgb = RGBColor(30, 41, 59)
            if sec_subtitle:
                r_sub = p_sec.add_run(f" — {sec_subtitle}")
                r_sub.font.name = "Segoe UI"
                r_sub.font.size = Pt(7.5)
                r_sub.font.italic = True
                r_sub.font.color.rgb = RGBColor(100, 116, 139)

        table = doc.add_table(rows=1 + len(rows), cols=len(cols))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Header Row
        for c_idx, col in enumerate(cols):
            c = table.cell(0, c_idx)
            set_cell_background(c, "334155")
            set_cell_margins(c, top=100, bottom=100, left=100, right=100)
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if col.align == "center":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif col.align == "right":
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

            r = p.add_run(col.header)
            r.font.name = "Segoe UI"
            r.font.size = Pt(8.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

        # Data Rows
        for r_idx, row_dict in enumerate(rows, start=1):
            is_even = (r_idx % 2 == 0)
            row_bg = "F8FAFC" if is_even else "FFFFFF"
            
            # Highlight summary/total rows
            is_total_row = any(isinstance(v, str) and ("TOTAL" in v.upper() or "SUBTOTAL" in v.upper()) for v in row_dict.values() if v)
            if is_total_row:
                row_bg = "E2E8F0"

            for c_idx, col in enumerate(cols):
                c = table.cell(r_idx, c_idx)
                set_cell_background(c, row_bg)
                set_cell_margins(c, top=80, bottom=80, left=80, right=80)
                p = c.paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                if col.align == "center":
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif col.align == "right":
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                val = row_dict.get(col.key)
                r = p.add_run(str(val if val is not None else "-"))
                r.font.name = "Segoe UI"
                r.font.size = Pt(8)
                if is_total_row:
                    r.font.bold = True
                r.font.color.rgb = RGBColor(15, 23, 42)

        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    if data.sections:
        for sec in data.sections:
            render_docx_table(sec.columns, sec.rows, sec_title=sec.title, sec_subtitle=sec.subtitle)
    else:
        render_docx_table(data.columns, data.rows)

    # 6. SIGNATURES BLOCK
    doc.add_paragraph().paragraph_format.space_after = Pt(18)
    if data.signatures:
        sig_table = doc.add_table(rows=2, cols=len(data.signatures))
        sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for idx, sig in enumerate(data.signatures):
            # Line cell
            c_line = sig_table.cell(0, idx)
            p_l = c_line.paragraphs[0]
            p_l.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_l.paragraph_format.space_after = Pt(0)
            r_l = p_l.add_run("________________________________________")
            r_l.font.name = "Segoe UI"
            r_l.font.size = Pt(8.5)
            r_l.font.bold = True

            # Label cell
            c_lbl = sig_table.cell(1, idx)
            p_b = c_lbl.paragraphs[0]
            p_b.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_b.paragraph_format.space_after = Pt(0)
            r_b = p_b.add_run(sig)
            r_b.font.name = "Segoe UI"
            r_b.font.size = Pt(8.5)
            r_b.font.color.rgb = RGBColor(71, 85, 105)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
