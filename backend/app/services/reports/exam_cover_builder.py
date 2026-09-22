import os
import cv2
from typing import Optional, List, Dict, Any
from PIL import Image
from reportlab.lib import pagesizes, colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget

# Standard A4: 595.275 x 841.889 pt
PAGE_WIDTH, PAGE_HEIGHT = pagesizes.A4

def mm_to_pt(mm: float) -> float:
    return mm * 2.83465

def get_aruco_img(marker_id: int, size: int = 140) -> Image.Image:
    try:
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        marker_img = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
    except AttributeError:
        dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        marker_img = cv2.aruco.drawMarker(dictionary, marker_id, size)
    return Image.fromarray(marker_img)

ARUCO_IMAGES = {
    0: get_aruco_img(0),
    1: get_aruco_img(1),
    2: get_aruco_img(2),
    3: get_aruco_img(3),
}

THEME_CONFIGS = {
    "opcao_1_montanhas_canoa": {
        "header_bg": "#a5d8ea",
        "pill_bg": "#0e2a47",
        "pill_fg": "#93c5fd",
        "title_color": "#ffffff",
        "bc_top_bg": "#0e2a47",
        "bc_top_fg": "#93c5fd",
        "bc_mid_bg": "#2d5a82",
        "bc_mid_fg": "#ffffff",
        "bc_bot_fg": "#0e2a47",
        "card_accent": "#1d4ed8",
        "instr_bg": "#e0f2fe",
        "instr_border": "#bae6fd",
        "instr_fg": "#0369a1",
        "table_header_bg": "#0e2a47",
        "bubble_color": "#1d4ed8",
        "art_type": "montanhas"
    },
    "opcao_2_rio_verde_petroleo": {
        "header_bg": "#042f2e",
        "pill_bg": "#134e4a",
        "pill_fg": "#5eead4",
        "title_color": "#ffffff",
        "bc_top_bg": "#042f2e",
        "bc_top_fg": "#5eead4",
        "bc_mid_bg": "#0d9488",
        "bc_mid_fg": "#ffffff",
        "bc_bot_fg": "#042f2e",
        "card_accent": "#0d9488",
        "instr_bg": "#ccfbf1",
        "instr_border": "#99f6e4",
        "instr_fg": "#115e59",
        "table_header_bg": "#0f766e",
        "bubble_color": "#0d9488",
        "art_type": "rio"
    },
    "opcao_3_por_do_sol_solar": {
        "header_bg": "#fef3c7",
        "pill_bg": "#7c2d12",
        "pill_fg": "#fed7aa",
        "title_color": "#ffffff",
        "bc_top_bg": "#7c2d12",
        "bc_top_fg": "#fed7aa",
        "bc_mid_bg": "#ea580c",
        "bc_mid_fg": "#ffffff",
        "bc_bot_fg": "#7c2d12",
        "card_accent": "#ea580c",
        "instr_bg": "#ffedd5",
        "instr_border": "#fed7aa",
        "instr_fg": "#9a3412",
        "table_header_bg": "#c2410c",
        "bubble_color": "#ea580c",
        "art_type": "solar"
    },
    "opcao_4_azul_nautico_lagoa": {
        "header_bg": "#0f172a",
        "pill_bg": "#1e3a8a",
        "pill_fg": "#93c5fd",
        "title_color": "#ffffff",
        "bc_top_bg": "#1e3a8a",
        "bc_top_fg": "#93c5fd",
        "bc_mid_bg": "#2563eb",
        "bc_mid_fg": "#ffffff",
        "bc_bot_fg": "#1e3a8a",
        "card_accent": "#2563eb",
        "instr_bg": "#eff6ff",
        "instr_border": "#bfdbfe",
        "instr_fg": "#1e40af",
        "table_header_bg": "#1e3a8a",
        "bubble_color": "#2563eb",
        "art_type": "nautico"
    }
}

