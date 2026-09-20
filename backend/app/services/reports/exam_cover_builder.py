import os
import math
from typing import Optional, List, Dict, Tuple
from PIL import Image
import fitz  # PyMuPDF
from reportlab.lib import pagesizes, colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget

# Standard A4: 595.275 x 841.889 pt
PAGE_WIDTH, PAGE_HEIGHT = pagesizes.A4

def _draw_modern_header(c: canvas.Canvas, accent_color: str = "#1e3a8a"):
    """Draws sleek modern corporate header area matching Prefeitura de Lagoa da Canoa design."""
    c.saveState()
    # Soft background for the top header banner
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.rect(0, PAGE_HEIGHT - 230, PAGE_WIDTH, 230, stroke=0, fill=1)

    # Accent top border (4pt)
    c.setFillColor(colors.HexColor(accent_color))
    c.rect(0, PAGE_HEIGHT - 6, PAGE_WIDTH, 6, stroke=0, fill=1)

    # Subtle modern wave line in the header background
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.setLineWidth(1.2)
    path = c.beginPath()
    path.moveTo(0, PAGE_HEIGHT - 220)
    path.curveTo(PAGE_WIDTH * 0.35, PAGE_HEIGHT - 200, PAGE_WIDTH * 0.65, PAGE_HEIGHT - 240, PAGE_WIDTH, PAGE_HEIGHT - 215)
    c.drawPath(path, stroke=1, fill=0)

    c.restoreState()

