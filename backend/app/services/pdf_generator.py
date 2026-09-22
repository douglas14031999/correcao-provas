import os
import io
import math
import base64
import numpy as np
import cv2
from PIL import Image
from reportlab.lib import pagesizes, colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from typing import Optional, List, Dict, Any
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget

PAGE_WIDTH, PAGE_HEIGHT = pagesizes.A4  # 595.275 x 841.889 pt

# Canonical resolution for warp perspective
CANONICAL_WIDTH = 1654
CANONICAL_HEIGHT = 2338
CANONICAL_HEIGHT_HALF = 1169  # Proporção exata 1:1 para modelo 2 por folha (meia página)

DEFAULT_LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage", "assets", "logo_lagoa_da_canoa.png"
)

def generate_aruco_marker_image(marker_id: int, size: int = 140) -> Image.Image:
    """Generate PIL image of ArUco marker using DICT_4X4_50."""
    try:
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        marker_img = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
    except AttributeError:
        dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        marker_img = cv2.aruco.drawMarker(dictionary, marker_id, size)
    return Image.fromarray(marker_img)

def _resolve_hex_color(hex_str: Optional[str], default: str = "#244061") -> colors.HexColor:
    try:
        if not hex_str or not isinstance(hex_str, str):
            return colors.HexColor(default)
        clean = hex_str.strip()
        if not clean.startswith("#"):
            clean = f"#{clean}"
        if len(clean) in (4, 7):
            return colors.HexColor(clean)
        return colors.HexColor(default)
    except Exception:
        return colors.HexColor(default)

