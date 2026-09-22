import os
import io
from datetime import datetime
from typing import Optional
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

from .base_report import ReportData

class NumberedCanvas(canvas.Canvas):
    """Canvas with two-pass evaluation to render 'Página X de Y' and footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(HexColor("#64748b"))

        # Footer divider line
        self.setStrokeColor(HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(10 * mm, 12 * mm, self._pagesize[0] - 10 * mm, 12 * mm)

        # Left: System identification
        self.drawString(10 * mm, 8 * mm, "Sistema Municipal de Gestão e Correção de Avaliações (OMR)")

        # Right: Page X of Y
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(self._pagesize[0] - 10 * mm, 8 * mm, page_text)
        self.restoreState()


def build_pdf_report(data: ReportData, orientation: str = "portrait") -> bytes:
    """Builds an official A4 institutional PDF report conforming to municipal standards."""
    buffer = io.BytesIO()
    
    page_size = landscape(A4) if orientation == "landscape" else A4
    page_width, page_height = page_size
    margin = 10 * mm
    printable_width = page_width - (2 * margin)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=16 * mm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_entity = ParagraphStyle(
        "ReportEntity",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=HexColor("#0f172a"),
        alignment=0 # Left aligned beside logo
    )
    style_subentity = ParagraphStyle(
        "ReportSubEntity",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=HexColor("#334155"),
        alignment=0
    )
    style_title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=white,
        alignment=1 # Center
    )
    style_meta_label = ParagraphStyle(
        "ReportMetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=HexColor("#334155")
    )
    style_meta_val = ParagraphStyle(
        "ReportMetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=HexColor("#0f172a")
    )
    style_th = ParagraphStyle(
        "ReportTH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=white,
        alignment=1 # Center
    )
    style_td = ParagraphStyle(
        "ReportTD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=HexColor("#0f172a")
    )
    style_td_center = ParagraphStyle(
        "ReportTDCenter",
        parent=style_td,
        alignment=1
    )
    style_td_bold = ParagraphStyle(
        "ReportTDBold",
        parent=style_td,
        fontName="Helvetica-Bold",
        alignment=1
    )

    story = []

    # 1. INSTITUTIONAL HEADER TABLE (Coat of arms on left + Left-aligned entity hierarchy)
    logo_flowable = Paragraph("", style_subentity)
    if data.metadata.logo_path and os.path.exists(data.metadata.logo_path):
        try:
            logo_flowable = Image(data.metadata.logo_path, width=48, height=48)
        except Exception:
            logo_flowable = Paragraph("", style_subentity)

    school_display = data.metadata.school_name.upper() if data.metadata.school_name else "REDE MUNICIPAL DE ENSINO"
    if data.metadata.inep_code:
        school_display += f" — INEP: {data.metadata.inep_code}"

    header_text = f"""
    <font fontName="Helvetica-Bold" size=11 color="#0f172a"><b>{data.metadata.prefeitura.upper()}</b></font><br/>
    <font fontName="Helvetica" size=9.5 color="#334155">{data.metadata.secretaria.upper()}</font><br/>
    <font fontName="Helvetica-Bold" size=9.5 color="#0f172a"><b>{school_display}</b></font>
    """
    header_para = Paragraph(header_text, style_entity)

    header_table_data = [
        [logo_flowable, header_para]
    ]
    header_table = Table(header_table_data, colWidths=[54, printable_width - 54])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 2 * mm))

    # 2. DOCUMENT TITLE BANNER (Sober Navy / Slate Strip)
    title_data = [[Paragraph(data.title.upper(), style_title)]]
    title_table = Table(title_data, colWidths=[printable_width])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor("#1e293b")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 2 * mm))

    # 3. METADATA GRID (Dynamic: only fields with real data)
    m = data.metadata
    meta_items = []
    
    if m.classroom_name and m.classroom_name.strip() not in ("", "-", "None"):
        meta_items.append(("Turma", m.classroom_name.strip()))
    
    if m.grade_year and m.grade_year.strip() not in ("", "-", "None", "Todos os Anos"):
        meta_items.append(("Série/Ano", m.grade_year.strip()))
        
    if m.shift and m.shift.strip() not in ("", "-", "None") and "( )" not in m.shift:
        meta_items.append(("Turno", m.shift.strip()))
    elif m.shift and m.shift.strip() not in ("", "-", "None") and m.classroom_name and m.classroom_name.strip() not in ("", "-", "None"):
        meta_items.append(("Turno", m.shift.strip()))
        
    if m.exam_title and m.exam_title.strip() not in ("", "-", "None"):
        meta_items.append(("Avaliação", m.exam_title.strip()))
        
    ano_val = m.school_year or str(datetime.now().year)
    meta_items.append(("Ano Letivo", ano_val))

    if meta_items:
        items_per_row = 2 if len(meta_items) == 2 else min(3, len(meta_items))
        chunks = [meta_items[i:i + items_per_row] for i in range(0, len(meta_items), items_per_row)]
        meta_table_rows = []
        for chunk in chunks:
            row_paras = [Paragraph(f"<b>{lbl}:</b> {val}", style_meta_val) for lbl, val in chunk]
            while len(row_paras) < items_per_row:
                row_paras.append(Paragraph("", style_meta_val))
            meta_table_rows.append(row_paras)
            
        col_w = printable_width / items_per_row
        meta_table = Table(meta_table_rows, colWidths=[col_w] * items_per_row)
        meta_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor("#f1f5f9")),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#f8fafc")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 3 * mm))

    # 4. SUMMARY STATS CHIPS (If provided)
    if data.summary_cards:
        cards_per_row = 4 if len(data.summary_cards) > 4 else len(data.summary_cards)
        chunks = [data.summary_cards[i:i + cards_per_row] for i in range(0, len(data.summary_cards), cards_per_row)]
        cards_table_rows = []
        col_w = printable_width / cards_per_row
        for chunk in chunks:
            row = []
            for card in chunk:
                lbl = card.get("label", "").upper()
                val = str(card.get("value", ""))
                sub = card.get("subtext", "")
                cell_p = Paragraph(f"<font size=7 color='#64748b'><b>{lbl}</b></font><br/><font size=10 color='#0f172a'><b>{val}</b></font>{f' <font size=6.5 color=#94a3b8>({sub})</font>' if sub else ''}", style_td_center)
                row.append(cell_p)
            while len(row) < cards_per_row:
                row.append(Paragraph("", style_td_center))
            cards_table_rows.append(row)
        cards_table = Table(cards_table_rows, colWidths=[col_w] * cards_per_row)
        cards_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#ffffff")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(cards_table)
        story.append(Spacer(1, 3 * mm))

    # 5. DATA TABLES (Supports single table or multiple sections)
    def render_table_flowable(cols, rows):
        total_ratio = sum(col.width_ratio for col in cols)
        col_widths = [(col.width_ratio / total_ratio) * printable_width for col in cols]

        table_data = []
        header_row = [Paragraph(col.header, style_th) for col in cols]
        table_data.append(header_row)

        total_row_indices = []
        for r_idx, row_dict in enumerate(rows, start=1):
            is_total = any(isinstance(v, str) and ("TOTAL" in v.upper() or "SUBTOTAL" in v.upper()) for v in row_dict.values() if v)
            if is_total:
                total_row_indices.append(r_idx)

            row_cells = []
            for col in cols:
                val = row_dict.get(col.key, "")
                val_str = str(val if val is not None else "-")
                
                if is_total:
                    val_str = f"<b>{val_str}</b>"

                if col.align == "center":
                    cell_p = Paragraph(val_str, style_td_center)
                elif col.align == "right":
                    cell_p = Paragraph(val_str, ParagraphStyle("Right", parent=style_td, alignment=2))
                else:
                    cell_p = Paragraph(val_str, style_td)

                row_cells.append(cell_p)
            table_data.append(row_cells)

        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#334155")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 4),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ]

        for i in range(1, len(table_data)):
            if i in total_row_indices:
                t_style.append(('BACKGROUND', (0, i), (-1, i), HexColor("#e2e8f0")))
                t_style.append(('LINEABOVE', (0, i), (-1, i), 1.0, HexColor("#94a3b8")))
                t_style.append(('LINEBELOW', (0, i), (-1, i), 1.0, HexColor("#94a3b8")))
            elif i % 2 == 0:
                t_style.append(('BACKGROUND', (0, i), (-1, i), HexColor("#f8fafc")))

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle(t_style))
        return tbl

    if data.sections:
        for s_idx, sec in enumerate(data.sections):
            sec_heading = f"<b>{sec.title}</b>"
            if sec.subtitle:
                sec_heading += f"<br/><font size=6.5 color='#64748b'>{sec.subtitle}</font>"
            sec_p = Paragraph(sec_heading, ParagraphStyle(
                "SecHeader",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8.5,
                leading=11,
                textColor=HexColor("#1e293b")
            ))
            sec_table = Table([[sec_p]], colWidths=[printable_width])
            sec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor("#f1f5f9")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
            ]))
            story.append(sec_table)
            story.append(Spacer(1, 1.5 * mm))

            t_flow = render_table_flowable(sec.columns, sec.rows)
            story.append(t_flow)
            story.append(Spacer(1, 4 * mm))
    else:
        main_table = render_table_flowable(data.columns, data.rows)
        story.append(main_table)
        story.append(Spacer(1, 6 * mm))

    # 6. SIGNATURES BLOCK (Kept together at document end)
    if data.signatures:
        sig_cols = len(data.signatures)
        sig_width = printable_width / sig_cols
        sig_data = []
        
        line_row = [Paragraph("____________________________________________", style_td_center) for _ in data.signatures]
        label_row = [Paragraph(f"<b>{sig}</b>", style_td_center) for sig in data.signatures]
        sig_table = Table([line_row, label_row], colWidths=[sig_width] * sig_cols)
        sig_table.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(KeepTogether([Spacer(1, 4 * mm), sig_table]))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
