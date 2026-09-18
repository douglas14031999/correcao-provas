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
from typing import Optional, List
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
    is_compact: bool = False
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

    # 4. Header Banner (#244061 Navy Blue)
    c.setFillColor(colors.HexColor("#244061"))
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
    if student_name:
        c.setFont("Helvetica", 7.0 if is_compact else 8.5)
        c.drawString(r_left + (60 if is_compact else 70), tbl_top - 2 * row_h + (4.0 if is_compact else 5.5), student_name.upper()[:44])

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
        c.setFillColor(colors.HexColor("#244061"))
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

def get_exam_template_for_layout(exam: dict, is_compact: bool = False) -> dict:
    """
    Returns or dynamically generates the accurate canonical template (single or compact)
    for the specified exam.
    """
    stored_template = exam.get("sheet_template") or {}
    req_h = CANONICAL_HEIGHT_HALF if is_compact else CANONICAL_HEIGHT
    if stored_template.get("canonical_height") == req_h and stored_template.get("bubbles"):
        return stored_template

    if is_compact and exam.get("sheet_template_compact"):
        return exam["sheet_template_compact"]

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
        num_questions=exam.get("num_questions", 20),
        num_alternatives=exam.get("num_alternatives", 4),
        logo_path=exam.get("logo_path"),
        is_compact=is_compact
    )
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
    student_id: str = ""
) -> tuple[bytes, dict]:
    """
    Generates Answer Sheet PDF adhering to the user's requested layout:
    - sheets_per_page = 1: Single full A4 sheet
    - sheets_per_page = 2: Two autonomous A5 half-sheets with scissor cut guide (50% paper economy)
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
            logo_path=logo_path, is_compact=True
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
            logo_path=logo_path, is_compact=True
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
            logo_path=logo_path, is_compact=False
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
        exam_titles = f"{exams[0].get('title', 'Prova 1')}  +  {exams[1].get('title', 'Prova 2')}"
    elif len(exams) == 1:
        exam_titles = exams[0].get('title', 'Simulado / Avaliação')
    else:
        exam_titles = "Gabaritos Oficiais"

    # Sort students alphabetically by name
    sorted_students = sorted(students, key=lambda s: s.get("name", "").lower())

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
            st_name = st.get("name", "").strip().upper()

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
                is_compact=True
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
                is_compact=True
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
                    is_compact=False
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
                    logo_path=logo_p, is_compact=True
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
                    logo_path=logo_p, is_compact=True
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
                    logo_path=logo_p, is_compact=False
                )
                c.showPage()

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
