import os
import io
import re
import uuid
import base64
import tempfile
import subprocess
import shutil
try:
    import qrcode
    HAVE_QRCODE = True
except ImportError:
    qrcode = None
    HAVE_QRCODE = False

from typing import List, Dict, Any, Optional

try:
    import fitz
except ImportError:
    import pymupdf as fitz

SHEETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage", "sheets"
)

def get_chrome_executable() -> Optional[str]:
    candidates = [
        "/opt/google/chrome/chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
        "google-chrome",
        "google-chrome-stable",
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
    if HAVE_QRCODE and qrcode is not None:
        try:
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
        except Exception:
            pass

    # Zero-dependency fallback using ReportLab built-in QrCodeWidget & renderPM
    try:
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderPM

        d = Drawing(120, 120)
        qr = QrCodeWidget(data)
        qr.barWidth = 120
        qr.barHeight = 120
        qr.barBorder = 1
        d.add(qr)
        buf = io.BytesIO()
        renderPM.drawToFile(d, buf, fmt="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

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

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates", "covers"
)

@functools.lru_cache(maxsize=16)
def get_cover_template_html(model_id: str) -> str:
    """Reads base template HTML for the chosen cover model (cached in RAM)."""
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '', model_id)
    if not safe_name.endswith(".html"):
        safe_name += ".html"
    
    # 1. Busca nos diretórios candidatos
    candidates = [
        os.path.join(TEMPLATES_DIR, safe_name),
        os.path.join(SHEETS_DIR, safe_name),
        os.path.join(TEMPLATES_DIR, "opcao_4_azul_nautico_lagoa.html"),
        os.path.join(SHEETS_DIR, "opcao_4_azul_nautico_lagoa.html"),
        os.path.join(TEMPLATES_DIR, "opcao_1_montanhas_canoa.html"),
        os.path.join(SHEETS_DIR, "opcao_1_montanhas_canoa.html"),
    ]

    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()

    # 2. Fallback dinâmico do gerador oficial (zero dependência de arquivo em disco)
    try:
        from app.services.reports.generate_4_canoa_proposals import html_op1, html_op2, html_op3, html_op4
        map_html = {
            "opcao_1_montanhas_canoa.html": html_op1,
            "opcao_2_rio_verde_petroleo.html": html_op2,
            "opcao_3_por_do_sol_solar.html": html_op3,
            "opcao_4_azul_nautico_lagoa.html": html_op4,
        }
        if safe_name in map_html:
            return map_html[safe_name]
        return html_op4
    except Exception:
        pass

    raise FileNotFoundError(f"Template de capa '{safe_name}' não localizado.")

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
    classroom: Dict[str, Any],
    model_override: Optional[str] = None
) -> str:
    """Populates template HTML with exam and student metadata."""
    effective_model = model_override or exam.get("cover_model") or "opcao_4_azul_nautico_lagoa"
    effective_model = str(effective_model).strip().replace(".html", "")
    content = get_cover_template_html(effective_model)
    
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
    base_color = header_colors.get(effective_model, "#1e3a8a")

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

