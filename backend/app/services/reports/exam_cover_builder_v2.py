import os
import math
from typing import Optional, List, Dict
import fitz  # PyMuPDF
from reportlab.lib import pagesizes, colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget

PAGE_WIDTH, PAGE_HEIGHT = pagesizes.A4  # 595.275 x 841.889 pt

def _draw_fiducial_markers(c: canvas.Canvas, top_y: float = 330.0, bot_y: float = 38.0, size: float = 14.5, margin_x: float = 24.0):
    """Standard 4 black square fiducial markers for submillimeter OMR reading."""
    c.saveState()
    c.setFillColor(colors.black)
    c.rect(margin_x, top_y, size, size, stroke=0, fill=1)
    c.rect(PAGE_WIDTH - margin_x - size, top_y, size, size, stroke=0, fill=1)
    c.rect(margin_x, bot_y, size, size, stroke=0, fill=1)
    c.rect(PAGE_WIDTH - margin_x - size, bot_y, size, size, stroke=0, fill=1)
    c.restoreState()

def _draw_answer_grid(
    c: canvas.Canvas,
    top_y: float,
    num_questions: int = 22,
    num_alternatives: int = 4,
    margin_x: float = 24.0,
    marker_size: float = 14.5,
    zebra: bool = False
):
    """Renders 4-column OMR answer grid."""
    num_cols = 4
    rows_per_col = math.ceil(num_questions / num_cols)
    grid_left = margin_x + marker_size + 16.0
    grid_right = PAGE_WIDTH - margin_x - marker_size - 16.0
    total_w = grid_right - grid_left
    col_gap = 14.0
    col_w = (total_w - (num_cols - 1) * col_gap) / num_cols
    options = ["A", "B", "C", "D", "E"][:num_alternatives]

    header_h = 16.0
    row_h = 19.5
    bubble_radius = 4.2
    num_box_w = 15.0
    alt_cell_w = (col_w - num_box_w) / num_alternatives

    for col_idx in range(num_cols):
        cx = grid_left + col_idx * (col_w + col_gap)
        start_q = col_idx * rows_per_col + 1
        end_q = min((col_idx + 1) * rows_per_col, num_questions)
        q_count = max(0, end_q - start_q + 1)
        if q_count == 0:
            continue

        # Column Header (A B C D [E])
        c.saveState()
        c.setFont("Helvetica-Bold", 8.0)
        c.setFillColor(colors.HexColor("#334155"))
        for opt_idx, opt in enumerate(options):
            ox = cx + num_box_w + opt_idx * alt_cell_w + alt_cell_w / 2.0
            c.drawCentredString(ox, top_y - header_h + 4.5, opt)
        c.restoreState()

        # Border
        col_box_y = top_y - header_h - q_count * row_h
        c.saveState()
        c.setStrokeColor(colors.HexColor("#94a3b8"))
        c.setLineWidth(0.7)
        c.setDash([2.5, 2.0])
        c.rect(cx, col_box_y, col_w, q_count * row_h, stroke=1, fill=0)
        c.restoreState()

        # Rows
        for r_idx in range(q_count):
            q_num = start_q + r_idx
            ry = top_y - header_h - (r_idx + 1) * row_h
            bg = colors.HexColor("#f8fafc") if (zebra and r_idx % 2 == 1) else colors.white

            c.saveState()
            if zebra and r_idx % 2 == 1:
                c.setFillColor(bg)
                c.rect(cx + num_box_w, ry, col_w - num_box_w, row_h, stroke=0, fill=1)

            # Item number badge
            c.setFillColor(colors.HexColor("#e2e8f0"))
            c.setStrokeColor(colors.HexColor("#94a3b8"))
            c.setLineWidth(0.5)
            c.rect(cx, ry, num_box_w, row_h, stroke=1, fill=1)

            c.setFillColor(colors.HexColor("#1e293b"))
            c.setFont("Helvetica-Bold", 6.8)
            c.drawCentredString(cx + num_box_w / 2.0, ry + 6.0, f"{q_num:02d}")

            # Bubbles
            c.setStrokeColor(colors.HexColor("#1e293b"))
            c.setLineWidth(0.8)
            for opt_idx in range(num_alternatives):
                bx = cx + num_box_w + opt_idx * alt_cell_w + alt_cell_w / 2.0
                by = ry + row_h / 2.0
                c.setFillColor(colors.white)
                c.circle(bx, by, bubble_radius, stroke=1, fill=1)
            c.restoreState()


