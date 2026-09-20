import os
import sys
import io
import json
import math
import numpy as np
import cv2
from PIL import Image

import fitz
from reportlab.lib import pagesizes, colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from app.services.database import get_exam, update_exam_template, get_student_by_id

PAGE_WIDTH, PAGE_HEIGHT = pagesizes.A4  # 595.275 x 841.889 pt
CANONICAL_WIDTH = 1654
CANONICAL_HEIGHT_HALF = 1169

def generate_aruco_marker_image(marker_id: int, size: int = 140) -> Image.Image:
    try:
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        marker_img = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
    except AttributeError:
        dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        marker_img = cv2.aruco.drawMarker(dictionary, marker_id, size)
    return Image.fromarray(marker_img)

def render_cover_and_template(
    output_pdf_path: str,
    school_name: str,
    student_name: str,
    student_reg: str,
    student_id: str,
    classroom_name: str,
    shift: str,
    exam_id: str,
    exam_title: str,
    exam_subtitle: str,
    num_questions: int = 22,
    num_alternatives: int = 4,
    filled_answers: dict = None
) -> tuple[str, dict]:
    """
    Renders the official Prova Canoa 2026 exam cover with ReportLab:
    - Top half: 2026, PROVA CANOA, Discipline, Stage, and full-width Student Card.
    - Bottom half: Reading Area strictly bounded by 4 ArUco markers, instructions banner,
      canonical 2-column question grid, and QR code at bottom-right.
    - Returns output PDF path and the exact mathematical template for OMR engine.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=pagesizes.A4)

    # =========================================================================
    # 1. TOP HALF: INSTITUTIONAL HEADER & STUDENT CARD (Outside OMR scan zone)
    # =========================================================================
    top_section_h = PAGE_HEIGHT / 2.0  # 420.94 pt
    top_y0 = PAGE_HEIGHT / 2.0

    # Decorative header background (Azul Náutico / Lagoa palette)
    c.saveState()
    c.setFillColor(colors.HexColor("#0f2744"))  # Deep nautical navy
    c.rect(0, PAGE_HEIGHT - 130, PAGE_WIDTH, 130, stroke=0, fill=1)

    # Accent decorative gradient / wave band
    c.setFillColor(colors.HexColor("#0284c7"))  # Vivid lake blue
    c.rect(0, PAGE_HEIGHT - 134, PAGE_WIDTH, 4, stroke=0, fill=1)

    # Soft organic water ripples on top header
    c.setFillColor(colors.Color(1, 1, 1, alpha=0.06))
    c.circle(PAGE_WIDTH - 40, PAGE_HEIGHT - 20, 90, stroke=0, fill=1)
    c.circle(PAGE_WIDTH - 90, PAGE_HEIGHT - 60, 60, stroke=0, fill=1)
    c.circle(40, PAGE_HEIGHT - 30, 70, stroke=0, fill=1)

    # 1.1 Year Pill Badge
    pill_x = 36.0
    pill_y = PAGE_HEIGHT - 44.0
    pill_w = 68.0
    pill_h = 24.0
    c.setFillColor(colors.HexColor("#0284c7"))
    c.roundRect(pill_x, pill_y, pill_w, pill_h, 6, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12.0)
    c.drawCentredString(pill_x + pill_w / 2.0, pill_y + 6.5, "2026")

    # 1.2 Main Title: PROVA CANOA (Strictly below 2026)
    c.setFont("Helvetica-Bold", 24.0)
    c.setFillColor(colors.white)
    c.drawString(pill_x, pill_y - 32.0, "PROVA CANOA")

    # 1.3 Subtitle / Discipline / Grade (Right Aligned in Top Banner)
    right_margin = PAGE_WIDTH - 36.0
    c.setFont("Helvetica-Bold", 14.0)
    c.setFillColor(colors.HexColor("#38bdf8"))  # Light sky blue
    c.drawRightString(right_margin, PAGE_HEIGHT - 38.0, "MATEMÁTICA")

    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#cbd5e1"))
    c.drawRightString(right_margin, PAGE_HEIGHT - 54.0, exam_subtitle or "8º ANO DO ENSINO FUNDAMENTAL")

    c.setFont("Helvetica-Bold", 8.0)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawRightString(right_margin, PAGE_HEIGHT - 70.0, "PREFEITURA MUNICIPAL DE LAGOA DA CANOA • SEMED")
    c.restoreState()

    # 1.4 Middle Card: Student Identification (Full Width)
    card_x = 36.0
    card_w = PAGE_WIDTH - 72.0  # 523.275 pt
    card_y = top_y0 + 20.0
    card_h = top_section_h - 134.0 - 35.0  # ~251 pt

    c.saveState()
    # Card container
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(1.0)
    c.roundRect(card_x, card_y, card_w, card_h, 8, stroke=1, fill=1)

    # Card Top Header Bar
    bar_h = 24.0
    c.setFillColor(colors.HexColor("#1e293b"))
    c.roundRect(card_x, card_y + card_h - bar_h, card_w, bar_h, 8, stroke=0, fill=1)
    c.rect(card_x, card_y + card_h - bar_h, card_w, 8, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(card_x + 14.0, card_y + card_h - 16.0, "CADERNO DE RESPOSTAS • IDENTIFICAÇÃO DO(A) ESTUDANTE")

    # Fields inside the card
    inner_x = card_x + 16.0
    inner_w = card_w - 32.0
    curr_y = card_y + card_h - bar_h - 18.0

    # Field 1: UNIDADE ESCOLAR
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(inner_x, curr_y, "UNIDADE ESCOLAR")
    curr_y -= 22.0
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.setLineWidth(0.8)
    c.roundRect(inner_x, curr_y, inner_w, 20.0, 3, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(inner_x + 8.0, curr_y + 5.5, school_name.upper())

    # Field 2: NOME COMPLETO DO(A) ESTUDANTE
    curr_y -= 16.0
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(inner_x, curr_y, "NOME COMPLETO DO(A) ESTUDANTE")
    curr_y -= 22.0
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.roundRect(inner_x, curr_y, inner_w, 20.0, 3, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 10.0)
    st_full = f"{student_name.upper()} ({student_reg})" if student_reg else student_name.upper()
    c.drawString(inner_x + 8.0, curr_y + 5.5, st_full)

    # Row 3: TURMA and TURNO (Two clean columns)
    curr_y -= 16.0
    col_w = (inner_w - 14.0) / 2.0

    # Field 3: TURMA
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(inner_x, curr_y, "TURMA")
    c.drawString(inner_x + col_w + 14.0, curr_y, "TURNO")

    curr_y -= 22.0
    # Turma box
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.roundRect(inner_x, curr_y, col_w, 20.0, 3, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(inner_x + 8.0, curr_y + 5.5, classroom_name.upper())

    # Turno box
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.roundRect(inner_x + col_w + 14.0, curr_y, col_w, 20.0, 3, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(inner_x + col_w + 22.0, curr_y + 5.5, shift.upper())
    c.restoreState()

    # =========================================================================
    # 2. BOTTOM HALF: SCAN ZONE / READING AREA (Strictly bounded by ArUco markers)
    # =========================================================================
    reading_y0 = 0.0
    reading_h = PAGE_HEIGHT / 2.0  # 420.94 pt
    reading_w = PAGE_WIDTH         # 595.275 pt

    # Geometry for ArUco markers inside the bottom half
    pad_x = 18.0
    pad_y = 14.0
    m_size = 36.0

    markers = {
        0: (pad_x, reading_y0 + reading_h - pad_y - m_size),                    # Top-Left (TL)
        1: (reading_w - pad_x - m_size, reading_y0 + reading_h - pad_y - m_size),# Top-Right (TR)
        2: (reading_w - pad_x - m_size, reading_y0 + pad_y),                    # Bottom-Right (BR)
        3: (pad_x, reading_y0 + pad_y)                                          # Bottom-Left (BL)
    }

    marker_centers_canonical = {}
    for mid, (mx, my) in markers.items():
        pil_marker = generate_aruco_marker_image(mid, size=160)
        c.drawImage(ImageReader(pil_marker), mx, my, m_size, m_size)

        cx_pt = mx + m_size / 2.0
        cy_pt = (my - reading_y0) + m_size / 2.0

        canon_x = int((cx_pt / reading_w) * CANONICAL_WIDTH)
        canon_y = int(((reading_h - cy_pt) / reading_h) * CANONICAL_HEIGHT_HALF)
        marker_centers_canonical[str(mid)] = (canon_x, canon_y)

    # Content boundaries inside reading area
    content_left = pad_x + m_size + 10.0
    content_right = reading_w - pad_x - m_size - 10.0
    content_width = content_right - content_left

    # 2.1 Instructions Banner at top of reading area
    instr_h = 14.0
    instr_y = reading_y0 + reading_h - pad_y - 20.0

    c.saveState()
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(0.6)
    c.roundRect(content_left, instr_y, content_width, instr_h, 3, stroke=1, fill=1)

    c.setFillColor(colors.HexColor("#1e293b"))
    c.setFont("Helvetica-Bold", 5.8)
    c.drawString(content_left + 8.0, instr_y + 4.0, "ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.")
    c.drawRightString(content_right - 8.0, instr_y + 4.0, "CORRETO: [ ⬤ ]   ERRADO: [ ✕ ] [ ✓ ]")
    c.restoreState()

    # 2.2 Question Grid (2 Columns for 22 Questions)
    cols = 2
    questions_per_col = 12
    gap_cols = 16.0
    total_col_w = (content_width - gap_cols) / cols
    item_col_w = 30.0
    alt_col_w = (total_col_w - item_col_w) / num_alternatives

    grid_top = instr_y - 8.0
    grid_bottom = reading_y0 + pad_y + m_size + 6.0
    avail_h = grid_top - grid_bottom

    th_h = 16.0
    q_row_h = (avail_h - th_h) / questions_per_col  # ~24.5 pt per row
    bubble_r = 6.2  # Generous radius for student filling and OMR precision

    options = ["A", "B", "C", "D"][:num_alternatives]
    bubbles_canonical_map = {}

    # Render Table Headers
    for c_idx in range(cols):
        col_x = content_left + c_idx * (total_col_w + gap_cols)

        # Header ITEM
        c.saveState()
        c.setFillColor(colors.HexColor("#0f2744"))  # Navy accent
        c.setStrokeColor(colors.HexColor("#0f172a"))
        c.setLineWidth(0.6)
        c.rect(col_x, grid_top - th_h, item_col_w, th_h, stroke=1, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7.2)
        c.drawCentredString(col_x + item_col_w / 2.0, grid_top - th_h + 4.5, "ITEM")

        # Header Alternatives
        for o_idx, opt in enumerate(options):
            bx = col_x + item_col_w + o_idx * alt_col_w
            c.setFillColor(colors.HexColor("#e2e8f0"))
            c.setStrokeColor(colors.HexColor("#64748b"))
            c.setLineWidth(0.6)
            c.rect(bx, grid_top - th_h, alt_col_w, th_h, stroke=1, fill=1)
            c.setFillColor(colors.HexColor("#0f172a"))
            c.setFont("Helvetica-Bold", 8.0)
            c.drawCentredString(bx + alt_col_w / 2.0, grid_top - th_h + 4.5, opt)
        c.restoreState()

    # Render Question Rows & Bubbles
    for q_idx in range(num_questions):
        q_num = q_idx + 1
        c_idx = q_idx // questions_per_col
        r_idx = q_idx % questions_per_col

        col_x = content_left + c_idx * (total_col_w + gap_cols)
        row_top = grid_top - th_h - r_idx * q_row_h
        row_y = row_top - q_row_h

        bg_color = colors.HexColor("#f8fafc") if r_idx % 2 == 1 else colors.white

        # ITEM cell
        c.saveState()
        c.setFillColor(colors.HexColor("#f1f5f9"))
        c.setStrokeColor(colors.HexColor("#94a3b8"))
        c.setLineWidth(0.5)
        c.rect(col_x, row_y, item_col_w, q_row_h, stroke=1, fill=1)
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 8.0)
        c.drawCentredString(col_x + item_col_w / 2.0, row_y + (q_row_h - 7.0) / 2.0, f"{q_num:02d}")
        c.restoreState()

        bubbles_canonical_map[str(q_num)] = {}

        # Alternative bubbles
        for o_idx, opt in enumerate(options):
            bx = col_x + item_col_w + o_idx * alt_col_w
            c.saveState()
            c.setFillColor(bg_color)
            c.setStrokeColor(colors.HexColor("#cbd5e1"))
            c.setLineWidth(0.5)
            c.rect(bx, row_y, alt_col_w, q_row_h, stroke=1, fill=1)

            center_x = bx + alt_col_w / 2.0
            center_y = row_y + q_row_h / 2.0

            is_filled = filled_answers and filled_answers.get(str(q_num)) == opt

            if is_filled:
                c.setStrokeColor(colors.HexColor("#0f172a"))
                c.setFillColor(colors.HexColor("#0f172a"))
                c.circle(center_x, center_y, bubble_r, stroke=1, fill=1)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", bubble_r * 1.15)
                c.drawCentredString(center_x, center_y - (bubble_r * 0.36), opt)
            else:
                c.setStrokeColor(colors.HexColor("#1e293b"))
                c.setFillColor(colors.white)
                c.setLineWidth(0.7)
                c.circle(center_x, center_y, bubble_r, stroke=1, fill=1)
                # Option letter in subtle slate gray (#94A3B8)
                c.setFillColor(colors.HexColor("#94a3b8"))
                c.setFont("Helvetica-Bold", bubble_r * 1.15)
                c.drawCentredString(center_x, center_y - (bubble_r * 0.36), opt)

            c.restoreState()

            # Exact canonical coordinates calculation for OMR engine
            cx_pt = center_x
            cy_pt = center_y - reading_y0
            canon_x = int((cx_pt / reading_w) * CANONICAL_WIDTH)
            canon_y = int(((reading_h - cy_pt) / reading_h) * CANONICAL_HEIGHT_HALF)
            canon_r = int((bubble_r / reading_w) * CANONICAL_WIDTH)

            bubbles_canonical_map[str(q_num)][opt] = {
                "x": canon_x,
                "y": canon_y,
                "radius": max(5, canon_r)
            }

    # 2.3 QR Code at Bottom-Right (Below question 22 in column 2)
    qr_payload = f"E:{exam_id}|S:{student_id}"
    qr_size = 56.0
    qr_x = content_right - qr_size - 4.0
    qr_y = reading_y0 + pad_y + 12.0

    qr_widget = QrCodeWidget(qr_payload)
    qr_widget.barWidth = qr_size
    qr_widget.barHeight = qr_size
    qr_widget.barBorder = 1
    d = Drawing(qr_size, qr_size)
    d.add(qr_widget)
    d.drawOn(c, qr_x, qr_y)

    c.saveState()
    c.setFont("Helvetica-Bold", 6.5)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawCentredString(qr_x + qr_size / 2.0, qr_y - 7.5, f"ID: {student_reg} • MAT")
    c.restoreState()

    # 2.4 Footer micro-text inside reading area
    c.saveState()
    c.setFont("Helvetica", 5.5)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(content_left, reading_y0 + pad_y + 3.0, "Prefeitura Municipal de Lagoa da Canoa • SEMED — Sistema OMR de Avaliações")
    c.restoreState()

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    actual_pdf_path = output_pdf_path
    try:
        os.makedirs(os.path.dirname(os.path.abspath(actual_pdf_path)), exist_ok=True)
        with open(actual_pdf_path, "wb") as f:
            f.write(pdf_bytes)
    except PermissionError:
        actual_pdf_path = output_pdf_path.replace(".pdf", "_novo.pdf")
        with open(actual_pdf_path, "wb") as f:
            f.write(pdf_bytes)

    template_data = {
        "exam_id": exam_id,
        "is_compact": True,
        "canonical_width": CANONICAL_WIDTH,
        "canonical_height": CANONICAL_HEIGHT_HALF,
        "marker_centers": marker_centers_canonical,
        "num_questions": num_questions,
        "num_alternatives": num_alternatives,
        "bubbles": bubbles_canonical_map
    }

    return actual_pdf_path, template_data

if __name__ == "__main__":
    STUDENT_ID = "377e901e-4eb9-41c2-b676-d00d8a6defc0"
    EXAM_ID = "a7556746-7e39-4526-b752-bf0477a0e461"
    
    st = get_student_by_id(STUDENT_ID)
    ex = get_exam(EXAM_ID)
    
    school_name = "ESC. GOV. LUIZ CAVALCANTE"
    student_name = "ADRYEL GABRIEL RODRIGUES DA SILVA"
    student_reg = "8BM"
    classroom_name = "8º ANO - B MATUTINO"
    shift = "MATUTINO"
    
    base_out = os.path.join(backend_dir, "storage", "sheets")
    out_pdf = os.path.join(base_out, "capa_teste_adryel_gabriel_8bm_v2.pdf")
    pdf_p, tpl = render_cover_and_template(
        output_pdf_path=out_pdf,
        school_name=school_name,
        student_name=student_name,
        student_reg=student_reg,
        student_id=STUDENT_ID,
        classroom_name=classroom_name,
        shift=shift,
        exam_id=EXAM_ID,
        exam_title=ex.get("title", "PROVA CANOA 2026 – MATEMÁTICA"),
        exam_subtitle=ex.get("subtitle", "8º ANO DO ENSINO FUNDAMENTAL"),
        num_questions=22,
        num_alternatives=4
    )
    print("PDF gerado:", pdf_p)
    print("Total de questões no template:", len(tpl["bubbles"]))
    print("Q1 no template:", tpl["bubbles"]["1"])
    print("Q22 no template:", tpl["bubbles"]["22"])
