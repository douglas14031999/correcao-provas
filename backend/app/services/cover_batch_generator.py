import os
import io
import re
import uuid
import base64
import tempfile
import subprocess
import shutil
import qrcode
from typing import List, Dict, Any, Optional
import pymupdf as fitz

SHEETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage", "sheets"
)

def get_chrome_executable() -> Optional[str]:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        "google-chrome",
        "chromium-browser",
        "chromium",
        "chrome"
    ]
    for p in candidates:
        if os.path.isabs(p) and os.path.exists(p):
            return p
        elif not os.path.isabs(p) and shutil.which(p):
            return shutil.which(p)
    return None

import functools

def make_qr_base64(data: str) -> str:
    """Generates crisp QR code PNG as base64 string with optimized dimensions."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=5,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

@functools.lru_cache(maxsize=32)
def build_table_html(num_questions: int = 22, num_alternatives: int = 4, header_bg: str = "#1e3a8a") -> str:
    """Builds calibrated OMR question tables for the cover sheet (cached for instant reuse)."""
    options = ["A", "B", "C", "D", "E"][:num_alternatives]
    
    col1_max = min(12, num_questions)
    col2_start = 13
    col2_max = min(24, num_questions)

    def render_col(start_q: int, end_q: int) -> str:
        if start_q > end_q:
            return ""
        th_opts = "".join([f'<th class="th-opt">{opt}</th>' for opt in options])
        h = f'<table class="omr-table"><thead><tr><th class="th-item" style="background: {header_bg};">ITEM</th>{th_opts}</tr></thead><tbody>'
        for q in range(start_q, end_q + 1):
            td_opts = "".join([f'<td class="td-opt"><span class="bubble">{opt}</span></td>' for opt in options])
            h += f'<tr data-q="{q}"><td class="td-item">{q:02d}</td>{td_opts}</tr>'
        h += "</tbody></table>"
        return h

    col1_html = render_col(1, col1_max)
    col2_html = render_col(col2_start, col2_max) if num_questions >= col2_start else ""

    return f"""
    <div class="omr-tables-container">
        <div class="omr-col-wrap">{col1_html}</div>
        <div class="omr-col-wrap">{col2_html}</div>
    </div>
    """

@functools.lru_cache(maxsize=16)
def get_cover_template_html(model_id: str) -> str:
    """Reads base template HTML for the chosen cover model (cached in RAM)."""
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '', model_id)
    if not safe_name.endswith(".html"):
        safe_name += ".html"
    
    file_path = os.path.join(SHEETS_DIR, safe_name)
    if not os.path.exists(file_path):
        file_path = os.path.join(SHEETS_DIR, "opcao_4_azul_nautico_lagoa.html")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_exam_discipline(exam: Dict[str, Any]) -> str:
    """
    Extracts or detects the academic discipline/subject from the exam metadata
    (title, cover_subtitle, or explicit discipline field).
    """
    if not exam:
        return ""
    explicit = exam.get("discipline")
    if explicit and str(explicit).strip():
        return str(explicit).strip().upper()
    cover_sub = (exam.get("cover_subtitle") or "").strip()
    search_text = f"{exam.get('title', '')} {cover_sub}".upper()
    if any(k in search_text for k in ["LÍNGUA PORTUGUESA", "LINGUA PORTUGUESA", "PORTUGUÊS", "PORTUGUES"]):
        return "LÍNGUA PORTUGUESA"
    if any(k in search_text for k in ["MATEMÁTICA", "MATEMATICA"]):
        return "MATEMÁTICA"
    if any(k in search_text for k in ["CIÊNCIAS DA NATUREZA", "CIENCIAS DA NATUREZA"]):
        return "CIÊNCIAS DA NATUREZA"
    if any(k in search_text for k in ["CIÊNCIAS", "CIENCIAS"]):
        return "CIÊNCIAS"
    if any(k in search_text for k in ["HISTÓRIA", "HISTORIA"]):
        return "HISTÓRIA"
    if "GEOGRAFIA" in search_text:
        return "GEOGRAFIA"
    if any(k in search_text for k in ["CIÊNCIAS HUMANAS", "CIENCIAS HUMANAS"]):
        return "CIÊNCIAS HUMANAS"
    if any(k in search_text for k in ["INGLÊS", "INGLES"]):
        return "INGLÊS"
    if any(k in search_text for k in ["ARTES", "ARTE"]):
        return "ARTES"
    if any(k in search_text for k in ["REDAÇÃO", "REDACAO"]):
        return "REDAÇÃO"
    if any(k in search_text for k in ["ALFABETIZAÇÃO", "ALFABETIZACAO"]):
        return "ALFABETIZAÇÃO"
    if cover_sub and not re.search(r'^\d+[º°ªa]?\s*ano', cover_sub, re.IGNORECASE):
        return cover_sub.upper()
    parts = re.split(r'[–\-\:]', exam.get('title', ''))
    if len(parts) > 1:
        candidate = parts[-1].strip().upper()
        if candidate and not re.search(r'^\d+[º°ªa]?\s*ano', candidate, re.IGNORECASE) and len(candidate) <= 25:
            return candidate
    return (exam.get("subtitle") or "AVALIAÇÃO").upper()

def render_single_cover_html(
    exam: Dict[str, Any],
    student: Dict[str, Any],
    classroom: Dict[str, Any]
) -> str:
    """Populates template HTML with exam and student metadata."""
    model_id = exam.get("cover_model") or "opcao_4_azul_nautico_lagoa"
    content = get_cover_template_html(model_id)
    
    school_name = (classroom.get("school_name") or exam.get("school_name") or "SEMED LAGOA DA CANOA").upper()
    student_name = (student.get("name") or "ESTUDANTE").upper()
    class_name = (classroom.get("name") or exam.get("classroom") or "TURMA").upper()
    shift = (classroom.get("shift") or exam.get("shift") or "MATUTINO").upper()
    if shift.startswith("( "):
        shift = "MATUTINO" if "MANHÃ" in shift else "VESPERTINO"
    
    exam_title = (exam.get("cover_title") or exam.get("title") or "PROVA CANOA").upper()
    discipline = extract_exam_discipline(exam)
    
    num_questions = int(exam.get("num_questions", 22))
    num_alternatives = int(exam.get("num_alternatives", 4))

    # Header color per model
    header_colors = {
        "opcao_1_montanhas_canoa": "#0e2a47",
        "opcao_2_rio_verde_petroleo": "#0b5d5c",
        "opcao_3_por_do_sol_solar": "#c2410c",
        "opcao_4_azul_nautico_lagoa": "#1e3a8a"
    }
    base_color = header_colors.get(model_id, "#1e3a8a")

    # 1. Update Title and Brand
    content = re.sub(
        r'<div class="titulo-prova">[^<]*</div>',
        f'<div class="titulo-prova">{exam_title}</div>',
        content
    )

    # 2. Update Badge Caderno (3-tier: CADERNO / DISCIPLINA / TURMA)
    if len(discipline) > 13:
        mid_style = 'style="font-size: 9px; letter-spacing: 0.5px; padding: 2.8mm 1mm; line-height: 1.1;"'
    elif len(discipline) > 10:
        mid_style = 'style="font-size: 10px; letter-spacing: 0.8px; padding: 2.5mm 1mm;"'
    else:
        mid_style = ''

    content = re.sub(
        r'<div class="bc-mid"[^>]*>[^<]*</div>',
        f'<div class="bc-mid" {mid_style}>{discipline}</div>',
        content
    )
    if class_name:
        content = re.sub(
            r'<div class="bc-bot"[^>]*>[^<]*</div>',
            f'<div class="bc-bot">{class_name}</div>',
            content
        )

    # 3. Update Student Card Header
    card_header_text = f"DADOS DO(A) ESTUDANTE &bull; {exam_title} &bull; {discipline}"
    content = re.sub(
        r'<div class="student-card-header">[^<]*</div>',
        f'<div class="student-card-header">{card_header_text}</div>',
        content
    )

    # 4. Replace Student Card Field values
    content = re.sub(
        r'(<span class="field-lbl">Unidade Escolar:</span>\s*<span class="field-txt">)[^<]*(</span>)',
        rf'\g<1>{school_name}\g<2>',
        content
    )
    content = re.sub(
        r'(<span class="field-lbl">Nome Completo do\(a\) Estudante:</span>\s*<span class="field-txt name">)[^<]*(</span>)',
        rf'\g<1>{student_name}\g<2>',
        content
    )
    content = re.sub(
        r'(<span class="field-lbl">Turma:</span>\s*<span class="field-txt">)[^<]*(</span>)',
        rf'\g<1>{class_name}\g<2>',
        content
    )
    content = re.sub(
        r'(<span class="field-lbl">Turno:</span>\s*<span class="field-txt">)[^<]*(</span>)',
        rf'\g<1>{shift}\g<2>',
        content
    )

    # 5. Inject Dynamic OMR Question Table
    table_markup = build_table_html(num_questions, num_alternatives, header_bg=base_color)
    content = re.sub(
        r'<div class="omr-tables-container">[\s\S]*?</div>\s*</div>\s*<div class="scan-qr-box">',
        f'{table_markup}\n    <div class="scan-qr-box">',
        content
    )

    # 6. Generate and Inject Student QR Code
    exam_id_short = exam.get("id", "")
    student_id_short = student.get("id", "")
    qr_payload = f"E:{exam_id_short}|S:{student_id_short}"
    qr_b64 = make_qr_base64(qr_payload)

    content = re.sub(
        r'(<div class="scan-qr-box"[^>]*>\s*<img src=")[^"]*(")',
        rf'\g<1>data:image/png;base64,{qr_b64}\g<2>',
        content
    )

    return content

def generate_classroom_covers_pdf(
    classroom: Dict[str, Any],
    students: List[Dict[str, Any]],
    exams: List[Dict[str, Any]],
    order_by: str = "student",
    chunk_size: int = 120,
    include_attendance_roster: bool = True
) -> bytes:
    """
    Renders high-definition cover PDFs for every student in the classroom,
    merged into a single PDF document in the requested sorting order.
    ALWAYS includes as Page 1 (and subsequent if > 28 students) the official
    Attendance & Signature Roster (Ata de Frequência e Entrega de Gabaritos/Capas).
    Uses chunked multi-page single-pass Chrome printing for ultra-fast generation (10x-20x faster).
    """
    if not students or not exams:
        raise ValueError("Estudantes e simulados são obrigatórios para emissão das capas.")

    chrome_bin = get_chrome_executable()
    if not chrome_bin:
        raise RuntimeError("Navegador Google Chrome ou Microsoft Edge não encontrado no servidor para renderizar o PDF.")

    temp_dir = tempfile.mkdtemp(prefix="covers_batch_")
    merged_pdf = fitz.open()

    try:
        # 1. Page 1: Official Attendance & Signature Roster (Ata de Frequência)
        if include_attendance_roster and students:
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib import pagesizes
                from app.services.pdf_generator import render_attendance_roster_page

                buf_roster = io.BytesIO()
                c_roster = canvas.Canvas(buf_roster, pagesize=pagesizes.A4)
                render_attendance_roster_page(
                    c=c_roster,
                    classroom=classroom,
                    students=students,
                    exams=exams,
                    logo_path=None
                )
                c_roster.save()
                roster_bytes = buf_roster.getvalue()
                buf_roster.close()

                if roster_bytes:
                    roster_doc = fitz.open(stream=roster_bytes, filetype="pdf")
                    merged_pdf.insert_pdf(roster_doc)
                    roster_doc.close()
            except Exception as e:
                import logging
                logging.getLogger("uvicorn").error(f"Erro ao gerar ata de presença para capas: {e}")

        # 2. Determine sequence of (exam, student) pairs based on order_by
        pairs = []
        if order_by == "exam":
            for ex in exams:
                for st in students:
                    pairs.append((ex, st))
        else:
            # Default: student
            for st in students:
                for ex in exams:
                    pairs.append((ex, st))

        # Process in chunks of up to `chunk_size` pages per Chrome pass
        for chunk_idx in range(0, len(pairs), chunk_size):
            chunk_pairs = pairs[chunk_idx : chunk_idx + chunk_size]
            slots = []

            for ex, st in chunk_pairs:
                page_html = render_single_cover_html(ex, st, classroom)
                slots.append(f'<div class="cover-page-slot">{page_html}</div>')

            combined_html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
@page {
    size: 210mm 297mm;
    margin: 0;
}
html, body {
    margin: 0;
    padding: 0;
    background: #ffffff;
}
.cover-page-slot {
    width: 210mm;
    height: 297mm;
    page-break-after: always;
    break-after: page;
    position: relative;
    overflow: hidden;
}
.cover-page-slot:last-child {
    page-break-after: avoid;
    break-after: avoid;
}
</style>
</head>
<body>
""" + "\n".join(slots) + "\n</body>\n</html>"

            chunk_html_file = os.path.join(temp_dir, f"chunk_{chunk_idx}.html")
            chunk_pdf_file = os.path.join(temp_dir, f"chunk_{chunk_idx}.pdf")

            with open(chunk_html_file, "w", encoding="utf-8") as f:
                f.write(combined_html)

            cmd = [
                chrome_bin,
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-default-apps",
                "--no-first-run",
                "--metrics-recording-only",
                f"--print-to-pdf={chunk_pdf_file}",
                os.path.abspath(chunk_html_file)
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)

            if os.path.exists(chunk_pdf_file):
                chunk_doc = fitz.open(chunk_pdf_file)
                merged_pdf.insert_pdf(chunk_doc)
                chunk_doc.close()

        pdf_bytes = merged_pdf.tobytes()
        return pdf_bytes
    finally:
        merged_pdf.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