# =========================================================================
# DESIGN 1: MODERN TECH / MINIMALISTA CONTEMPORÂNEO (Estilo INEP / ENEM)
# =========================================================================
def render_design_modern_tech(
    output_pdf: str,
    year: str = "2026",
    title: str = "SISTEMA MUNICIPAL DE AVALIAÇÃO",
    subtitle: str = "AVALIAÇÃO DE DESEMPENHO ESCOLAR",
    caderno_code: str = "MAT-0402",
    discipline: str = "MATEMÁTICA",
    grade_stage: str = "4º ano do Ensino Fundamental",
    num_questions: int = 22,
    num_alternatives: int = 4,
    tracking_code: str = "7749102834"
):
    c = canvas.Canvas(output_pdf, pagesize=pagesizes.A4)

    # Dark Indigo / Tech Header Banner
    c.saveState()
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(0, PAGE_HEIGHT - 130, PAGE_WIDTH, 130, stroke=0, fill=1)

    # Accent colored geometric strip
    c.setFillColor(colors.HexColor("#2563eb"))
    c.rect(0, PAGE_HEIGHT - 136, PAGE_WIDTH, 6, stroke=0, fill=1)

    # Year Tag
    c.setFillColor(colors.HexColor("#38bdf8"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(44, PAGE_HEIGHT - 38, f"● CICLO {year}")

    # Main Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(44, PAGE_HEIGHT - 65, title)

    c.setFont("Helvetica", 10.5)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawString(44, PAGE_HEIGHT - 85, subtitle)

    # Caderno Badge in Header (Right Side)
    bw, bh = 140, 56
    bx = PAGE_WIDTH - 44 - bw
    by = PAGE_HEIGHT - 105
    c.setFillColor(colors.HexColor("#1e293b"))
    c.setStrokeColor(colors.HexColor("#38bdf8"))
    c.setLineWidth(1.2)
    c.roundRect(bx, by, bw, bh, 6, stroke=1, fill=1)

    c.setFillColor(colors.HexColor("#94a3b8"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(bx + bw/2.0, by + 36, "CADERNO DE PROVA")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(bx + bw/2.0, by + 12, caderno_code)
    c.restoreState()

    # Student Card (Clean Minimal Card)
    card_x, card_w = 38, PAGE_WIDTH - 76
    card_h = 170
    card_y = PAGE_HEIGHT - 325

    c.saveState()
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(1.0)
    c.roundRect(card_x, card_y, card_w, card_h, 8, stroke=1, fill=1)

    # QR Code
    qr_size = 48
    qr_x, qr_y = card_x + 20, card_y + card_h - qr_size - 16
    qr_widget = QrCodeWidget(f"EXAM:{caderno_code}|{year}")
    qr_widget.barWidth = qr_size
    qr_widget.barHeight = qr_size
    qr_widget.barBorder = 1
    d = Drawing(qr_size, qr_size)
    d.add(qr_widget)
    d.drawOn(c, qr_x, qr_y)

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawCentredString(qr_x + qr_size/2.0, qr_y - 8, caderno_code)

    # Discipline & Grade
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawRightString(card_x + card_w - 20, card_y + card_h - 28, discipline)
    c.setFont("Helvetica", 10.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawRightString(card_x + card_w - 20, card_y + card_h - 45, grade_stage)

    # Name input
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawString(card_x + 20, card_y + 78, "NOME COMPLETO DO(A) ESTUDANTE:")
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.rect(card_x + 20, card_y + 48, card_w - 40, 24, stroke=1, fill=1)

    # Birth Date & Class
    c.setFillColor(colors.HexColor("#334155"))
    c.setFont("Helvetica-Bold", 8.0)
    c.drawString(card_x + 20, card_y + 22, "TURMA: ______________")
    c.drawRightString(card_x + card_w - 180, card_y + 22, "DATA DE NASCIMENTO:")

    # Date boxes
    dx = card_x + card_w - 170
    for i in range(8):
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#94a3b8"))
        c.rect(dx + i*18 + (6 if i in (2,4) else 0), card_y + 12, 16, 18, stroke=1, fill=1)
    c.restoreState()

    # Divider
    c.saveState()
    c.setFillColor(colors.HexColor("#2563eb"))
    c.rect(card_x, card_y - 12, card_w, 3, stroke=0, fill=1)
    c.restoreState()

    # OMR Fiducials & Grid
    marker_top_y = card_y - 32.0
    _draw_fiducial_markers(c, top_y=marker_top_y, bot_y=38.0)
    _draw_answer_grid(c, top_y=marker_top_y - 10.0, num_questions=num_questions, num_alternatives=num_alternatives, zebra=True)

    # Tracking Code
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawRightString(PAGE_WIDTH - 44, 40, tracking_code)

    c.save()
    return output_pdf


# =========================================================================
# DESIGN 2: EDITORIAL / EDUCATIVO COM GUIA DE PREENCHIMENTO (Lemann / Nova Escola)
# =========================================================================
def render_design_editorial_instructions(
    output_pdf: str,
    year: str = "2026",
    title: str = "AVALIAÇÃO DIAGNÓSTICA MUNICIPAL",
    subtitle: str = "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
    caderno_code: str = "LP-0501",
    discipline: str = "LÍNGUA PORTUGUESA",
    grade_stage: str = "5º ano do Ensino Fundamental",
    num_questions: int = 22,
    num_alternatives: int = 4,
    tracking_code: str = "9981245012"
):
    c = canvas.Canvas(output_pdf, pagesize=pagesizes.A4)

    c.saveState()
    c.setFillColor(colors.HexColor("#0f766e"))
    c.rect(0, PAGE_HEIGHT - 120, PAGE_WIDTH, 120, stroke=0, fill=1)

    c.setFillColor(colors.HexColor("#f59e0b"))
    c.rect(0, PAGE_HEIGHT - 125, PAGE_WIDTH, 5, stroke=0, fill=1)

    c.setFillColor(colors.HexColor("#99f6e4"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(44, PAGE_HEIGHT - 36, subtitle.upper())

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(44, PAGE_HEIGHT - 65, title)

    # Year Pill
    c.setFillColor(colors.HexColor("#115e59"))
    c.roundRect(44, PAGE_HEIGHT - 105, 90, 24, 12, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(89, PAGE_HEIGHT - 99, f"ANO {year}")

    # Caderno Badge (Right)
    bw, bh = 145, 54
    bx = PAGE_WIDTH - 44 - bw
    by = PAGE_HEIGHT - 100
    c.setFillColor(colors.white)
    c.roundRect(bx, by, bw, bh, 6, stroke=0, fill=1)

    c.setFillColor(colors.HexColor("#0f766e"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(bx + bw/2.0, by + 36, "CADERNO")
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(bx + bw/2.0, by + 12, caderno_code)
    c.restoreState()

    # Middle Card with Instructions Banner
    card_x, card_w = 38, PAGE_WIDTH - 76
    card_h = 186
    card_y = PAGE_HEIGHT - 330

    c.saveState()
    c.setFillColor(colors.HexColor("#f0fdfa"))
    c.setStrokeColor(colors.HexColor("#99f6e4"))
    c.setLineWidth(1.0)
    c.roundRect(card_x, card_y, card_w, card_h, 8, stroke=1, fill=1)

    # QR Code
    qr_size = 46
    qr_x, qr_y = card_x + 18, card_y + card_h - qr_size - 14
    qr_widget = QrCodeWidget(f"TEST:{caderno_code}")
    qr_widget.barWidth = qr_size
    qr_widget.barHeight = qr_size
    qr_widget.barBorder = 1
    d = Drawing(qr_size, qr_size)
    d.add(qr_widget)
    d.drawOn(c, qr_x, qr_y)

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#115e59"))
    c.drawCentredString(qr_x + qr_size/2.0, qr_y - 8, caderno_code)

    # Discipline & Stage
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#134e4a"))
    c.drawRightString(card_x + card_w - 18, card_y + card_h - 26, discipline.upper())
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#0f766e"))
    c.drawRightString(card_x + card_w - 18, card_y + card_h - 42, grade_stage)

    # Student name
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#134e4a"))
    c.drawString(card_x + 18, card_y + 98, "NOME DO(A) ESTUDANTE:")
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#0d9488"))
    c.rect(card_x + 18, card_y + 70, card_w - 36, 22, stroke=1, fill=1)

    # Visual Instruction Box: Como preencher o gabarito
    instr_y = card_y + 12
    c.setFillColor(colors.HexColor("#ccfbf1"))
    c.roundRect(card_x + 18, instr_y, card_w - 36, 46, 6, stroke=0, fill=1)

    c.setFont("Helvetica-Bold", 7.8)
    c.setFillColor(colors.HexColor("#115e59"))
    c.drawString(card_x + 28, instr_y + 28, "INSTRUÇÕES DE PREENCHIMENTO DO GABARITO:")

    # Mini examples
    # Correct
    c.setFillColor(colors.HexColor("#0f172a"))
    c.circle(card_x + 36, instr_y + 12, 4.5, stroke=1, fill=1)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#134e4a"))
    c.drawString(card_x + 46, instr_y + 9, "Correto (preenchimento total)")

    # Wrong 1 (X)
    c.setFillColor(colors.white)
    c.circle(card_x + 185, instr_y + 12, 4.5, stroke=1, fill=1)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#dc2626"))
    c.drawCentredString(card_x + 185, instr_y + 9, "✕")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#134e4a"))
    c.drawString(card_x + 195, instr_y + 9, "Incorreto (não use X)")

    # Wrong 2 (half)
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#134e4a"))
    c.circle(card_x + 310, instr_y + 12, 4.5, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#134e4a"))
    c.circle(card_x + 310, instr_y + 12, 2.0, stroke=0, fill=1)
    c.setFont("Helvetica", 7.5)
    c.drawString(card_x + 320, instr_y + 9, "Incorreto (não rasure)")
    c.restoreState()

    # OMR Fiducials & Grid
    marker_top_y = card_y - 28.0
    _draw_fiducial_markers(c, top_y=marker_top_y, bot_y=38.0)
    _draw_answer_grid(c, top_y=marker_top_y - 10.0, num_questions=num_questions, num_alternatives=num_alternatives)

    # Tracking Code
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawRightString(PAGE_WIDTH - 44, 40, tracking_code)

    c.save()
    return output_pdf


# =========================================================================
# DESIGN 3: INSTITUCIONAL / FORMAL GOVERNO (Estilo Prova Brasil / Clássico)
# =========================================================================
def render_design_formal_gov(
    output_pdf: str,
    year: str = "2026",
    title: str = "SISTEMA DE AVALIAÇÃO DA EDUCAÇÃO BÁSICA",
    subtitle: str = "SECRETARIA MUNICIPAL DE EDUCAÇÃO E CULTURA",
    caderno_code: str = "M0402",
    discipline: str = "MATEMÁTICA",
    grade_stage: str = "4º ANO DO ENSINO FUNDAMENTAL",
    num_questions: int = 22,
    num_alternatives: int = 4,
    tracking_code: str = "6638192047"
):
    c = canvas.Canvas(output_pdf, pagesize=pagesizes.A4)

    # Formal Double Outer Border around the page
    c.saveState()
    c.setStrokeColor(colors.HexColor("#0f172a"))
    c.setLineWidth(1.5)
    c.rect(20, 20, PAGE_WIDTH - 40, PAGE_HEIGHT - 40, stroke=1, fill=0)
    c.setLineWidth(0.6)
    c.rect(23, 23, PAGE_WIDTH - 46, PAGE_HEIGHT - 46, stroke=1, fill=0)
    c.restoreState()

    # Formal Centered Header
    c.saveState()
    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 48, subtitle.upper())

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 70, title.upper())

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 88, f"AVALIAÇÃO CENSITÁRIA – ANO LETIVO {year}")

    c.setStrokeColor(colors.HexColor("#0f172a"))
    c.setLineWidth(1.0)
    c.line(40, PAGE_HEIGHT - 98, PAGE_WIDTH - 40, PAGE_HEIGHT - 98)
    c.restoreState()

    # Caderno & Discipline Bar
    bar_y = PAGE_HEIGHT - 132
    c.saveState()
    c.setFillColor(colors.HexColor("#1e293b"))
    c.rect(40, bar_y, PAGE_WIDTH - 80, 26, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(52, bar_y + 8, f"COMPONENTE: {discipline.upper()} – {grade_stage.upper()}")
    c.drawRightString(PAGE_WIDTH - 52, bar_y + 8, f"CADERNO: {caderno_code}")
    c.restoreState()

    # Formal Tabular Student Identification
    tbl_x, tbl_w = 40, PAGE_WIDTH - 80
    tbl_y = bar_y - 126
    tbl_h = 118

    c.saveState()
    c.setStrokeColor(colors.HexColor("#334155"))
    c.setLineWidth(0.8)
    c.rect(tbl_x, tbl_y, tbl_w, tbl_h, stroke=1, fill=0)

    # Line 1: Escola
    c.line(tbl_x, tbl_y + 82, tbl_x + tbl_w, tbl_y + 82)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(tbl_x + 8, tbl_y + 104, "NOME DA ESCOLA:")

    # Line 2: Nome do Estudante
    c.line(tbl_x, tbl_y + 46, tbl_x + tbl_w, tbl_y + 46)
    c.drawString(tbl_x + 8, tbl_y + 68, "NOME DO(A) ESTUDANTE:")

    # Line 3: Turma, Turno e Data
    c.drawString(tbl_x + 8, tbl_y + 30, "TURMA:")
    c.line(tbl_x + 130, tbl_y, tbl_x + 130, tbl_y + 46)
    c.drawString(tbl_x + 138, tbl_y + 30, "TURNO: ( ) MANHÃ   ( ) TARDE")
    c.line(tbl_x + 340, tbl_y, tbl_x + 340, tbl_y + 46)
    c.drawString(tbl_x + 348, tbl_y + 30, "DATA DE NASCIMENTO:")

    dx = tbl_x + 348
    for i in range(8):
        c.rect(dx + i*16 + (4 if i in (2,4) else 0), tbl_y + 8, 14, 16, stroke=1, fill=0)

    # QR Code
    qr_size = 42
    qr_x, qr_y = tbl_x + tbl_w - qr_size - 6, tbl_y + 70
    qr_widget = QrCodeWidget(f"BR:{caderno_code}")
    qr_widget.barWidth = qr_size
    qr_widget.barHeight = qr_size
    qr_widget.barBorder = 1
    d = Drawing(qr_size, qr_size)
    d.add(qr_widget)
    d.drawOn(c, qr_x, qr_y)
    c.restoreState()

    # Instruction Note
    c.saveState()
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawCentredString(PAGE_WIDTH / 2.0, tbl_y - 14, "FOLHA DE RESPOSTAS OFICIAL – PREENCHA COMPLETAMENTE AS BOLHAS COM CANETA AZUL OU PRETA")
    c.restoreState()

    # OMR Fiducials & Grid
    marker_top_y = tbl_y - 36.0
    _draw_fiducial_markers(c, top_y=marker_top_y, bot_y=42.0)
    _draw_answer_grid(c, top_y=marker_top_y - 10.0, num_questions=num_questions, num_alternatives=num_alternatives)

    # Tracking Code
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawRightString(PAGE_WIDTH - 44, 44, tracking_code)

    c.save()
    return output_pdf


# =========================================================================
# DESIGN 4: ONDA DINÂMICA / CONTEMPORÂNEO (Estilo CAEd Waves & Gradients)
# =========================================================================
def render_design_dynamic_wave(
    output_pdf: str,
    year: str = "2026",
    title: str = "AVALIAÇÃO DE APRENDIZAGEM EM FOCO",
    subtitle: str = "CICLO DE DIAGNÓSTICO E MONITORAMENTO",
    caderno_code: str = "SIM-0901",
    discipline: str = "CIÊNCIAS DA NATUREZA",
    grade_stage: str = "9º ano do Ensino Fundamental",
    num_questions: int = 26,
    num_alternatives: int = 5,
    tracking_code: str = "8819203948"
):
    c = canvas.Canvas(output_pdf, pagesize=pagesizes.A4)

    # Dynamic Asymmetrical Wave Header
    c.saveState()
    c.setFillColor(colors.HexColor("#1e1b4b"))
    p1 = c.beginPath()
    p1.moveTo(0, PAGE_HEIGHT)
    p1.lineTo(PAGE_WIDTH, PAGE_HEIGHT)
    p1.lineTo(PAGE_WIDTH, PAGE_HEIGHT - 110)
    p1.curveTo(PAGE_WIDTH * 0.6, PAGE_HEIGHT - 145, PAGE_WIDTH * 0.3, PAGE_HEIGHT - 85, 0, PAGE_HEIGHT - 130)
    p1.close()
    c.drawPath(p1, stroke=0, fill=1)

    c.setFillColor(colors.HexColor("#3b82f6"))
    p2 = c.beginPath()
    p2.moveTo(0, PAGE_HEIGHT - 130)
    p2.curveTo(PAGE_WIDTH * 0.3, PAGE_HEIGHT - 85, PAGE_WIDTH * 0.6, PAGE_HEIGHT - 145, PAGE_WIDTH, PAGE_HEIGHT - 110)
    p2.lineTo(PAGE_WIDTH, PAGE_HEIGHT - 116)
    p2.curveTo(PAGE_WIDTH * 0.6, PAGE_HEIGHT - 151, PAGE_WIDTH * 0.3, PAGE_HEIGHT - 91, 0, PAGE_HEIGHT - 136)
    p2.close()
    c.drawPath(p2, stroke=0, fill=1)

    # Year Floating Badge
    c.setFillColor(colors.white)
    c.roundRect(40, PAGE_HEIGHT - 45, 66, 22, 11, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#1e1b4b"))
    c.setFont("Helvetica-Bold", 10.5)
    c.drawCentredString(73, PAGE_HEIGHT - 39, year)

    # Main Title (Carefully bounded)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 15.5)
    c.drawString(40, PAGE_HEIGHT - 75, "AVALIAÇÃO DE APRENDIZAGEM EM FOCO")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#93c5fd"))
    c.drawString(40, PAGE_HEIGHT - 92, subtitle)

    # Caderno Badge
    bw, bh = 145, 54
    bx = PAGE_WIDTH - 40 - bw
    by = PAGE_HEIGHT - 105
    c.setFillColor(colors.HexColor("#312e81"))
    c.roundRect(bx, by, bw, bh, 6, stroke=0, fill=1)
    c.setStrokeColor(colors.HexColor("#60a5fa"))
    c.setLineWidth(1.2)
    c.roundRect(bx, by, bw, bh, 6, stroke=1, fill=0)

    c.setFillColor(colors.HexColor("#93c5fd"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(bx + bw/2.0, by + 35, "CADERNO OFICIAL")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(bx + bw/2.0, by + 12, caderno_code)
    c.restoreState()

    # Middle Card
    card_x, card_w = 38, PAGE_WIDTH - 76
    card_h = 168
    card_y = PAGE_HEIGHT - 325

    c.saveState()
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#e0e7ff"))
    c.setLineWidth(1.0)
    c.roundRect(card_x, card_y, card_w, card_h, 8, stroke=1, fill=1)

    # QR Code
    qr_size = 46
    qr_x, qr_y = card_x + 20, card_y + card_h - qr_size - 16
    qr_widget = QrCodeWidget(f"WAVE:{caderno_code}")
    qr_widget.barWidth = qr_size
    qr_widget.barHeight = qr_size
    qr_widget.barBorder = 1
    d = Drawing(qr_size, qr_size)
    d.add(qr_widget)
    d.drawOn(c, qr_x, qr_y)

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#312e81"))
    c.drawCentredString(qr_x + qr_size/2.0, qr_y - 8, caderno_code)

    # Discipline & Stage
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1e1b4b"))
    c.drawRightString(card_x + card_w - 20, card_y + card_h - 28, discipline.upper())
    c.setFont("Helvetica", 10.5)
    c.setFillColor(colors.HexColor("#4338ca"))
    c.drawRightString(card_x + card_w - 20, card_y + card_h - 45, grade_stage)

    # Name input box
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#1e1b4b"))
    c.drawString(card_x + 20, card_y + 78, "NOME COMPLETO DO(A) ESTUDANTE:")
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#a5b4fc"))
    c.rect(card_x + 20, card_y + 48, card_w - 40, 24, stroke=1, fill=1)

    # Birth Date & Class
    c.setFillColor(colors.HexColor("#312e81"))
    c.setFont("Helvetica-Bold", 8.0)
    c.drawString(card_x + 20, card_y + 22, "TURMA / ANO: ______________")
    c.drawRightString(card_x + card_w - 180, card_y + 22, "DATA DE NASCIMENTO:")

    dx = card_x + card_w - 170
    for i in range(8):
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#a5b4fc"))
        c.rect(dx + i*18 + (6 if i in (2,4) else 0), card_y + 12, 16, 18, stroke=1, fill=1)
    c.restoreState()

    # OMR Fiducials & Grid (26 Questions, 5 Alternatives A-E)
    marker_top_y = card_y - 28.0
    _draw_fiducial_markers(c, top_y=marker_top_y, bot_y=38.0)
    _draw_answer_grid(c, top_y=marker_top_y - 10.0, num_questions=num_questions, num_alternatives=num_alternatives, zebra=True)

    # Tracking Code
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawRightString(PAGE_WIDTH - 44, 40, tracking_code)

    c.save()
    return output_pdf