def draw_top_artwork(c: canvas.Canvas, theme_id: str):
    cfg = THEME_CONFIGS.get(theme_id, THEME_CONFIGS["opcao_4_azul_nautico_lagoa"])
    art_h = mm_to_pt(80)
    art_y = PAGE_HEIGHT - art_h
    art_w = PAGE_WIDTH

    c.saveState()
    c.setFillColor(colors.HexColor(cfg["header_bg"]))
    c.rect(0, art_y, art_w, art_h, stroke=0, fill=1)

    art_type = cfg["art_type"]

    if art_type == "montanhas":
        sx = art_w / 800.0
        sy = art_h / 290.0

        def to_pt(x, y_svg):
            return x * sx, art_y + (290 - y_svg) * sy

        # Back mountain: fill #437b9b
        p1 = [(0, 190), (150, 80), (300, 200), (440, 60), (590, 190), (700, 105), (800, 190), (800, 290), (0, 290)]
        path1 = c.beginPath()
        x0, y0 = to_pt(p1[0][0], p1[0][1])
        path1.moveTo(x0, y0)
        for pt in p1[1:]:
            xi, yi = to_pt(pt[0], pt[1])
            path1.lineTo(xi, yi)
        path1.close()
        c.setFillColor(colors.HexColor("#437b9b"))
        c.drawPath(path1, stroke=0, fill=1)

        # Front mountain: fill #0e2a47
        p2 = [(0, 230), (120, 135), (260, 235), (420, 120), (560, 230), (680, 150), (800, 235), (800, 290), (0, 290)]
        path2 = c.beginPath()
        x0, y0 = to_pt(p2[0][0], p2[0][1])
        path2.moveTo(x0, y0)
        for pt in p2[1:]:
            xi, yi = to_pt(pt[0], pt[1])
            path2.lineTo(xi, yi)
        path2.close()
        c.setFillColor(colors.HexColor("#0e2a47"))
        c.drawPath(path2, stroke=0, fill=1)

        # Wave: fill #e2f3f8
        c.setFillColor(colors.HexColor("#e2f3f8"))
        path_w = c.beginPath()
        path_w.moveTo(0, art_y)
        path_w.lineTo(0, art_y + 30 * sy)
        path_w.curveTo(220 * sx, art_y + 58 * sy, 400 * sx, art_y + 30 * sy, 800 * sx, art_y + 30 * sy)
        path_w.lineTo(800 * sx, art_y)
        path_w.close()
        c.drawPath(path_w, stroke=0, fill=1)

        # Golden canoe: fill #f59e0b
        c.setFillColor(colors.HexColor("#f59e0b"))
        path_c = c.beginPath()
        path_c.moveTo(330 * sx, art_y + 40 * sy)
        path_c.curveTo(400 * sx, art_y + 20 * sy, 400 * sx, art_y + 20 * sy, 470 * sx, art_y + 40 * sy)
        path_c.curveTo(400 * sx, art_y + 30 * sy, 400 * sx, art_y + 30 * sy, 330 * sx, art_y + 40 * sy)
        path_c.close()
        c.drawPath(path_c, stroke=0, fill=1)

    elif art_type == "solar":
        # Sun disk top right
        c.setFillColor(colors.HexColor("#f59e0b"))
        c.circle(art_w * 0.72, art_y + art_h * 0.75, mm_to_pt(28), stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#fbbf24"))
        c.circle(art_w * 0.72, art_y + art_h * 0.75, mm_to_pt(20), stroke=0, fill=1)

        # Dunes
        c.setFillColor(colors.HexColor("#fb923c"))
        p1 = c.beginPath()
        p1.moveTo(0, art_y)
        p1.lineTo(0, art_y + art_h * 0.45)
        p1.curveTo(art_w * 0.35, art_y + art_h * 0.60, art_w * 0.70, art_y + art_h * 0.35, art_w, art_y + art_h * 0.50)
        p1.lineTo(art_w, art_y)
        p1.close()
        c.drawPath(p1, stroke=0, fill=1)

        c.setFillColor(colors.HexColor("#ea580c"))
        p2 = c.beginPath()
        p2.moveTo(0, art_y)
        p2.lineTo(0, art_y + art_h * 0.30)
        p2.curveTo(art_w * 0.40, art_y + art_h * 0.42, art_w * 0.65, art_y + art_h * 0.20, art_w, art_y + art_h * 0.32)
        p2.lineTo(art_w, art_y)
        p2.close()
        c.drawPath(p2, stroke=0, fill=1)

        c.setFillColor(colors.HexColor("#c2410c"))
        p3 = c.beginPath()
        p3.moveTo(0, art_y)
        p3.lineTo(0, art_y + art_h * 0.16)
        p3.curveTo(art_w * 0.30, art_y + art_h * 0.22, art_w * 0.75, art_y + art_h * 0.08, art_w, art_y + art_h * 0.16)
        p3.lineTo(art_w, art_y)
        p3.close()
        c.drawPath(p3, stroke=0, fill=1)

        # Small canoe with sail
        cx = art_w * 0.50
        cy = art_y + art_h * 0.17
        c.setFillColor(colors.white)
        ps = c.beginPath()
        ps.moveTo(cx, cy)
        ps.lineTo(cx, cy + mm_to_pt(7))
        ps.lineTo(cx + mm_to_pt(4.5), cy + mm_to_pt(4.5))
        ps.close()
        c.drawPath(ps, stroke=0, fill=1)

        c.setFillColor(colors.HexColor("#78350f"))
        pc = c.beginPath()
        pc.moveTo(cx - mm_to_pt(10), cy)
        pc.curveTo(cx, cy - mm_to_pt(2.5), cx, cy - mm_to_pt(2.5), cx + mm_to_pt(10), cy)
        pc.curveTo(cx, cy - mm_to_pt(1.0), cx, cy - mm_to_pt(1.0), cx - mm_to_pt(10), cy)
        pc.close()
        c.drawPath(pc, stroke=0, fill=1)

    elif art_type == "rio":
        c.setFillColor(colors.HexColor("#0f766e"))
        p1 = c.beginPath()
        p1.moveTo(0, art_y)
        p1.lineTo(0, art_y + art_h * 0.55)
        p1.curveTo(art_w * 0.35, art_y + art_h * 0.70, art_w * 0.70, art_y + art_h * 0.40, art_w, art_y + art_h * 0.60)
        p1.lineTo(art_w, art_y)
        p1.close()
        c.drawPath(p1, stroke=0, fill=1)

        c.setFillColor(colors.HexColor("#0d9488"))
        p2 = c.beginPath()
        p2.moveTo(0, art_y)
        p2.lineTo(0, art_y + art_h * 0.35)
        p2.curveTo(art_w * 0.30, art_y + art_h * 0.48, art_w * 0.65, art_y + art_h * 0.22, art_w, art_y + art_h * 0.38)
        p2.lineTo(art_w, art_y)
        p2.close()
        c.drawPath(p2, stroke=0, fill=1)

        c.setFillColor(colors.HexColor("#14b8a6"))
        p3 = c.beginPath()
        p3.moveTo(0, art_y)
        p3.lineTo(0, art_y + art_h * 0.18)
        p3.curveTo(art_w * 0.45, art_y + art_h * 0.26, art_w * 0.75, art_y + art_h * 0.10, art_w, art_y + art_h * 0.18)
        p3.lineTo(art_w, art_y)
        p3.close()
        c.drawPath(p3, stroke=0, fill=1)

    else: # nautico
        c.setFillColor(colors.HexColor("#1e3a8a"))
        p1 = c.beginPath()
        p1.moveTo(0, art_y)
        p1.lineTo(0, art_y + art_h * 0.55)
        p1.curveTo(art_w * 0.35, art_y + art_h * 0.70, art_w * 0.70, art_y + art_h * 0.40, art_w, art_y + art_h * 0.60)
        p1.lineTo(art_w, art_y)
        p1.close()
        c.drawPath(p1, stroke=0, fill=1)

        c.setFillColor(colors.HexColor("#2563eb"))
        p2 = c.beginPath()
        p2.moveTo(0, art_y)
        p2.lineTo(0, art_y + art_h * 0.35)
        p2.curveTo(art_w * 0.30, art_y + art_h * 0.48, art_w * 0.65, art_y + art_h * 0.22, art_w, art_y + art_h * 0.38)
        p2.lineTo(art_w, art_y)
        p2.close()
        c.drawPath(p2, stroke=0, fill=1)

        c.setFillColor(colors.HexColor("#38bdf8"))
        p3 = c.beginPath()
        p3.moveTo(0, art_y)
        p3.lineTo(0, art_y + art_h * 0.18)
        p3.curveTo(art_w * 0.45, art_y + art_h * 0.26, art_w * 0.75, art_y + art_h * 0.10, art_w, art_y + art_h * 0.18)
        p3.lineTo(art_w, art_y)
        p3.close()
        c.drawPath(p3, stroke=0, fill=1)

    c.restoreState()

def render_native_cover_page(
    c: canvas.Canvas,
    exam: Dict[str, Any],
    student: Dict[str, Any],
    classroom: Dict[str, Any],
    model_override: Optional[str] = None
):
    """
    Renders an official vector-based exam cover with 100% visual fidelity matching the
    chosen template (montanhas, rio, solar, nautico), ArUco markers, OMR bubble grid,
    3-tier Caderno badge, student identification card, and dynamic QR Code.
    """
    eff_model = model_override or exam.get("cover_model") or "opcao_4_azul_nautico_lagoa"
    eff_model = str(eff_model).strip().replace(".html", "")
    cfg = THEME_CONFIGS.get(eff_model, THEME_CONFIGS["opcao_4_azul_nautico_lagoa"])

    school_name = (classroom.get("school_name") or exam.get("school_name") or "SEMED LAGOA DA CANOA").upper()
    student_name = (student.get("name") or "ESTUDANTE").upper()
    class_name = (classroom.get("name") or exam.get("classroom") or "TURMA").upper()
    raw_shift = (classroom.get("shift") or exam.get("shift") or "MATUTINO").upper()
    if raw_shift.startswith("( "):
        shift = "MANHÃ" if "MANHÃ" in raw_shift else "TARDE"
    elif "MATUTINO" in raw_shift or "MANHÃ" in raw_shift:
        shift = "MANHÃ"
    elif "VESPERTINO" in raw_shift or "TARDE" in raw_shift:
        shift = "TARDE"
    else:
        shift = raw_shift

    exam_title = (exam.get("cover_title") or exam.get("title") or "PROVA CANOA").upper()
    from app.services.cover_batch_generator import extract_exam_discipline
    discipline = extract_exam_discipline(exam)
    num_questions = max(1, int(exam.get("num_questions") or 22))
    num_alternatives = max(2, min(5, int(exam.get("num_alternatives") or 4)))

    # 1. Top Artwork
    draw_top_artwork(c, eff_model)

    # 2. Top-Left Brand (2026 Pill + Exam Title)
    top_x = mm_to_pt(16)
    c.saveState()
    pill_y = PAGE_HEIGHT - mm_to_pt(18)
    pill_w, pill_h = mm_to_pt(20), mm_to_pt(6.5)
    c.setFillColor(colors.HexColor(cfg["pill_bg"]))
    c.roundRect(top_x, pill_y, pill_w, pill_h, mm_to_pt(3.2), stroke=0, fill=1)
    c.setFillColor(colors.HexColor(cfg["pill_fg"]))
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(top_x + pill_w / 2.0, pill_y + mm_to_pt(1.8), "2026")

    c.setFillColor(colors.HexColor(cfg["title_color"]))
    c.setFont("Helvetica-Bold", 19)
    c.drawString(top_x, pill_y - mm_to_pt(8.5), exam_title[:28])
    c.restoreState()

    # 3. Top-Right Caderno Badge (3-Tier)
    badge_w = mm_to_pt(48)
    badge_x = PAGE_WIDTH - mm_to_pt(16) - badge_w
    badge_y = PAGE_HEIGHT - mm_to_pt(32)
    h_top, h_mid, h_bot = mm_to_pt(6.5), mm_to_pt(7.5), mm_to_pt(6.5)
    total_badge_h = h_top + h_mid + h_bot

    c.saveState()
    # Shadow / Border
    c.setFillColor(colors.white)
    c.roundRect(badge_x, badge_y, badge_w, total_badge_h, mm_to_pt(3), stroke=0, fill=1)

    # Top tier: CADERNO
    c.setFillColor(colors.HexColor(cfg["bc_top_bg"]))
    c.roundRect(badge_x, badge_y + h_mid + h_bot, badge_w, h_top, mm_to_pt(3), stroke=0, fill=1)
    c.rect(badge_x, badge_y + h_mid + h_bot, badge_w, mm_to_pt(2), stroke=0, fill=1)
    c.setFillColor(colors.HexColor(cfg["bc_top_fg"]))
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(badge_x + badge_w / 2.0, badge_y + h_mid + h_bot + mm_to_pt(1.8), "C A D E R N O")

    # Mid tier: DISCIPLINA
    c.setFillColor(colors.HexColor(cfg["bc_mid_bg"]))
    c.rect(badge_x, badge_y + h_bot, badge_w, h_mid, stroke=0, fill=1)
    c.setFillColor(colors.HexColor(cfg["bc_mid_fg"]))
    disc_font_size = 9 if len(discipline) <= 12 else (7.5 if len(discipline) <= 16 else 6.5)
    c.setFont("Helvetica-Bold", disc_font_size)
    c.drawCentredString(badge_x + badge_w / 2.0, badge_y + h_bot + mm_to_pt(2.2), discipline)

    # Bot tier: TURMA
    c.setFillColor(colors.white)
    c.roundRect(badge_x, badge_y, badge_w, h_bot, mm_to_pt(3), stroke=0, fill=1)
    c.rect(badge_x, badge_y + h_bot - mm_to_pt(2), badge_w, mm_to_pt(2), stroke=0, fill=1)
    c.setFillColor(colors.HexColor(cfg["bc_bot_fg"]))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(badge_x + badge_w / 2.0, badge_y + mm_to_pt(1.8), class_name[:20])
    c.restoreState()

    # 4. Student Card (Middle Area)
    card_x = mm_to_pt(12)
    card_w = PAGE_WIDTH - card_x * 2
    card_h = mm_to_pt(46)
    card_y = PAGE_HEIGHT - mm_to_pt(80) - card_h

    c.saveState()
    # White card with light border
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.setLineWidth(1.0)
    c.roundRect(card_x, card_y, card_w, card_h, mm_to_pt(3.5), stroke=1, fill=1)

    # Left colored accent bar
    c.setFillColor(colors.HexColor(cfg["card_accent"]))
    c.roundRect(card_x, card_y, mm_to_pt(3.5), card_h, mm_to_pt(3.5), stroke=0, fill=1)
    c.rect(card_x + mm_to_pt(2), card_y, mm_to_pt(1.5), card_h, stroke=0, fill=1)

    # Header text inside card
    c.setFont("Helvetica-Bold", 7.0)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(card_x + mm_to_pt(8), card_y + card_h - mm_to_pt(5.5), f"DADOS DO(A) ESTUDANTE • {exam_title} • {discipline}")

    # Field 1: Unidade Escolar
    f1_y = card_y + card_h - mm_to_pt(16.5)
    f1_h = mm_to_pt(8.5)
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(0.8)
    c.roundRect(card_x + mm_to_pt(8), f1_y, card_w - mm_to_pt(16), f1_h, mm_to_pt(1.8), stroke=1, fill=1)
    c.setFont("Helvetica-Bold", 5.5)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(card_x + mm_to_pt(11), f1_y + f1_h - mm_to_pt(3.0), "UNIDADE ESCOLAR:")
    c.setFont("Helvetica-Bold", 8.0)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(card_x + mm_to_pt(11), f1_y + mm_to_pt(1.6), school_name[:52])

    # Field 2: Nome Completo do(a) Estudante
    f2_y = f1_y - mm_to_pt(10.5)
    f2_h = mm_to_pt(9.5)
    c.setFillColor(colors.HexColor("#f1f5f9"))
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.roundRect(card_x + mm_to_pt(8), f2_y, card_w - mm_to_pt(16), f2_h, mm_to_pt(1.8), stroke=1, fill=1)
    c.setFont("Helvetica-Bold", 5.5)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(card_x + mm_to_pt(11), f2_y + f2_h - mm_to_pt(3.2), "NOME COMPLETO DO(A) ESTUDANTE:")
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(colors.HexColor("#0b192c"))
    c.drawString(card_x + mm_to_pt(11), f2_y + mm_to_pt(1.8), student_name[:48])

    # Field 3: Turma e Turno (Dual Row)
    f3_y = f2_y - mm_to_pt(9.5)
    f3_h = mm_to_pt(8.5)
    half_w = (card_w - mm_to_pt(16) - mm_to_pt(4)) / 2.0

    # Turma
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.roundRect(card_x + mm_to_pt(8), f3_y, half_w, f3_h, mm_to_pt(1.8), stroke=1, fill=1)
    c.setFont("Helvetica-Bold", 5.5)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(card_x + mm_to_pt(11), f3_y + f3_h - mm_to_pt(3.0), "TURMA:")
    c.setFont("Helvetica-Bold", 8.0)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(card_x + mm_to_pt(11), f3_y + mm_to_pt(1.6), class_name[:26])

    # Turno
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.roundRect(card_x + mm_to_pt(8) + half_w + mm_to_pt(4), f3_y, half_w, f3_h, mm_to_pt(1.8), stroke=1, fill=1)
    c.setFont("Helvetica-Bold", 5.5)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(card_x + mm_to_pt(11) + half_w + mm_to_pt(4), f3_y + f3_h - mm_to_pt(3.0), "TURNO:")
    c.setFont("Helvetica-Bold", 8.0)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(card_x + mm_to_pt(11) + half_w + mm_to_pt(4), f3_y + mm_to_pt(1.6), shift[:18])
    c.restoreState()

    # 5. Bottom Reading Area (135mm to 289mm from top -> y from mm_to_pt(8) to mm_to_pt(162))
    read_x = mm_to_pt(8)
    read_y = mm_to_pt(8)
    read_w = PAGE_WIDTH - read_x * 2
    read_h = mm_to_pt(154)

    # 5.1 Draw the 4 ArUco markers at the 4 corners of Reading Area
    m_size = mm_to_pt(14)
    # TL: marker 0
    tl_x = read_x + mm_to_pt(2)
    tl_y = read_y + read_h - mm_to_pt(2) - m_size
    c.drawInlineImage(ARUCO_IMAGES[0], tl_x, tl_y, m_size, m_size)

    # TR: marker 1
    tr_x = read_x + read_w - mm_to_pt(2) - m_size
    tr_y = tl_y
    c.drawInlineImage(ARUCO_IMAGES[1], tr_x, tr_y, m_size, m_size)

    # BL: marker 3
    bl_x = tl_x
    bl_y = read_y + mm_to_pt(2)
    c.drawInlineImage(ARUCO_IMAGES[3], bl_x, bl_y, m_size, m_size)

    # BR: marker 2
    br_x = tr_x
    br_y = bl_y
    c.drawInlineImage(ARUCO_IMAGES[2], br_x, br_y, m_size, m_size)

    # 5.2 Instructions Bar between TL and TR markers
    instr_x = read_x + mm_to_pt(18)
    instr_w = read_w - mm_to_pt(36)
    instr_h = mm_to_pt(6.5)
    instr_y = tl_y + mm_to_pt(3.5)

    c.saveState()
    c.setFillColor(colors.HexColor(cfg["instr_bg"]))
    c.setStrokeColor(colors.HexColor(cfg["instr_border"]))
    c.setLineWidth(0.8)
    c.roundRect(instr_x, instr_y, instr_w, instr_h, mm_to_pt(1.8), stroke=1, fill=1)

    c.setFont("Helvetica-Bold", 6.8)
    c.setFillColor(colors.HexColor(cfg["instr_fg"]))
    c.drawString(instr_x + mm_to_pt(3.5), instr_y + mm_to_pt(2.0), "ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.")
    c.drawRightString(instr_x + instr_w - mm_to_pt(3.5), instr_y + mm_to_pt(2.0), "CORRETO: [ ● ]  ERRADO: [ × ] [ / ]")
    c.restoreState()

    # 5.3 OMR Question Tables
    table_top_y = instr_y - mm_to_pt(4)
    col_w = mm_to_pt(72)
    gap_cols = mm_to_pt(6)
    col1_x = read_x + mm_to_pt(8)
    col2_x = col1_x + col_w + gap_cols

    opts = ["A", "B", "C", "D", "E"][:num_alternatives]
    row_h = mm_to_pt(7.8)
    col1_end_q = min(12, num_questions)

    def draw_omr_column(start_x, start_q, end_q):
        if start_q > end_q:
            return
        # Header Row
        c.setFillColor(colors.HexColor(cfg["table_header_bg"]))
        c.rect(start_x, table_top_y - row_h, col_w, row_h, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7.5)
        item_w = mm_to_pt(14)
        c.drawCentredString(start_x + item_w / 2.0, table_top_y - row_h + mm_to_pt(2.4), "ITEM")

        opt_w = (col_w - item_w) / len(opts)
        for i, opt in enumerate(opts):
            c.drawCentredString(start_x + item_w + i * opt_w + opt_w / 2.0, table_top_y - row_h + mm_to_pt(2.4), opt)

        # Question Rows
        c.setFont("Helvetica-Bold", 7.5)
        for q_idx, q_num in enumerate(range(start_q, end_q + 1)):
            qy = table_top_y - (q_idx + 2) * row_h
            # Row border
            c.setStrokeColor(colors.HexColor("#e2e8f0"))
            c.setLineWidth(0.6)
            c.line(start_x, qy, start_x + col_w, qy)

            # Item number
            c.setFillColor(colors.HexColor("#0f172a"))
            c.drawString(start_x + mm_to_pt(4.5), qy + mm_to_pt(2.2), f"{q_num:02d}")

            # Bubbles with letters inside
            for i, opt in enumerate(opts):
                bx = start_x + item_w + i * opt_w + opt_w / 2.0
                by = qy + row_h / 2.0
                bubble_r = mm_to_pt(2.2)

                # Outer circle stroke
                c.setStrokeColor(colors.HexColor(cfg["bubble_color"]))
                c.setFillColor(colors.white)
                c.setLineWidth(0.8)
                c.circle(bx, by, bubble_r, stroke=1, fill=1)

                # Letter inside bubble
                c.setFillColor(colors.HexColor(cfg["bubble_color"]))
                c.setFont("Helvetica-Bold", 5.8)
                c.drawCentredString(bx, by - mm_to_pt(1.0), opt)

    draw_omr_column(col1_x, 1, col1_end_q)
    if num_questions >= 13:
        draw_omr_column(col2_x, 13, min(24, num_questions))

    # 5.4 Student QR Code at bottom-right
    qr_x = read_x + read_w - mm_to_pt(18) - mm_to_pt(24)
    qr_y = bl_y + mm_to_pt(1.5)
    qr_size = mm_to_pt(24)

    exam_id_short = exam.get("id", "")
    student_id_short = student.get("id", "")
    qr_payload = f"E:{exam_id_short}|S:{student_id_short}"

    qr_widget = QrCodeWidget(qr_payload)
    qr_widget.barWidth = qr_size
    qr_widget.barHeight = qr_size
    qr_widget.barBorder = 1
    d = Drawing(qr_size, qr_size)
    d.add(qr_widget)
    d.drawOn(c, qr_x, qr_y)

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
    num_alternatives: int = 4,
    student_name: str = "",
    student_birth_date: str = "",
    tracking_code: str = "4454197329",
    caderno_accent_color: str = "#1e3a8a",
    school_name: str = "",
    classroom_name: str = "",
    shift: str = "MATUTINO",
    model_id: Optional[str] = "opcao_4_azul_nautico_lagoa"
) -> str:
    """Helper method creating a single cover file using the native official vector renderer."""
    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
    c = canvas.Canvas(output_pdf_path, pagesize=pagesizes.A4)

    exam_dict = {
        "id": tracking_code,
        "cover_model": model_id,
        "cover_title": " ".join(main_title_lines) if main_title_lines else "PROVA CANOA",
        "discipline": discipline,
        "num_questions": num_questions,
        "num_alternatives": num_alternatives,
    }
    student_dict = {
        "id": tracking_code,
        "name": student_name
    }
    classroom_dict = {
        "school_name": school_name,
        "name": classroom_name or grade_stage,
        "shift": shift
    }

    render_native_cover_page(c, exam=exam_dict, student=student_dict, classroom=classroom_dict, model_override=model_id)
    c.save()
    return output_pdf_path