def render_sheet_unit(
    c: canvas.Canvas,
    x0: float,
    y0: float,
    width: float,
    height: float,
    exam_id: str,
    title: str,
    subtitle: str = "2º ANO DO ENSINO FUNDAMENTAL",
    school_name: str = "",
    student_name: str = "",
    student_id: str = "",
    classroom: str = "",
    shift: str = "( ) MANHÃ    ( ) TARDE",
    num_questions: int = 20,
    num_alternatives: int = 4,
    logo_path: str = None,
    is_compact: bool = False,
    header_color: str = "#244061",
    filled_answers: Optional[Dict[str, str]] = None
) -> dict:
    """
    Renders an official answer sheet adhering to the Canoa / i-Diário visual identity:
    - Dark Navy Blue Header Banner (#244061) with 2 lines (Title & Subtitle/Etapa)
    - High-contrast institutional table underneath with custom or municipal Logo box
    - Standard fields: ESCOLA, ESTUDANTE, TURMA and TURNO: ( ) MANHÃ ( ) TARDE
    - 4 ArUco fiducial markers for submillimeter perspective correction
    - Embedded QR Code with exam ID and optional student ID
    - Structured Question Grid / Table with bounded ITEM and Alternative cells
    """
    # 1. Margins & Geometry
    canon_w = CANONICAL_WIDTH
    canon_h = CANONICAL_HEIGHT_HALF if is_compact else CANONICAL_HEIGHT

    m_size = 36.0 if is_compact else 42.0
    pad_x = 18.0 if is_compact else 22.0
    pad_y = 12.0 if is_compact else 18.0

    # 4 ArUco Markers
    # ID 0: Top-Left, ID 1: Top-Right, ID 2: Bottom-Right, ID 3: Bottom-Left
    markers = {
        0: (x0 + pad_x, y0 + height - pad_y - m_size),
        1: (x0 + width - pad_x - m_size, y0 + height - pad_y - m_size),
        2: (x0 + width - pad_x - m_size, y0 + pad_y),
        3: (x0 + pad_x, y0 + pad_y)
    }

    marker_centers_canonical = {}
    for mid, (mx, my) in markers.items():
        pil_marker = generate_aruco_marker_image(mid, size=160)
        c.drawImage(ImageReader(pil_marker), mx, my, m_size, m_size)

        cx_pt = (mx - x0) + m_size / 2.0
        cy_pt = (my - y0) + m_size / 2.0

        canon_x = int((cx_pt / width) * canon_w)
        canon_y = int(((height - cy_pt) / height) * canon_h)
        marker_centers_canonical[str(mid)] = (canon_x, canon_y)

    # 2. Content Bounds
    content_left = x0 + pad_x + m_size + 10.0
    content_right = x0 + width - pad_x - m_size - 10.0
    content_width = content_right - content_left

    # 3. Header Dimensions (Optimized to give maximum possible size to QR Code)
    banner_h = 26.0 if is_compact else 32.0
    banner_y = y0 + height - pad_y - banner_h
    tbl_top = banner_y
    tbl_h = 44.0 if is_compact else 54.0
    tbl_y = tbl_top - tbl_h
    total_header_h = banner_h + tbl_h

    # QR Code centered perfectly between banner top and table bottom (the two red lines)
    qr_inner_size = 68.0 if is_compact else 84.0
    qr_x = content_right - qr_inner_size
    qr_y = tbl_y + (total_header_h - qr_inner_size) / 2.0

    header_w = qr_x - content_left - (8.0 if is_compact else 10.0)

    # Compact short payload (25x25 chunky modules instead of 41x41 dense micro-dots)
    # 12 hex chars is 48 bits: perfectly unique and collision-free
    e_code = exam_id[:12] if (exam_id and len(exam_id) >= 12) else exam_id
    s_code = student_id[:12] if (student_id and len(student_id) >= 12) else student_id
    qr_payload = f"E:{e_code}|S:{s_code}" if student_id else f"E:{e_code}"

    qr_widget = QrCodeWidget(qr_payload)
    qr_widget.barWidth = qr_inner_size
    qr_widget.barHeight = qr_inner_size
    qr_widget.barBorder = 1  # 1 module clean quiet zone for guaranteed instant decoding
    d = Drawing(qr_inner_size, qr_inner_size)
    d.add(qr_widget)
    d.drawOn(c, qr_x, qr_y)

    # 4. Header Banner
    accent_color = _resolve_hex_color(header_color, "#244061")
    c.setFillColor(accent_color)
    c.setStrokeColor(colors.HexColor("#0f172a"))
    c.setLineWidth(0.8)
    c.rect(content_left, banner_y, header_w, banner_h, stroke=1, fill=1)

    # Line 1: Main Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5 if is_compact else 10.5)
    c.drawCentredString(content_left + header_w / 2.0, banner_y + (14.5 if is_compact else 18.0), (title or "PROVA CANOA 2026 – AVALIAÇÃO").upper()[:52])

    # Line 2: Subtitle / Etapa
    c.setFont("Helvetica-Bold", 7.0 if is_compact else 8.5)
    c.drawCentredString(content_left + header_w / 2.0, banner_y + (4.5 if is_compact else 6.0), (subtitle or "ENSINO FUNDAMENTAL").upper()[:56])

    # 4. Identification Table under Banner
    logo_col_w = 64.0 if is_compact else 76.0

    # Outer table rectangle
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.rect(content_left, tbl_y, header_w, tbl_h, stroke=1, fill=1)

    # Vertical divider for Logo column
    c.line(content_left + logo_col_w, tbl_y, content_left + logo_col_w, tbl_top)

    # Draw Logo in left cell
    active_logo = logo_path if (logo_path and os.path.exists(logo_path)) else (DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None)
    if active_logo:
        try:
            c.drawImage(active_logo, content_left + 3, tbl_y + 3, logo_col_w - 6, tbl_h - 6, preserveAspectRatio=True, anchor="c")
        except Exception:
            pass
    else:
        # Fallback shield / text if no logo file exists
        c.setFillColor(colors.HexColor("#1e293b"))
        c.setFont("Helvetica-Bold", 7.0)
        c.drawCentredString(content_left + logo_col_w / 2.0, tbl_y + tbl_h / 2.0, "MUNICÍPIO")

    # Right rows
    r_left = content_left + logo_col_w
    r_width = header_w - logo_col_w
    row_h = tbl_h / 3.0

    # Row dividers
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.6)
    c.line(r_left, tbl_top - row_h, r_left + r_width, tbl_top - row_h)
    c.line(r_left, tbl_top - 2 * row_h, r_left + r_width, tbl_top - 2 * row_h)

    # Row 1: ESCOLA:
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 6.8 if is_compact else 8.0)
    c.drawString(r_left + 5, tbl_top - row_h + (4.0 if is_compact else 5.5), "ESCOLA:")
    if school_name:
        c.setFont("Helvetica", 7.0 if is_compact else 8.5)
        c.drawString(r_left + (48 if is_compact else 55), tbl_top - row_h + (4.0 if is_compact else 5.5), school_name.upper()[:46])

    # Row 2: ESTUDANTE:
    c.setFont("Helvetica-Bold", 6.8 if is_compact else 8.0)
    c.drawString(r_left + 5, tbl_top - 2 * row_h + (4.0 if is_compact else 5.5), "ESTUDANTE:")
    display_student = student_name
    if filled_answers and not display_student:
        display_student = "GABARITO OFICIAL — RESPOSTAS CORRETAS"
    if display_student:
        c.setFont("Helvetica-Bold" if filled_answers else "Helvetica", 7.0 if is_compact else 8.5)
        c.drawString(r_left + (60 if is_compact else 70), tbl_top - 2 * row_h + (4.0 if is_compact else 5.5), display_student.upper()[:44])

    # Row 3: TURMA: | TURNO: ( ) MANHÃ   ( ) TARDE
    turma_w = r_width * 0.42
    c.drawString(r_left + 5, tbl_y + (4.0 if is_compact else 5.5), "TURMA:")
    if classroom:
        c.setFont("Helvetica", 7.0 if is_compact else 8.5)
        c.drawString(r_left + (45 if is_compact else 52), tbl_y + (4.0 if is_compact else 5.5), classroom.upper()[:16])

    # Vertical divider between TURMA and TURNO
    c.line(r_left + turma_w, tbl_y, r_left + turma_w, tbl_top - 2 * row_h)

    c.setFont("Helvetica-Bold", 6.8 if is_compact else 8.0)
    c.drawString(r_left + turma_w + 6, tbl_y + (4.0 if is_compact else 5.5), "TURNO:")
    c.setFont("Helvetica-Bold", 6.2 if is_compact else 7.5)
    c.drawString(r_left + turma_w + (42 if is_compact else 48), tbl_y + (4.0 if is_compact else 5.5), shift or "(  ) MANHÃ       (  ) TARDE")

    # 5. Instructions Banner
    instr_y = tbl_y - (18.0 if is_compact else 24.0)
    instr_h = 10.0 if is_compact else 13.0
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.setLineWidth(0.5)
    c.rect(content_left, instr_y, content_width, instr_h, stroke=1, fill=1)

    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica-Bold", 5.2 if is_compact else 6.0)
    if filled_answers:
        c.drawString(content_left + 6, instr_y + (2.5 if is_compact else 3.5), "★ GABARITO OFICIAL HOMOLOGADO — FOLHA COM AS RESPOSTAS CORRETAS")
        c.drawRightString(content_left + content_width - 6, instr_y + (2.5 if is_compact else 3.5), "DOCUMENTO DE CONFERÊNCIA E AUDITORIA")
    else:
        c.drawString(content_left + 6, instr_y + (2.5 if is_compact else 3.5), "ORIENTAÇÕES: Preencha totalmente a bolha com caneta preta ou azul.")
        c.drawRightString(content_left + content_width - 6, instr_y + (2.5 if is_compact else 3.5), "CORRETO: [ ⬤ ]   ERRADO: [ ✕ ] [ ✓ ]")

    # 6. Questions & Alternatives in a Structured Table Grid
    options = ["A", "B", "C", "D", "E"][:num_alternatives]
    
    # Calculate optimal column count
    # RULE: Up to 12 questions stays in a single column (cols = 1).
    # Only starts jumping to the next column after 12 questions.
    if num_questions <= 12:
        cols = 1
        questions_per_col = num_questions
    elif num_questions <= 24:
        cols = 2
        questions_per_col = 12
    elif num_questions <= 36:
        cols = 3
        questions_per_col = 12
    elif num_questions <= 48:
        cols = 4
        questions_per_col = 12
    else:
        cols = min(5, math.ceil(num_questions / 12))
        questions_per_col = math.ceil(num_questions / cols)

    grid_top = instr_y - (8.0 if is_compact else 10.0)
    grid_bottom = y0 + pad_y + m_size + (6.0 if is_compact else 10.0)
    avail_h = grid_top - grid_bottom

    th_h = 14.0 if is_compact else 16.0
    # Provide generous row height for clean, legible bubbles
    max_row_h = 28.0 if not is_compact else 18.0
    q_row_h = min(max_row_h, max(14.0, (avail_h - th_h) / questions_per_col))

    gap_between_cols = 12.0 if is_compact else 16.0
    if cols == 1:
        total_col_w = min(content_width, 280.0 if is_compact else 320.0)
        start_x_offset = (content_width - total_col_w) / 2.0
    else:
        total_col_w = (content_width - (cols - 1) * gap_between_cols) / cols
        start_x_offset = 0.0

    item_col_w = 28.0 if is_compact else 34.0
    alt_col_w = (total_col_w - item_col_w) / num_alternatives

    # Bubble radius: enlarged for easier filling by students and robust computer vision detection
    max_bubble_r = 7.0 if not is_compact else 4.8
    bubble_r = min(max_bubble_r, max(3.2, min(q_row_h * 0.30, alt_col_w * 0.32)))

    bubbles_canonical_map = {}

    # Render Table Headers for each column
    for c_idx in range(cols):
        col_x = content_left + start_x_offset + c_idx * (total_col_w + gap_between_cols)

        # ITEM cell
        c.setFillColor(accent_color)
        c.setStrokeColor(colors.HexColor("#0f172a"))
        c.setLineWidth(0.6)
        c.rect(col_x, grid_top - th_h, item_col_w, th_h, stroke=1, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 6.5 if is_compact else 7.5)
        c.drawCentredString(col_x + item_col_w / 2.0, grid_top - th_h + (3.5 if is_compact else 4.5), "ITEM")

        # Alternative header cells
        for o_idx, opt in enumerate(options):
            bx = col_x + item_col_w + o_idx * alt_col_w
            c.setFillColor(colors.HexColor("#E2E8F0"))
            c.setStrokeColor(colors.HexColor("#64748B"))
            c.setLineWidth(0.6)
            c.rect(bx, grid_top - th_h, alt_col_w, th_h, stroke=1, fill=1)
            c.setFillColor(colors.HexColor("#0F172A"))
            c.setFont("Helvetica-Bold", 7.0 if is_compact else 8.5)
            c.drawCentredString(bx + alt_col_w / 2.0, grid_top - th_h + (3.5 if is_compact else 4.5), opt)

    # Render Question Rows & Cells
    for q_idx in range(num_questions):
        q_num = q_idx + 1
        c_idx = q_idx // questions_per_col
        r_idx = q_idx % questions_per_col

        col_x = content_left + start_x_offset + c_idx * (total_col_w + gap_between_cols)
        row_top = grid_top - th_h - r_idx * q_row_h
        row_y = row_top - q_row_h

        # Alternating row background for optimal readability
        bg_color = colors.HexColor("#F8FAFC") if r_idx % 2 == 1 else colors.white

        # ITEM Cell
        c.setFillColor(colors.HexColor("#F1F5F9"))
        c.setStrokeColor(colors.HexColor("#94A3B8"))
        c.setLineWidth(0.5)
        c.rect(col_x, row_y, item_col_w, q_row_h, stroke=1, fill=1)

        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 7.0 if is_compact else 8.5)
        c.drawCentredString(col_x + item_col_w / 2.0, row_y + (q_row_h - (5.5 if is_compact else 7.0)) / 2.0, f"{q_num:02d}")

        bubbles_canonical_map[str(q_num)] = {}

        # Alternative Cells with Centered Bubbles
        for o_idx, opt in enumerate(options):
            bx = col_x + item_col_w + o_idx * alt_col_w
            c.setFillColor(bg_color)
            c.setStrokeColor(colors.HexColor("#CBD5E1"))
            c.setLineWidth(0.5)
            c.rect(bx, row_y, alt_col_w, q_row_h, stroke=1, fill=1)

            center_x = bx + alt_col_w / 2.0
            center_y = row_y + q_row_h / 2.0

            # Check if this bubble is the correct answer
            is_correct_ans = False
            if filled_answers:
                expected = filled_answers.get(str(q_num))
                if expected is None:
                    expected = filled_answers.get(int(q_num))
                if expected:
                    exp_clean = str(expected).strip().upper()
                    if exp_clean in ["*", "TODAS", "ALL", "ANULADA"] or opt.upper() == exp_clean or opt.upper() in [x.strip() for x in exp_clean.split(",")]:
                        is_correct_ans = True

            if is_correct_ans:
                # Filled bubble: solid dark circle
                c.setStrokeColor(colors.HexColor("#0F172A"))
                c.setFillColor(colors.HexColor("#0F172A"))
                c.setLineWidth(0.8)
                c.circle(center_x, center_y, bubble_r, stroke=1, fill=1)

                # Option letter inside: bright bold white for maximum contrast and legibility
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", bubble_r * 1.15)
                c.drawCentredString(center_x, center_y - (bubble_r * 0.36), opt)
            else:
                # Bubble circle: sharp, crisp border
                c.setStrokeColor(colors.HexColor("#1E293B"))
                c.setFillColor(colors.white)
                c.setLineWidth(0.7)
                c.circle(center_x, center_y, bubble_r, stroke=1, fill=1)

                # Option letter inside bubble: subtle slate gray (#94A3B8)
                # Highly readable to student eye, but filtered out by OMR binarization
                c.setFillColor(colors.HexColor("#94A3B8"))
                c.setFont("Helvetica-Bold", bubble_r * 1.15)
                c.drawCentredString(center_x, center_y - (bubble_r * 0.36), opt)

            # Calculate Canonical coordinates for OpenCV OMR engine
            cx_pt = center_x - x0
            cy_pt = center_y - y0
            canon_x = int((cx_pt / width) * canon_w)
            canon_y = int(((height - cy_pt) / height) * canon_h)
            canon_r = int((bubble_r / width) * canon_w)

            bubbles_canonical_map[str(q_num)][opt] = {
                "x": canon_x,
                "y": canon_y,
                "radius": max(4, canon_r)
            }

    # 7. Institutional Footer
    c.setFont("Helvetica", 5.5 if is_compact else 6.5)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawString(content_left, y0 + pad_y + (2.0 if is_compact else 4.0), "Prefeitura Municipal de Lagoa da Canoa — Secretaria Municipal de Educação | Sistema OMR Inteligente")
    c.drawRightString(content_right, y0 + pad_y + (2.0 if is_compact else 4.0), "Página 1 de 1")

    return {
        "exam_id": exam_id,
        "is_compact": is_compact,
        "canonical_width": canon_w,
        "canonical_height": canon_h,
        "marker_centers": marker_centers_canonical,
        "num_questions": num_questions,
        "num_alternatives": num_alternatives,
        "bubbles": bubbles_canonical_map
    }

