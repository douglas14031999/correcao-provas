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

    school_display = data.metadata.school_name.upper() if data.metadata.school_name else ""
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

    # 3. METADATA GRID (Compact i-Diario style)
    meta_rows = []
    m = data.metadata
    
    row1 = [
        Paragraph(f"<b>Turma:</b> {m.classroom_name or '-'}", style_meta_val),
        Paragraph(f"<b>Turno:</b> {m.shift or '( ) MANHÃ       ( ) TARDE'}", style_meta_val),
        Paragraph(f"<b>Ano Letivo:</b> {m.school_year or datetime.now().year}", style_meta_val),
    ]
    row2 = [
        Paragraph(f"<b>Avaliação:</b> {m.exam_title or 'Geral'}", style_meta_val),
        Paragraph(f"<b>Série/Ano:</b> {m.grade_year or '-'}", style_meta_val),
        Paragraph(f"<b>Total Alunos:</b> {len(data.rows)}", style_meta_val),
    ]
    meta_table = Table([row1, row2], colWidths=[printable_width * 0.4, printable_width * 0.3, printable_width * 0.3])
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
        cards_data = []
        card_cols = len(data.summary_cards)
        w = printable_width / max(1, card_cols)
        row = []
        for card in data.summary_cards:
            lbl = card.get("label", "").upper()
            val = str(card.get("value", ""))
            sub = card.get("subtext", "")
            cell_p = Paragraph(f"<font size=7 color='#64748b'><b>{lbl}</b></font><br/><font size=10 color='#0f172a'><b>{val}</b></font>{f' <font size=6.5 color=#94a3b8>({sub})</font>' if sub else ''}", style_td_center)
            row.append(cell_p)
        cards_table = Table([row], colWidths=[w] * card_cols)
        cards_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor("#ffffff")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(cards_table)
        story.append(Spacer(1, 3 * mm))

    # 5. DATA TABLE
    # Calculate column widths based on ratios
    total_ratio = sum(col.width_ratio for col in data.columns)
    col_widths = [(col.width_ratio / total_ratio) * printable_width for col in data.columns]

    table_data = []
    # Header Row
    header_row = [Paragraph(col.header, style_th) for col in data.columns]
    table_data.append(header_row)

    # Data Rows
    for r_idx, row_dict in enumerate(data.rows):
        row_cells = []
        for col in data.columns:
            val = row_dict.get(col.key, "")
            val_str = str(val if val is not None else "-")
            
            # Format text
            if col.align == "center":
                cell_p = Paragraph(val_str, style_td_center)
            elif col.align == "right":
                cell_p = Paragraph(val_str, ParagraphStyle("Right", parent=style_td, alignment=2))
            else:
                cell_p = Paragraph(val_str, style_td)

            row_cells.append(cell_p)
        table_data.append(row_cells)

    # Table styling
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

    # Alternating row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), HexColor("#f8fafc")))

    main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    main_table.setStyle(TableStyle(t_style))
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