def generate_exam_cover(
    output_pdf_path: str,
    year: str = "2026",
    main_title_lines: Optional[List[str]] = None,
    header_subtitle: str = "PREFEITURA DE LAGOA DA CANOA • SEMED",
    caderno_code: str = "M0402",
    discipline: str = "MATEMÁTICA",
    grade_stage: str = "4º ano do Ensino Fundamental",
    qr_code_text: Optional[str] = None,
    num_questions: int = 22,
    num_alternatives: int = 4,  # 4 for A-D, 5 for A-E
    student_name: str = "",
    student_birth_date: str = "",  # format "DDMMAAAA" or "DD/MM/AAAA"
    tracking_code: str = "4454197329",
    caderno_accent_color: str = "#1e3a8a",
    school_name: str = "",
    classroom_name: str = "",
    shift: str = "MATUTINO"
) -> str:
    """
    Generates a high-precision assessment cover + OMR answer sheet conforming to the
    official Prefeitura de Lagoa da Canoa 2026 template layout.
    """
    if main_title_lines is None:
        main_title_lines = [
            "PROVA CANOA"
        ]

    if qr_code_text is None:
        qr_code_text = f"2268{caderno_code}"

    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
    c = canvas.Canvas(output_pdf_path, pagesize=pagesizes.A4)

    # 1. Sleek Modern Header
    _draw_modern_header(c, accent_color=caderno_accent_color)

    # 2. Year Pill Badge (Top Left)
    pill_x, pill_y, pill_w, pill_h = 44, PAGE_HEIGHT - 54, 70, 22
    c.saveState()
    c.setFillColor(colors.HexColor(caderno_accent_color))
    c.roundRect(pill_x, pill_y, pill_w, pill_h, 11, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(pill_x + pill_w / 2.0, pill_y + 6.0, str(year))
    c.restoreState()

    # 3. Main Title (Left Column)
    title_start_y = pill_y - 28
    line_height = 24
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#0f172a"))
    for idx, line in enumerate(main_title_lines):
        c.drawString(pill_x, title_start_y - idx * line_height, line)

    # 4. Top-Right Header Subtitle
    c.saveState()
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#1e293b"))
    if " - " in header_subtitle:
        sub_p1, sub_p2 = header_subtitle.split(" - ", 1)
        c.drawRightString(PAGE_WIDTH - 44, PAGE_HEIGHT - 40, sub_p1.upper())
        c.drawRightString(PAGE_WIDTH - 44, PAGE_HEIGHT - 51, f"- {sub_p2.upper()}")
    else:
        c.drawRightString(PAGE_WIDTH - 44, PAGE_HEIGHT - 45, header_subtitle.upper())
    c.restoreState()

    # 5. Right Badge "CADERNO"
    badge_w, badge_h = 168, 58
    badge_x = PAGE_WIDTH - 44 - badge_w
    badge_y = PAGE_HEIGHT - 172

    c.saveState()
    # Top Section of Badge: "CADERNO"
    top_bar_h = 24
    c.setFillColor(colors.HexColor(caderno_accent_color))
    c.setStrokeColor(colors.HexColor(caderno_accent_color))
    c.roundRect(badge_x, badge_y + badge_h - top_bar_h, badge_w, top_bar_h, 4, stroke=1, fill=1)
    c.rect(badge_x, badge_y + badge_h - top_bar_h, badge_w, 4, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(badge_x + badge_w / 2.0, badge_y + badge_h - top_bar_h + 6.5, "C  A  D  E  R  N  O")

    # Bottom Section of Badge: Caderno Code (e.g. M0402)
    bot_bar_h = badge_h - top_bar_h
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setStrokeColor(colors.HexColor("#0f172a"))
    c.roundRect(badge_x, badge_y, badge_w, bot_bar_h, 4, stroke=1, fill=1)
    c.rect(badge_x, badge_y + bot_bar_h - 4, badge_w, 4, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 19)
    spaced_code = "  ".join(list(caderno_code.strip()))
    c.drawCentredString(badge_x + badge_w / 2.0, badge_y + 9.0, spaced_code)
    c.restoreState()

    # 6. Middle Card: Student Information & Discipline
    card_x = 38
    card_w = PAGE_WIDTH - 76  # 519.275 pt
    card_h = 176
    card_y = badge_y - card_h - 18

    c.saveState()
    # Light gray rounded background
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(1.0)
    c.roundRect(card_x, card_y, card_w, card_h, 8, stroke=1, fill=1)

    # 6.1 Card Header Bar
    bar_h = 24
    c.setFillColor(colors.HexColor(caderno_accent_color))
    c.roundRect(card_x, card_y + card_h - bar_h, card_w, bar_h, 8, stroke=0, fill=1)
    c.rect(card_x, card_y + card_h - bar_h, card_w, 8, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(card_x + 16, card_y + card_h - 16, f"DADOS DO(A) ESTUDANTE • {discipline.upper()}")
    if grade_stage:
        c.drawRightString(card_x + card_w - 16, card_y + card_h - 16, str(grade_stage).upper())

    # 6.2 QR Code inside card (left)
    qr_size = 60
    qr_x = card_x + 16
    qr_y = card_y + (card_h - bar_h - qr_size) / 2.0 + 4

    qr_widget = QrCodeWidget(qr_code_text)
    qr_widget.barWidth = qr_size
    qr_widget.barHeight = qr_size
    qr_widget.barBorder = 1
    d = Drawing(qr_size, qr_size)
    d.add(qr_widget)
    d.drawOn(c, qr_x, qr_y)

    # Text under QR code
    c.setFont("Helvetica", 7.0)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(qr_x + qr_size / 2.0, qr_y - 9.0, qr_code_text)

    # 6.3 Student Fields Table (right of QR code)
    field_x = qr_x + qr_size + 18
    field_w = card_w - (field_x - card_x) - 16
    start_field_y = card_y + card_h - bar_h - 22

    # Field 1: Unidade Escolar
    effective_school = school_name or "SECRETARIA MUNICIPAL DE EDUCAÇÃO - SEMED"
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(field_x, start_field_y, "UNIDADE ESCOLAR:")
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(field_x + 95, start_field_y, effective_school[:48].upper())
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.setLineWidth(0.6)
    c.line(field_x, start_field_y - 4, field_x + field_w, start_field_y - 4)

    # Field 2: Nome Completo do(a) Estudante
    effective_student = student_name or "ESTUDANTE"
    start_field_y -= 26
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(field_x, start_field_y, "NOME DO(A) ESTUDANTE:")
    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(field_x + 120, start_field_y, effective_student[:42].upper())
    c.line(field_x, start_field_y - 4, field_x + field_w, start_field_y - 4)

    # Field 3: Turma e Turno
    start_field_y -= 26
    effective_class = classroom_name or grade_stage
    effective_shift = shift or "MATUTINO"

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(field_x, start_field_y, "TURMA:")
    c.setFont("Helvetica-Bold", 9.0)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(field_x + 45, start_field_y, str(effective_class).upper())

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(field_x + field_w * 0.55, start_field_y, "TURNO:")
    c.setFont("Helvetica-Bold", 9.0)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(field_x + field_w * 0.55 + 45, start_field_y, str(effective_shift).upper())
    c.line(field_x, start_field_y - 4, field_x + field_w, start_field_y - 4)

    c.restoreState()

    # 7. Dark Gray Divider Bar below card
    div_y = card_y - 15
    c.saveState()
    c.setFillColor(colors.HexColor("#64748b"))
    c.rect(card_x + 24, div_y, card_w - 48, 5.0, stroke=0, fill=1)
    c.restoreState()

    # 8. Corner OMR Fiducial Markers (Solid Black Squares)
    marker_size = 14.5
    margin_x = 24.0
    marker_top_y = div_y - 32.0
    marker_bottom_y = 38.0

    c.saveState()
    c.setFillColor(colors.black)
    # Top-Left Marker
    c.rect(margin_x, marker_top_y, marker_size, marker_size, stroke=0, fill=1)
    # Top-Right Marker
    c.rect(PAGE_WIDTH - margin_x - marker_size, marker_top_y, marker_size, marker_size, stroke=0, fill=1)
    # Bottom-Left Marker
    c.rect(margin_x, marker_bottom_y, marker_size, marker_size, stroke=0, fill=1)
    # Bottom-Right Marker
    c.rect(PAGE_WIDTH - margin_x - marker_size, marker_bottom_y, marker_size, marker_size, stroke=0, fill=1)
    c.restoreState()

    # 9. OMR Answer Sheet Grid (Cartão-Resposta)
    num_cols = 4
    rows_per_col = math.ceil(num_questions / num_cols)

    grid_left = margin_x + marker_size + 16.0
    grid_right = PAGE_WIDTH - margin_x - marker_size - 16.0
    total_grid_w = grid_right - grid_left
    col_gap = 14.0
    col_w = (total_grid_w - (num_cols - 1) * col_gap) / num_cols

    options = ["A", "B", "C", "D", "E"][:num_alternatives]

    grid_top_y = marker_top_y - 10.0
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

        # Column Header: Letters (A B C D [E])
        c.saveState()
        c.setFont("Helvetica-Bold", 8.0)
        c.setFillColor(colors.HexColor("#334155"))
        for opt_idx, opt in enumerate(options):
            opt_center_x = cx + num_box_w + opt_idx * alt_cell_w + alt_cell_w / 2.0
            c.drawCentredString(opt_center_x, grid_top_y - header_h + 4.5, opt)
        c.restoreState()

        # Dashed border enclosing this column's question rows
        col_box_y = grid_top_y - header_h - q_count * row_h
        col_box_h = q_count * row_h
        c.saveState()
        c.setStrokeColor(colors.HexColor("#94a3b8"))
        c.setLineWidth(0.7)
        c.setDash([2.5, 2.0])
        c.rect(cx, col_box_y, col_w, col_box_h, stroke=1, fill=0)
        c.restoreState()

        # Render Question Rows
        for r_idx in range(q_count):
            q_num = start_q + r_idx
            ry = grid_top_y - header_h - (r_idx + 1) * row_h

            c.saveState()
            # Left item number cell (filled gray)
            c.setFillColor(colors.HexColor("#e2e8f0"))
            c.setStrokeColor(colors.HexColor("#94a3b8"))
            c.setLineWidth(0.5)
            c.rect(cx, ry, num_box_w, row_h, stroke=1, fill=1)

            c.setFillColor(colors.HexColor("#1e293b"))
            c.setFont("Helvetica-Bold", 6.8)
            c.drawCentredString(cx + num_box_w / 2.0, ry + 6.0, f"{q_num:02d}")

            # Option Bubbles
            c.setStrokeColor(colors.HexColor("#1e293b"))
            c.setLineWidth(0.8)
            for opt_idx, opt in enumerate(options):
                bubble_x = cx + num_box_w + opt_idx * alt_cell_w + alt_cell_w / 2.0
                bubble_y = ry + row_h / 2.0
                c.setFillColor(colors.white)
                c.circle(bubble_x, bubble_y, bubble_radius, stroke=1, fill=1)

            c.restoreState()

    # 10. Bottom Tracking Code / Barcode Number
    c.saveState()
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawRightString(grid_right, marker_bottom_y + 3.0, tracking_code)
    c.restoreState()

    c.save()
    return output_pdf_path

def render_pdf_to_image(pdf_path: str, output_image_path: str, dpi: int = 150) -> str:
    """Converts the first page of a PDF to a high-resolution PNG image."""
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
    pix.save(output_image_path)
    doc.close()
    return output_image_path