def get_cover_template(exam_id: str = "", num_questions: int = 22) -> dict:
    """Returns the canonical cover template (Opção 4 / Capa da Prova Canoa 2026)."""
    cover_bubbles = {}
    for q in range(1, num_questions + 1):
        q_str = str(q)
        cover_bubbles[q_str] = {}
        is_col2 = (q >= 13)
        row_idx = (q - 13) if is_col2 else (q - 1)
        approx_y = 225 + row_idx * 53
        base_x_list = [956, 1076, 1196, 1316] if is_col2 else [291, 407, 527, 647]
        for opt_idx, opt_letter in enumerate(["A", "B", "C", "D"]):
            cover_bubbles[q_str][opt_letter] = {
                "x": base_x_list[opt_idx],
                "y": approx_y,
                "radius": 18
            }
    return {
        "exam_id": exam_id,
        "is_compact": True,
        "is_cover": True,
        "canonical_width": 1654,
        "canonical_height": 1169,
        "marker_centers": {"0": (100, 83), "1": (1553, 83), "2": (1553, 1085), "3": (100, 1085)},
        "num_questions": num_questions,
        "num_alternatives": 4,
        "bubbles": cover_bubbles,
        "name": "capa_prova_canoa"
    }

_EXAM_TEMPLATE_CACHE: dict = {}