def generate_classroom_covers_reportlab(
    classroom: Dict[str, Any],
    students: List[Dict[str, Any]],
    exams: List[Dict[str, Any]],
    order_by: str = "student",
    model_id: Optional[str] = None,
    include_attendance_roster: bool = True
) -> bytes:
    """
    Renderizador 100% nativo ReportLab para capas personalizadas com folha OMR integrada.
    Utilizado quando o servidor não possui navegador Google Chrome/Chromium instalado
    ou quando a execução do browser em modo headless falha por restrição de ambiente.
    Garante funcionamento imediato e confiável em qualquer ambiente VPS Linux/Docker.
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib import pagesizes
    from app.services.pdf_generator import render_attendance_roster_page
    from app.services.reports.exam_cover_builder import generate_exam_cover

    merged_pdf = fitz.open()

    # 1. Página 1: Ata Oficial de Presença e Entrega
    if include_attendance_roster and students:
        try:
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
            logging.getLogger("uvicorn").error(f"Erro ao gerar ata de presença para capas (ReportLab): {e}")

    # 2. Sequência de pares (simulado, estudante)
    pairs = []
    if order_by == "exam":
        for ex in exams:
            for st in students:
                pairs.append((ex, st))
    else:
        for st in students:
            for ex in exams:
                pairs.append((ex, st))

    temp_dir = tempfile.mkdtemp(prefix="covers_rl_")
    try:
        class_name = (classroom.get("name") or "Turma").strip()
        school_name = (classroom.get("school_name") or "Escola").strip()
        grade_stage = classroom.get("grade_year") or "Ensino Fundamental"
        raw_shift = (classroom.get("shift") or "MATUTINO").strip().upper()
        shift = "MATUTINO" if ("MANHÃ" in raw_shift or "MATUTINO" in raw_shift) else "VESPERTINO"

        for idx, (ex, st) in enumerate(pairs):
            st_name = (st.get("name") or "ESTUDANTE").strip()
            st_id = str(st.get("id") or idx + 1)
            ex_id = str(ex.get("id") or "1")
            qr_payload = f"E:{ex_id}|S:{st_id}"

            ex_title = (ex.get("cover_title") or ex.get("title") or "PROVA CANOA").upper()
            discipline = extract_exam_discipline(ex)
            num_q = int(ex.get("num_questions", 22))
            num_alt = int(ex.get("num_alternatives", 4))

            page_pdf_path = os.path.join(temp_dir, f"cover_{idx:04d}.pdf")

            if " - " in ex_title:
                parts = ex_title.split(" - ", 1)
                title_lines = [parts[0], parts[1]]
            elif len(ex_title) > 26:
                words = ex_title.split()
                mid = len(words) // 2
                title_lines = [" ".join(words[:mid]), " ".join(words[mid:])]
            else:
                title_lines = [ex_title]

            caderno_label = f"CAD-{ex_id[:4].upper()}" if len(ex_id) > 2 else f"CAD-0{ex_id}"

            effective_model = model_id or ex.get("cover_model") or "opcao_4_azul_nautico_lagoa"
            effective_model = str(effective_model).strip().replace(".html", "")

            theme_colors = {
                "opcao_1_montanhas_canoa": "#0e2a47",
                "opcao_2_rio_verde_petroleo": "#0b5d5c",
                "opcao_3_por_do_sol_solar": "#c2410c",
                "opcao_4_azul_nautico_lagoa": "#1e3a8a"
            }
            caderno_color = theme_colors.get(effective_model, "#1e3a8a")

            generate_exam_cover(
                output_pdf_path=page_pdf_path,
                year="2026",
                main_title_lines=title_lines,
                header_subtitle=f"{school_name.upper()} • {class_name}",
                caderno_code=caderno_label,
                discipline=discipline,
                grade_stage=f"{grade_stage} • {class_name}",
                qr_code_text=qr_payload,
                num_questions=num_q,
                num_alternatives=num_alt,
                student_name=st_name,
                tracking_code=f"CANOA-{ex_id[:4]}-{st_id[:4]}",
                caderno_accent_color=caderno_color,
                school_name=school_name,
                classroom_name=class_name,
                shift=shift
            )

            cover_doc = fitz.open(page_pdf_path)
            merged_pdf.insert_pdf(cover_doc)
            cover_doc.close()

        out_buf = io.BytesIO()
        merged_pdf.save(out_buf)
        merged_pdf.close()
        return out_buf.getvalue()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def generate_classroom_covers_pdf(
    classroom: Dict[str, Any],
    students: List[Dict[str, Any]],
    exams: List[Dict[str, Any]],
    order_by: str = "student",
    model_id: Optional[str] = None,
    chunk_size: int = 60,
    include_attendance_roster: bool = True
) -> bytes:
    """
    Renders high-definition cover PDFs for every student in the classroom,
    merged into a single PDF document in the requested sorting order.
    ALWAYS includes as Page 1 (and subsequent if > 28 students) the official
    Attendance & Signature Roster (Ata de Frequência e Entrega de Gabaritos/Capas).
    Uses chunked multi-page single-pass Chrome printing for ultra-fast generation.
    Falls back gracefully to native pure ReportLab generation if Chrome/Chromium
    is not installed or encounters environmental sandboxing restrictions.
    """
    if not students or not exams:
        raise ValueError("Estudantes e simulados são obrigatórios para emissão das capas.")

    chrome_bin = get_chrome_executable()
    if not chrome_bin:
        return generate_classroom_covers_reportlab(
            classroom=classroom,
            students=students,
            exams=exams,
            order_by=order_by,
            model_id=model_id,
            include_attendance_roster=include_attendance_roster
        )

    base_temp = None
    if os.name != 'nt':
        home_dir = os.path.expanduser("~")
        if os.path.exists(home_dir) and os.access(home_dir, os.W_OK):
            snap_compatible_dir = os.path.join(home_dir, ".covers_batch_tmp")
            try:
                os.makedirs(snap_compatible_dir, exist_ok=True)
                base_temp = snap_compatible_dir
            except Exception:
                base_temp = None

    temp_dir = tempfile.mkdtemp(prefix="covers_batch_", dir=base_temp)
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
            for st in students:
                for ex in exams:
                    pairs.append((ex, st))

        # Process in chunks of up to `chunk_size` pages per Chrome pass
        for chunk_idx in range(0, len(pairs), chunk_size):
            chunk_pairs = pairs[chunk_idx : chunk_idx + chunk_size]
            slots = []

            for ex, st in chunk_pairs:
                page_html = render_single_cover_html(ex, st, classroom, model_override=model_id)
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
            user_data_dir = os.path.join(temp_dir, f"ud_{chunk_idx}")
            crash_dumps_dir = os.path.join(temp_dir, f"dumps_{chunk_idx}")
            os.makedirs(user_data_dir, exist_ok=True)
            os.makedirs(crash_dumps_dir, exist_ok=True)

            with open(chunk_html_file, "w", encoding="utf-8") as f:
                f.write(combined_html)

            cmd = [
                chrome_bin,
                "--headless=new",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--no-zygote",
                "--no-first-run",
                "--js-flags=--max-old-space-size=256",
                "--disable-features=Translate,OptimizationHints,MediaRouter",
                f"--user-data-dir={user_data_dir}",
                f"--crash-dumps-dir={crash_dumps_dir}",
                "--no-pdf-header-footer",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-default-apps",
                "--metrics-recording-only",
                f"--print-to-pdf={chunk_pdf_file}",
                os.path.abspath(chunk_html_file)
            ]

            proc_env = os.environ.copy()
            proc_env["PATH"] = f"/var/www/correcao-provas/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{proc_env.get('PATH', '')}"
            proc_env["HOME"] = temp_dir
            proc_env["TMPDIR"] = temp_dir
            proc_env["XDG_CONFIG_HOME"] = os.path.join(temp_dir, "xdg_config")
            proc_env["XDG_DATA_HOME"] = os.path.join(temp_dir, "xdg_data")

            chrome_success = False
            last_err = ""
            for headless_flag in ["--headless=new", "--headless"]:
                cmd[1] = headless_flag
                try:
                    res = subprocess.run(
                        cmd,
                        check=False,
                        capture_output=True,
                        timeout=120,
                        env=proc_env
                    )
                    if res.returncode == 0 and os.path.exists(chunk_pdf_file) and os.path.getsize(chunk_pdf_file) > 0:
                        chrome_success = True
                        break
                    else:
                        err_bytes = (res.stderr or b"") + (res.stdout or b"")
                        last_err = err_bytes.decode("utf-8", errors="ignore")
                except Exception as ex_proc:
                    last_err = str(ex_proc)

            if not chrome_success:
                import logging
                logging.getLogger("uvicorn").warning(
                    f"Execução do Chrome/Chromium falhou no servidor: {last_err.strip()[:300]}. "
                    "Ativando fallback seguro via ReportLab para emissão das capas."
                )
                return generate_classroom_covers_reportlab(
                    classroom=classroom,
                    students=students,
                    exams=exams,
                    order_by=order_by,
                    model_id=model_id,
                    include_attendance_roster=include_attendance_roster
                )

            if os.path.exists(chunk_pdf_file):
                chunk_doc = fitz.open(chunk_pdf_file)
                merged_pdf.insert_pdf(chunk_doc)
                chunk_doc.close()
                try:
                    os.remove(chunk_pdf_file)
                except Exception:
                    pass

            # Liberação imediata de espaço e memória do chunk processado
            shutil.rmtree(user_data_dir, ignore_errors=True)
            shutil.rmtree(crash_dumps_dir, ignore_errors=True)
            if os.path.exists(chunk_html_file):
                try:
                    os.remove(chunk_html_file)
                except Exception:
                    pass

        pdf_bytes = merged_pdf.tobytes()
        return pdf_bytes
    finally:
        merged_pdf.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