def get_exam_template_for_layout(exam: dict, is_compact: bool = False, is_cover: bool = False) -> dict:
    """
    Returns or dynamically generates the accurate canonical template (single, compact or cover).
    When is_cover=True (QR at bottom), returns the cover template.
    When is_cover=False (QR at top), returns the official gabarito template.
    Uses in-memory cache to eliminate repetitive ReportLab rendering overhead.
    """
    if isinstance(exam, str):
        from app.services.database import get_exam
        exam = get_exam(exam) or {}
    elif not isinstance(exam, dict):
        exam = {}

    exam_id = str(exam.get("id", ""))
    num_q = int(exam.get("num_questions", 20) or 20)
    num_alt = int(exam.get("num_alternatives", 4) or 4)
    cache_key = (exam_id, is_compact, is_cover, num_q, num_alt)

    if cache_key in _EXAM_TEMPLATE_CACHE:
        return _EXAM_TEMPLATE_CACHE[cache_key]

    if is_cover:
        tpl = get_cover_template(exam_id, num_q)
        _EXAM_TEMPLATE_CACHE[cache_key] = tpl
        return tpl

    stored_template = exam.get("sheet_template") or {}
    if isinstance(stored_template, str):
        try:
            stored_template = json.loads(stored_template)
        except Exception:
            stored_template = {}

    req_h = CANONICAL_HEIGHT_HALF if is_compact else CANONICAL_HEIGHT
    if isinstance(stored_template, dict) and stored_template.get("canonical_height") == req_h and stored_template.get("bubbles") and not stored_template.get("is_cover"):
        _EXAM_TEMPLATE_CACHE[cache_key] = stored_template
        return stored_template

    if is_compact and exam.get("sheet_template_compact"):
        tpl_compact = exam["sheet_template_compact"]
        if isinstance(tpl_compact, str):
            try:
                tpl_compact = json.loads(tpl_compact)
            except Exception:
                tpl_compact = {}
        if isinstance(tpl_compact, dict) and tpl_compact.get("bubbles"):
            _EXAM_TEMPLATE_CACHE[cache_key] = tpl_compact
            return tpl_compact

    buffer = io.BytesIO()
    half_h = PAGE_HEIGHT / 2.0
    c = canvas.Canvas(buffer, pagesize=(PAGE_WIDTH, half_h if is_compact else PAGE_HEIGHT))
    
    template = render_sheet_unit(
        c, x0=0, y0=0,
        width=PAGE_WIDTH,
        height=half_h if is_compact else PAGE_HEIGHT,
        exam_id=exam.get("id", ""),
        title=exam.get("title", ""),
        subtitle=exam.get("subtitle", "2º ANO DO ENSINO FUNDAMENTAL"),
        school_name=exam.get("school_name", ""),
        student_name=exam.get("student_name", ""),
        classroom=exam.get("classroom", ""),
        shift=exam.get("shift", "( ) MANHÃ    ( ) TARDE"),
        num_questions=num_q,
        num_alternatives=num_alt,
        logo_path=exam.get("logo_path"),
        is_compact=is_compact,
        header_color=exam.get("header_color", "#244061")
    )
    _EXAM_TEMPLATE_CACHE[cache_key] = template
    return template

def generate_answer_sheet_pdf(
    exam_id: str,
    title: str,
    subtitle: str = "2º ANO DO ENSINO FUNDAMENTAL",
    school_name: str = "",
    student_name: str = "",
    classroom: str = "",
    shift: str = "( ) MANHÃ    ( ) TARDE",
    num_questions: int = 20,
    num_alternatives: int = 4,
    sheets_per_page: int = 1,
    logo_path: str = None,
    output_path: str = None,
    student_id: str = "",
    header_color: str = "#244061",
    filled_answers: Optional[Dict[str, str]] = None
) -> tuple[bytes, dict]:
    """
    Generates Answer Sheet PDF adhering to the user's requested layout:
    - sheets_per_page = 1: Single full A4 sheet
    - sheets_per_page = 2: Two autonomous A5 half-sheets with scissor cut guide (50% paper economy)
    - filled_answers: When provided, renders bubbles filled for correct answers (Gabarito Oficial)
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=pagesizes.A4)

    if sheets_per_page == 2:
        half_h = PAGE_HEIGHT / 2.0  # 420.94 pt

        # Top Sheet (Unit 1)
        template_data = render_sheet_unit(
            c, x0=0, y0=half_h, width=PAGE_WIDTH, height=half_h,
            exam_id=exam_id, title=title, subtitle=subtitle,
            school_name=school_name, student_name=student_name,
            student_id=student_id,
            classroom=classroom, shift=shift,
            num_questions=num_questions, num_alternatives=num_alternatives,
            logo_path=logo_path, is_compact=True,
            header_color=header_color,
            filled_answers=filled_answers
        )

        # Scissor Cut Line in middle
        c.setStrokeColor(colors.HexColor("#94a3b8"))
        c.setLineWidth(0.8)
        c.setDash([4, 4])
        c.line(16, half_h, PAGE_WIDTH - 16, half_h)
        c.setDash([])

        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(colors.HexColor("#64748b"))
        c.drawCentredString(PAGE_WIDTH / 2.0, half_h - 2.5, "✂ - - - - - - - - CORTE AQUI PARA DESTACAR AS DUAS FOLHAS - - - - - - - - ✂")

        # Bottom Sheet (Unit 2 - identical)
        render_sheet_unit(
            c, x0=0, y0=0, width=PAGE_WIDTH, height=half_h,
            exam_id=exam_id, title=title, subtitle=subtitle,
            school_name=school_name, student_name=student_name,
            student_id=student_id,
            classroom=classroom, shift=shift,
            num_questions=num_questions, num_alternatives=num_alternatives,
            logo_path=logo_path, is_compact=True,
            header_color=header_color,
            filled_answers=filled_answers
        )

    else:
        # Full A4 Sheet
        template_data = render_sheet_unit(
            c, x0=0, y0=0, width=PAGE_WIDTH, height=PAGE_HEIGHT,
            exam_id=exam_id, title=title, subtitle=subtitle,
            school_name=school_name, student_name=student_name,
            student_id=student_id,
            classroom=classroom, shift=shift,
            num_questions=num_questions, num_alternatives=num_alternatives,
            logo_path=logo_path, is_compact=False,
            header_color=header_color,
            filled_answers=filled_answers
        )

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes, template_data


def render_attendance_roster_page(
    c: canvas.Canvas,
    classroom: dict,
    students: list,
    exams: list,
    logo_path: str = None
):
    """
    Renders the official attendance and signature list (Ata de Presença e Entrega de Gabaritos)
    as the first page(s) of a batch answer sheet PDF.
    Contains two primary columns: NOME DO ALUNO and ASSINATURA DO ALUNO (along with index #).
    """
    try:
        from app.services.database import get_system_settings
        sys_settings = get_system_settings()
    except Exception:
        sys_settings = {
            "prefeitura_name": "PREFEITURA MUNICIPAL DE LAGOA DA CANOA",
            "secretaria_name": "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
            "state_name": "Estado de Alagoas",
            "logo_path": ""
        }

    prefeitura_name = sys_settings.get("prefeitura_name") or "PREFEITURA MUNICIPAL DE LAGOA DA CANOA"
    secretaria_name = sys_settings.get("secretaria_name") or "SECRETARIA MUNICIPAL DE EDUCAÇÃO"
    state_name = sys_settings.get("state_name") or "Estado de Alagoas"

    eff_logo = logo_path or sys_settings.get("logo_path") or DEFAULT_LOGO_PATH
    if eff_logo and not os.path.exists(eff_logo):
        eff_logo = DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None

    school_name = classroom.get("school_name", "")
    if not school_name and exams and len(exams) > 0:
        school_name = exams[0].get("school_name", "")
    school_name = school_name or "ESCOLA MUNICIPAL"

    class_name = classroom.get("name", "")
    raw_shift = (classroom.get("shift") or "MANHÃ").upper()
    shift_label = f"[X] {raw_shift}" if raw_shift else "(  ) MANHÃ   (  ) TARDE"

    # Exam title(s)
    if len(exams) >= 2:
        t1 = (exams[0].get('title') or 'Prova 1').strip()
        t2 = (exams[1].get('title') or 'Prova 2').strip()
        exam_titles = f"{t1}  +  {t2}"
    elif len(exams) == 1:
        exam_titles = (exams[0].get('title') or 'Simulado / Avaliação').strip()
    else:
        exam_titles = "Gabaritos Oficiais"

    # Sort students alphabetically by name safely
    valid_students = [s for s in students if isinstance(s, dict)]
    sorted_students = sorted(valid_students, key=lambda s: (s.get("name") or "Aluno").strip().lower())

    left_margin = 36.0
    right_margin = PAGE_WIDTH - 36.0
    content_width = right_margin - left_margin  # 523.275 pt

    # Students pagination: max 28 per page so everything fits with comfortable signature space
    students_per_page = 28
    chunks = [sorted_students[i:i + students_per_page] for i in range(0, max(1, len(sorted_students)), students_per_page)]

    for page_idx, chunk in enumerate(chunks, 1):
        is_last_chunk = (page_idx == len(chunks))

        # --- 1. Institutional Header ---
        y_top = PAGE_HEIGHT - 36.0
        
        # Logo
        if eff_logo and os.path.exists(eff_logo):
            try:
                c.drawImage(eff_logo, left_margin, y_top - 50.0, width=50.0, height=50.0, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        # Header Titles
        c.setFont("Helvetica-Bold", 10.5)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.drawString(left_margin + 58.0, y_top - 12.0, prefeitura_name.upper())

        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(colors.HexColor("#334155"))
        c.drawString(left_margin + 58.0, y_top - 24.0, secretaria_name.upper())

        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(colors.HexColor("#1E293B"))
        c.drawString(left_margin + 58.0, y_top - 36.0, school_name.upper())

        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawString(left_margin + 58.0, y_top - 48.0, f"{state_name} • Ano Letivo 2026")

        # --- 2. Dark Navy Banner ---
        y_banner = y_top - 76.0
        banner_h = 22.0
        c.setFillColor(colors.HexColor("#1E293B"))
        c.rect(left_margin, y_banner, content_width, banner_h, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(colors.white)
        c.drawCentredString(PAGE_WIDTH / 2.0, y_banner + 6.5, "ATA DE FREQUÊNCIA E ENTREGA DE GABARITOS")

        # --- 3. Metadata Box ---
        y_meta = y_banner - 36.0
        meta_h = 32.0
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(0.75)
        c.rect(left_margin, y_meta, content_width, meta_h, fill=1, stroke=1)

        # Meta row 1
        c.setFont("Helvetica-Bold", 8.0)
        c.setFillColor(colors.HexColor("#1E293B"))
        c.drawString(left_margin + 8.0, y_meta + 19.0, f"Turma: {class_name}")

        c.setFont("Helvetica", 8.0)
        c.setFillColor(colors.HexColor("#334155"))
        c.drawString(left_margin + 170.0, y_meta + 19.0, f"Turno: {shift_label}")
        c.drawString(left_margin + 360.0, y_meta + 19.0, f"Total de Alunos: {len(sorted_students)}")

        # Meta row 2
        exam_display = exam_titles if len(exam_titles) <= 55 else (exam_titles[:52] + "...")
        c.drawString(left_margin + 8.0, y_meta + 7.0, f"Avaliação: {exam_display}")
        c.drawString(left_margin + 360.0, y_meta + 7.0, "Data: ____ / ____ / ________")

        # --- 4. Students Table (Columns: Nº, Nome do Aluno, Assinatura) ---
        w_num = 32.0
        w_name = 261.275
        w_sig = 230.0

        y_th = y_meta - 20.0
        th_h = 18.0

        # Table Header
        c.setFillColor(colors.HexColor("#1E293B"))
        c.rect(left_margin, y_th, content_width, th_h, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 8.0)
        c.setFillColor(colors.white)
        c.drawCentredString(left_margin + w_num / 2.0, y_th + 5.5, "Nº")
        c.drawString(left_margin + w_num + 8.0, y_th + 5.5, "NOME DO ALUNO")
        c.drawCentredString(left_margin + w_num + w_name + w_sig / 2.0, y_th + 5.5, "ASSINATURA DO ALUNO")

        # Table Rows
        row_h = 20.0
        curr_y = y_th

        start_num = (page_idx - 1) * students_per_page + 1

        for idx, st in enumerate(chunk):
            curr_y -= row_h
            student_num = start_num + idx
            st_name = (st.get("name") or "ALUNO").strip().upper()

            # Alternating background
            if idx % 2 == 1:
                c.setFillColor(colors.HexColor("#F8FAFC"))
                c.rect(left_margin, curr_y, content_width, row_h, fill=1, stroke=0)

            # Row bottom border
            c.setStrokeColor(colors.HexColor("#E2E8F0"))
            c.setLineWidth(0.5)
            c.line(left_margin, curr_y, right_margin, curr_y)

            # Vertical dividers
            c.line(left_margin + w_num, curr_y, left_margin + w_num, curr_y + row_h)
            c.line(left_margin + w_num + w_name, curr_y, left_margin + w_num + w_name, curr_y + row_h)

            # Cell Nº
            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(colors.HexColor("#475569"))
            c.drawCentredString(left_margin + w_num / 2.0, curr_y + 6.0, str(student_num))

            # Cell Nome do Aluno
            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(colors.HexColor("#0F172A"))
            display_name = st_name if len(st_name) <= 45 else (st_name[:42] + "...")
            c.drawString(left_margin + w_num + 8.0, curr_y + 6.0, display_name)

            # Cell Assinatura: clean line guideline
            c.setStrokeColor(colors.HexColor("#94A3B8"))
            c.setLineWidth(0.5)
            x_sig_start = left_margin + w_num + w_name + 12.0
            x_sig_end = right_margin - 12.0
            c.line(x_sig_start, curr_y + 5.0, x_sig_end, curr_y + 5.0)

        # Outer box for table
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(0.75)
        c.rect(left_margin, curr_y, content_width, y_th + th_h - curr_y, fill=0, stroke=1)

        # --- 5. Footer (Teacher Signature & Counters) ---
        if is_last_chunk:
            y_footer = 42.0
            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(colors.HexColor("#334155"))
            c.drawString(left_margin + 6.0, y_footer + 14.0, "Total de Presentes: (        )       Ausentes: (        )")

            # Signature line for teacher
            x_sig_teacher = left_margin + 260.0
            c.setStrokeColor(colors.HexColor("#64748B"))
            c.setLineWidth(0.8)
            c.line(x_sig_teacher, y_footer + 16.0, right_margin - 6.0, y_footer + 16.0)

            c.setFont("Helvetica", 7.0)
            c.setFillColor(colors.HexColor("#64748B"))
            c.drawCentredString((x_sig_teacher + right_margin - 6.0) / 2.0, y_footer + 4.0, "Assinatura do(a) Professor(a) / Aplicador(a)")

        # Page number indicator
        c.setFont("Helvetica", 6.5)
        c.setFillColor(colors.HexColor("#94A3B8"))
        page_info = f"Lista de Presença • Página {page_idx} de {len(chunks)}"
        c.drawString(left_margin, 20.0, page_info)

        c.showPage()


def generate_classroom_attendance_roster_pdf(
    classroom: dict,
    students: list,
    exams: list,
    logo_path: Optional[str] = None
) -> bytes:
    """
    Gera um PDF contendo unicamente a Ata Oficial de Presença e Entrega de Gabaritos
    para a turma informada (paginado com até 28 alunos por folha A4).
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    render_attendance_roster_page(
        c=c,
        classroom=classroom,
        students=students,
        exams=exams,
        logo_path=logo_path
    )
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_batch_classroom_pdf(
    exam: Optional[dict] = None,
    classroom: dict = None,
    students: list = None,
    sheets_per_page: int = 1,
    logo_path: str = None,
    exams: Optional[List[dict]] = None
) -> bytes:
    """
    Generates a personalized batch PDF containing customized answer sheets
    for all students in a classroom.
    
    ALWAYS includes as Page 1 an official Attendance / Signature Sheet
    (Ata de Presença e Entrega de Prova) with Student Name and Signature columns.
    
    If 2 exams are provided and sheets_per_page == 2:
      For EVERY student, prints Exam 1 on the top half and Exam 2 on the bottom half
      of a single A4 page with an easy-cut dashed line between them.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=pagesizes.A4)

    classroom = classroom or {}
    students = students or []
    school_name = classroom.get("school_name", "") or (exam.get("school_name", "") if exam else "")
    class_name = classroom.get("name", "")
    raw_shift = classroom.get("shift", "MANHÃ").upper()
    shift_label = f"[X] {raw_shift}" if raw_shift else "(  ) MANHÃ       (  ) TARDE"

    effective_exams = exams if (exams and len(exams) > 0) else ([exam] if exam else [])

    # Page 1 (and subsequent if > 28 students): Official Attendance & Signature Roster
    if students:
        render_attendance_roster_page(
            c=c,
            classroom=classroom,
            students=students,
            exams=effective_exams,
            logo_path=logo_path
        )

    # DUAL-EXAM PER STUDENT CASE (User requirement: 2 exams linked + 2 per page)
    if len(effective_exams) == 2 and sheets_per_page == 2:
        ex1, ex2 = effective_exams[0], effective_exams[1]
        half_h = PAGE_HEIGHT / 2.0

        logo1 = logo_path or ex1.get("logo_path")
        if not logo1 or not os.path.exists(logo1):
            logo1 = DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None

        logo2 = logo_path or ex2.get("logo_path")
        if not logo2 or not os.path.exists(logo2):
            logo2 = DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None

        for st in students:
            st_name = f"{st['name']} ({st['registration']})" if st.get('registration') else st['name']
            st_id = st.get("id", "")

            # Top Unit: Exam 1
            render_sheet_unit(
                c, x0=0, y0=half_h, width=PAGE_WIDTH, height=half_h,
                exam_id=ex1["id"],
                title=ex1.get("title", ""),
                subtitle=ex1.get("subtitle", "2º ANO DO ENSINO FUNDAMENTAL"),
                school_name=school_name or ex1.get("school_name", ""),
                student_name=st_name,
                student_id=st_id,
                classroom=class_name,
                shift=shift_label,
                num_questions=ex1.get("num_questions", 20),
                num_alternatives=ex1.get("num_alternatives", 4),
                logo_path=logo1,
                is_compact=True,
                header_color=ex1.get("header_color", "#244061")
            )

            # Middle Cut Line
            c.setStrokeColor(colors.HexColor("#94a3b8"))
            c.setLineWidth(0.8)
            c.setDash([4, 4])
            c.line(16, half_h, PAGE_WIDTH - 16, half_h)
            c.setDash([])
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(colors.HexColor("#64748b"))
            c.drawCentredString(PAGE_WIDTH / 2.0, half_h - 2.5, "✂ - - - - - - - - CORTE AQUI PARA DESTACAR AS DUAS PROVAS DO ALUNO - - - - - - - - ✂")

            # Bottom Unit: Exam 2
            render_sheet_unit(
                c, x0=0, y0=0, width=PAGE_WIDTH, height=half_h,
                exam_id=ex2["id"],
                title=ex2.get("title", ""),
                subtitle=ex2.get("subtitle", "2º ANO DO ENSINO FUNDAMENTAL"),
                school_name=school_name or ex2.get("school_name", ""),
                student_name=st_name,
                student_id=st_id,
                classroom=class_name,
                shift=shift_label,
                num_questions=ex2.get("num_questions", 20),
                num_alternatives=ex2.get("num_alternatives", 4),
                logo_path=logo2,
                is_compact=True,
                header_color=ex2.get("header_color", "#244061")
            )

            c.showPage()

    elif len(effective_exams) >= 2 and sheets_per_page == 1:
        # Multiple exams, but full sheet per exam (1 per page)
        for st in students:
            st_name = f"{st['name']} ({st['registration']})" if st.get('registration') else st['name']
            st_id = st.get("id", "")
            for ex in effective_exams:
                logo_p = logo_path or ex.get("logo_path")
                if not logo_p or not os.path.exists(logo_p):
                    logo_p = DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None

                render_sheet_unit(
                    c, x0=0, y0=0, width=PAGE_WIDTH, height=PAGE_HEIGHT,
                    exam_id=ex["id"],
                    title=ex.get("title", ""),
                    subtitle=ex.get("subtitle", "2º ANO DO ENSINO FUNDAMENTAL"),
                    school_name=school_name or ex.get("school_name", ""),
                    student_name=st_name,
                    student_id=st_id,
                    classroom=class_name,
                    shift=shift_label,
                    num_questions=ex.get("num_questions", 20),
                    num_alternatives=ex.get("num_alternatives", 4),
                    logo_path=logo_p,
                    is_compact=False,
                    header_color=ex.get("header_color", "#244061")
                )
                c.showPage()
    else:
        # Single exam mode
        active_exam = effective_exams[0] if effective_exams else (exam or {})
        title = active_exam.get("title", "")
        subtitle = active_exam.get("subtitle", "2º ANO DO ENSINO FUNDAMENTAL")
        active_school = school_name or active_exam.get("school_name", "")
        num_questions = active_exam.get("num_questions", 20)
        num_alternatives = active_exam.get("num_alternatives", 4)
        active_color = active_exam.get("header_color", "#244061")
        logo_p = logo_path or active_exam.get("logo_path")
        if not logo_p or not os.path.exists(logo_p):
            logo_p = DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None

        if sheets_per_page == 2:
            half_h = PAGE_HEIGHT / 2.0
            # Process in pairs of different students for the same single exam
            for i in range(0, max(1, len(students)), 2):
                st1 = students[i] if i < len(students) else None
                st2 = students[i + 1] if i + 1 < len(students) else None

                # Top Unit
                st1_name = f"{st1['name']} ({st1['registration']})" if (st1 and st1.get('registration')) else (st1['name'] if st1 else "Aluno Avulso")
                st1_id = st1["id"] if st1 else ""
                render_sheet_unit(
                    c, x0=0, y0=half_h, width=PAGE_WIDTH, height=half_h,
                    exam_id=active_exam.get("id", ""), title=title, subtitle=subtitle,
                    school_name=active_school, student_name=st1_name, student_id=st1_id,
                    classroom=class_name, shift=shift_label,
                    num_questions=num_questions, num_alternatives=num_alternatives,
                    logo_path=logo_p, is_compact=True,
                    header_color=active_color
                )

                # Middle Cut Line
                c.setStrokeColor(colors.HexColor("#94a3b8"))
                c.setLineWidth(0.8)
                c.setDash([4, 4])
                c.line(16, half_h, PAGE_WIDTH - 16, half_h)
                c.setDash([])
                c.setFont("Helvetica-Bold", 6.5)
                c.setFillColor(colors.HexColor("#64748b"))
                c.drawCentredString(PAGE_WIDTH / 2.0, half_h - 2.5, "✂ - - - - - - - - CORTE AQUI PARA DESTACAR AS DUAS FOLHAS - - - - - - - - ✂")

                # Bottom Unit
                st2_name = f"{st2['name']} ({st2['registration']})" if (st2 and st2.get('registration')) else (st2['name'] if st2 else "")
                st2_id = st2["id"] if st2 else ""
                render_sheet_unit(
                    c, x0=0, y0=0, width=PAGE_WIDTH, height=half_h,
                    exam_id=active_exam.get("id", ""), title=title, subtitle=subtitle,
                    school_name=active_school, student_name=st2_name, student_id=st2_id,
                    classroom=class_name, shift=shift_label,
                    num_questions=num_questions, num_alternatives=num_alternatives,
                    logo_path=logo_p, is_compact=True,
                    header_color=active_color
                )
                c.showPage()
        else:
            for st in students:
                st_name = f"{st['name']} ({st['registration']})" if st.get('registration') else st['name']
                render_sheet_unit(
                    c, x0=0, y0=0, width=PAGE_WIDTH, height=PAGE_HEIGHT,
                    exam_id=active_exam.get("id", ""), title=title, subtitle=subtitle,
                    school_name=active_school, student_name=st_name, student_id=st["id"],
                    classroom=class_name, shift=shift_label,
                    num_questions=num_questions, num_alternatives=num_alternatives,
                    logo_path=logo_p, is_compact=False,
                    header_color=active_color
                )
                c.showPage()

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_envelope_labels_pdf(
    school: Dict[str, Any],
    classrooms: List[Dict[str, Any]],
    logo_path: Optional[str] = DEFAULT_LOGO_PATH
) -> bytes:
    """
    Gera um PDF em formato A4 contendo etiquetas de envelope para as turmas de uma escola.
    Organizado em grade 4x1 (4 faixas horizontais por folha A4 com guias de recorte).
    Cada etiqueta identifica:
      - Escola e Código INEP
      - Turma, Turno e Quantidade esperada de alunos/gabaritos
      - Lista dos simulados/gabaritos contidos no envelope
      - Seção de conferência e lacre para o aplicador/fiscal
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=pagesizes.A4)

    total_classes = len(classrooms)
    slot_height = PAGE_HEIGHT / 4.0  # 210.47 pt
    margin_x = 18.0
    label_width = PAGE_WIDTH - (2 * margin_x)  # ~559.27 pt
    label_height = 194.0  # ~68.5 mm
    header_height = 25.0

    # Iterar sobre as turmas em blocos de 4 (uma página A4 por bloco)
    for chunk_idx in range(0, total_classes, 4):
        chunk = classrooms[chunk_idx:chunk_idx + 4]

        # Desenhar linhas de corte horizontais da página (entre as 4 faixas)
        for k in range(1, 4):
            cut_y = PAGE_HEIGHT - (k * slot_height)
            c.setStrokeColor(colors.HexColor("#94a3b8"))
            c.setLineWidth(0.7)
            c.setDash([3, 3])
            c.line(10, cut_y, PAGE_WIDTH - 10, cut_y)
            c.setDash([])
            c.setFont("Helvetica-Bold", 6.0)
            c.setFillColor(colors.HexColor("#64748b"))
            c.drawCentredString(PAGE_WIDTH / 2.0, cut_y - 2.0, "✂ - - - - - - - - - - - - - - - - - - - CORTE AQUI - - - - - - - - - - - - - - - - - - - ✂")

        # Desenhar cada etiqueta do bloco
        for slot_k, classroom in enumerate(chunk):
            slot_y0 = PAGE_HEIGHT - ((slot_k + 1) * slot_height)
            label_y0 = slot_y0 + (slot_height - label_height) / 2.0
            label_x0 = margin_x

            # Fundo branco da etiqueta
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.HexColor("#0f172a"))
            c.setLineWidth(1.0)
            c.rect(label_x0, label_y0, label_width, label_height, stroke=1, fill=1)

            # Faixa de cabeçalho da etiqueta (Azul Marinho Escuro / Slate)
            c.setFillColor(colors.HexColor("#1e293b"))
            c.rect(label_x0, label_y0 + label_height - header_height, label_width, header_height, stroke=0, fill=1)

            text_start_x = label_x0 + 10
            if logo_path and os.path.exists(logo_path):
                try:
                    logo_size = 18.0
                    c.drawImage(
                        ImageReader(logo_path),
                        label_x0 + 8,
                        label_y0 + label_height - header_height + (header_height - logo_size) / 2.0,
                        logo_size,
                        logo_size,
                        mask='auto',
                        preserveAspectRatio=True
                    )
                    text_start_x = label_x0 + 31
                except Exception:
                    pass

            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8.0)
            c.drawString(text_start_x, label_y0 + label_height - 16.0, "PREFEITURA MUNICIPAL DE LAGOA DA CANOA • SEMED")
            c.setFont("Helvetica-Bold", 8.5)
            c.drawRightString(label_x0 + label_width - 10, label_y0 + label_height - 16.0, "ENVELOPE DE AVALIAÇÃO / SIMULADO")

            # --- COLUNA 1: IDENTIFICAÇÃO DA ESCOLA E TURMA (Largura ~185 pt) ---
            col1_x = label_x0 + 10.0
            col1_w = 185.0

            # Nome da Escola
            y1 = label_y0 + label_height - header_height - 13.0
            c.setFont("Helvetica-Bold", 6.2)
            c.setFillColor(colors.HexColor("#64748b"))
            c.drawString(col1_x, y1, "UNIDADE ESCOLAR:")

            y1 -= 11.0
            sch_name = (school.get("name") or "Escola").strip()
            font_sz_sch = 8.5
            while font_sz_sch > 6.0 and c.stringWidth(sch_name.upper(), "Helvetica-Bold", font_sz_sch) > col1_w:
                font_sz_sch -= 0.3
            c.setFont("Helvetica-Bold", font_sz_sch)
            c.setFillColor(colors.HexColor("#0f172a"))
            c.drawString(col1_x, y1, sch_name.upper())

            inep = (school.get("inep_code") or "").strip()
            if inep:
                y1 -= 9.0
                c.setFont("Helvetica", 6.8)
                c.setFillColor(colors.HexColor("#64748b"))
                c.drawString(col1_x, y1, f"CÓDIGO INEP: {inep}")

            # Caixa destacada de Turma e Turno
            turma_box_h = 44.0
            turma_box_y = y1 - 8.0 - turma_box_h
            c.setFillColor(colors.HexColor("#f8fafc"))
            c.setStrokeColor(colors.HexColor("#cbd5e1"))
            c.setLineWidth(0.8)
            c.roundRect(col1_x, turma_box_y, col1_w, turma_box_h, radius=3, stroke=1, fill=1)

            # Rótulos no topo da caixa
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(colors.HexColor("#475569"))
            c.drawString(col1_x + 8, turma_box_y + 31, "TURMA:")

            # Turno alinhado à direita no topo da caixa
            shift = (classroom.get("shift") or "Geral").strip()
            if shift:
                c.setFont("Helvetica-Bold", 7.0)
                c.setFillColor(colors.HexColor("#0284c7"))
                c.drawRightString(col1_x + col1_w - 8, turma_box_y + 31, f"TURNO: {shift.upper()}")

            # Nome completo da turma com ajuste dinâmico de fonte para caber 100%
            class_name = (classroom.get("name") or "Turma").strip()
            font_sz_cl = 11.5
            avail_cl_w = col1_w - 16.0
            while font_sz_cl > 6.5 and c.stringWidth(class_name.upper(), "Helvetica-Bold", font_sz_cl) > avail_cl_w:
                font_sz_cl -= 0.3
            c.setFont("Helvetica-Bold", font_sz_cl)
            c.setFillColor(colors.HexColor("#0f172a"))
            c.drawString(col1_x + 8, turma_box_y + 12, class_name.upper())

            # Total de Alunos / Gabaritos Esperados (Alunos x Quantidade de Simulados)
            st_count = classroom.get("student_count") or classroom.get("students_count") or len(classroom.get("students", []))
            linked_exams = classroom.get("linked_exams") or []
            num_exams = len(linked_exams) if linked_exams else 1
            expected_sheets = st_count * num_exams

            y_cnt = turma_box_y - 12.0
            c.setFont("Helvetica-Bold", 6.8)
            c.setFillColor(colors.HexColor("#475569"))
            c.drawString(col1_x, y_cnt, "GABARITOS ESPERADOS NO ENVELOPE:")
            y_cnt -= 11.0
            c.setFont("Helvetica-Bold", 9.0)
            c.setFillColor(colors.HexColor("#047857"))  # Verde floresta
            c.drawString(col1_x, y_cnt, f"➜  {expected_sheets} FOLHAS DE RESPOSTAS")
            if num_exams > 1:
                c.setFont("Helvetica", 6.3)
                c.setFillColor(colors.HexColor("#64748b"))
                c.drawString(col1_x + 14, y_cnt - 8.5, f"({st_count} alunos × {num_exams} cadernos)")

            # Linha Divisória 1
            div1_x = col1_x + col1_w + 7.0
            c.setStrokeColor(colors.HexColor("#e2e8f0"))
            c.setLineWidth(0.8)
            c.line(div1_x, label_y0 + 6, div1_x, label_y0 + label_height - header_height - 6)

            # --- COLUNA 2: CONTEÚDO DO ENVELOPE / GABARITOS (Largura ~195 pt) ---
            col2_x = div1_x + 7.0
            col2_w = 195.0
            y2 = label_y0 + label_height - header_height - 14.0

            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(colors.HexColor("#0f172a"))
            c.drawString(col2_x, y2, "GABARITOS NO ENVELOPE")

            y2 -= 9.5
            c.setFont("Helvetica", 6.5)
            c.setFillColor(colors.HexColor("#64748b"))
            c.drawString(col2_x, y2, "Cadernos de respostas inseridos:")

            y2 -= 13.0

            if linked_exams:
                avail_ew = col2_w - 20.0
                for idx, ex in enumerate(linked_exams[:4]):
                    ex_title = (ex.get("title") or f"Simulado {idx+1}").strip()
                    num_q = ex.get("num_questions")
                    q_info = f" ({num_q} questões)" if num_q else ""

                    # Ajuste de fonte e/ou quebra em 2 linhas para nome completo
                    ex_font_sz = 7.5
                    while ex_font_sz > 6.4 and c.stringWidth(ex_title, "Helvetica-Bold", ex_font_sz) > avail_ew:
                        ex_font_sz -= 0.3

                    if c.stringWidth(ex_title, "Helvetica-Bold", ex_font_sz) <= avail_ew:
                        c.setFont("Helvetica-Bold", ex_font_sz)
                        c.setFillColor(colors.HexColor("#1e293b"))
                        c.drawString(col2_x, y2, f"[ ✓ ] {ex_title}")
                        y2 -= 8.5
                    else:
                        # Quebra em 2 linhas para títulos longos
                        words = ex_title.split(" ")
                        line1, line2 = [], []
                        for w in words:
                            if c.stringWidth(" ".join(line1 + [w]), "Helvetica-Bold", 6.8) <= avail_ew:
                                line1.append(w)
                            else:
                                line2.append(w)
                        c.setFont("Helvetica-Bold", 6.8)
                        c.setFillColor(colors.HexColor("#1e293b"))
                        c.drawString(col2_x, y2, f"[ ✓ ] {' '.join(line1)}")
                        y2 -= 8.0
                        if line2:
                            c.drawString(col2_x + 16, y2, " ".join(line2))
                            y2 -= 8.0

                    if q_info:
                        c.setFont("Helvetica", 6.3)
                        c.setFillColor(colors.HexColor("#64748b"))
                        c.drawString(col2_x + 16, y2, q_info)
                        y2 -= 10.0
                    else:
                        y2 -= 6.0
            else:
                c.setFont("Helvetica", 7.2)
                c.setFillColor(colors.HexColor("#334155"))
                c.drawString(col2_x, y2, "[  ] 1º Simulado: __________________")
                y2 -= 14.0
                c.drawString(col2_x, y2, "[  ] 2º Simulado: __________________")
                y2 -= 14.0
                c.drawString(col2_x, y2, "[  ] Folhas Extras / Reserva")

            # Aviso de manuseio no rodapé da Coluna 2
            c.setFont("Helvetica-Oblique", 6.2)
            c.setFillColor(colors.HexColor("#94a3b8"))
            c.drawString(col2_x, label_y0 + 10.0, "⚠️ Manter as folhas sem rasuras ou dobraduras.")

            # Linha Divisória 2
            div2_x = col2_x + col2_w + 7.0
            c.setStrokeColor(colors.HexColor("#e2e8f0"))
            c.setLineWidth(0.8)
            c.line(div2_x, label_y0 + 6, div2_x, label_y0 + label_height - header_height - 6)

            # --- COLUNA 3: CONTROLE DO APLICADOR & LACRE (Largura ~135 pt) ---
            col3_x = div2_x + 8.0
            y3 = label_y0 + label_height - header_height - 14.0

            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(colors.HexColor("#0f172a"))
            c.drawString(col3_x, y3, "CONTROLE DO APLICADOR")

            y3 -= 13.0
            c.setFont("Helvetica-Bold", 6.8)
            c.setFillColor(colors.HexColor("#475569"))
            c.drawString(col3_x, y3, "Data de Aplicação:")
            y3 -= 9.5
            c.setFont("Helvetica", 7.8)
            c.setFillColor(colors.HexColor("#0f172a"))
            c.drawString(col3_x, y3, "_____ / _____ / _________")

            y3 -= 14.0
            c.setFont("Helvetica-Bold", 6.8)
            c.setFillColor(colors.HexColor("#475569"))
            c.drawString(col3_x, y3, "Professor / Fiscal:")
            y3 -= 9.5
            c.setFont("Helvetica", 7.8)
            c.drawString(col3_x, y3, "___________________________")

            y3 -= 14.0
            c.setFont("Helvetica-Bold", 6.8)
            c.setFillColor(colors.HexColor("#475569"))
            c.drawString(col3_x, y3, "Gabaritos Devolvidos:")
            y3 -= 9.5
            c.setFont("Helvetica", 7.2)
            c.drawString(col3_x, y3, "[  ] Presentes: ___")
            c.drawString(col3_x + 68, y3, "[  ] Ausentes: ___")

            y3 -= 17.0
            c.setFont("Helvetica", 7.5)
            c.drawString(col3_x, y3, "___________________________")
            y3 -= 7.5
            c.setFont("Helvetica", 6.2)
            c.setFillColor(colors.HexColor("#64748b"))
            c.drawString(col3_x + 18, y3, "Visto / Assinatura do Aplicador")

        c.showPage()

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
