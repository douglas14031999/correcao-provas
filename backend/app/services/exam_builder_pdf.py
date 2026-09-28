import os
import re
import io
import html
import base64
import tempfile
import subprocess
from typing import Dict, Any, Optional

from app.services.cover_batch_generator import get_chrome_executable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
BUILDER_IMAGES_DIR = os.path.join(STORAGE_DIR, "builder_images")

def resolve_image_to_base64(url_or_path: str) -> str:
    """
    Converte qualquer caminho local de imagem ou URL /storage/... em URI Base64 autossuficiente
    para que o Chrome Headless renderize perfeitamente no PDF sem falhas de carregamento.
    """
    if not url_or_path:
        return ""
    s = str(url_or_path).strip()
    if s.startswith("data:image/"):
        return s
    
    # Normalizar URLs locais com host
    for prefix in ["http://localhost:8080/storage/", "http://127.0.0.1:8080/storage/", "http://localhost/storage/"]:
        if s.startswith(prefix):
            s = "/storage/" + s[len(prefix):]
            break
            
    local_path = None
    if s.startswith("/storage/"):
        rel = s[len("/storage/"):]
        cand = os.path.join(STORAGE_DIR, rel.replace("/", os.sep))
        if os.path.isfile(cand):
            local_path = cand
    elif s.startswith("storage/"):
        rel = s[len("storage/"):]
        cand = os.path.join(STORAGE_DIR, rel.replace("/", os.sep))
        if os.path.isfile(cand):
            local_path = cand
    elif os.path.isfile(s):
        local_path = s
    else:
        cand = os.path.join(BUILDER_IMAGES_DIR, os.path.basename(s))
        if os.path.isfile(cand):
            local_path = cand

    if local_path and os.path.isfile(local_path):
        ext = os.path.splitext(local_path)[1].lower().lstrip(".")
        mime_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "svg": "image/svg+xml",
            "gif": "image/gif"
        }
        mime = mime_map.get(ext, "image/png")
        try:
            with open(local_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            return f"data:{mime};base64,{b64}"
        except Exception:
            pass
    return s

def embed_images_in_html(html_text: str) -> str:
    """
    Substitui tags <img src="..."> que apontem para /storage/... por dados inline Base64.
    """
    if not html_text:
        return ""
    def _repl(match):
        prefix = match.group(1)
        src = match.group(2)
        suffix = match.group(3)
        b64_src = resolve_image_to_base64(src)
        return f"{prefix}{b64_src}{suffix}"
    
    return re.sub(r'(<img\s+[^>]*?src=["\'])([^"\']+)(["\'])', _repl, html_text, flags=re.IGNORECASE)

# Brasão oficial de Lagoa da Canoa em Base64 ou SVG vetorial limpo para máxima nitidez
CANOA_BRASAO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="60" height="60">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e3a8a;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0284c7;stop-opacity:1" />
    </linearGradient>
  </defs>
  <circle cx="50" cy="50" r="46" fill="url(#grad1)" stroke="#0e2a47" stroke-width="2"/>
  <circle cx="50" cy="50" r="41" fill="none" stroke="#facc15" stroke-width="2" stroke-dasharray="2 1"/>
  <path d="M 28 65 Q 50 78 72 65 L 75 70 Q 50 85 25 70 Z" fill="#facc15"/>
  <path d="M 32 62 C 40 50, 60 50, 68 62 C 60 57, 40 57, 32 62 Z" fill="#ffffff"/>
  <path d="M 50 20 L 53 32 L 65 32 L 55 40 L 59 52 L 50 44 L 41 52 L 45 40 L 35 32 L 47 32 Z" fill="#facc15"/>
  <text x="50" y="88" font-family="Arial, sans-serif" font-size="7" font-weight="bold" fill="#ffffff" text-anchor="middle">LAGOA DA CANOA</text>
</svg>"""

def get_official_logo_html() -> str:
    """
    Retorna o brasão oficial de Lagoa da Canoa embutido em Base64 para garantir nitidez e renderização imediata,
    com fallback automático para SVG vetorial caso o arquivo não seja encontrado.
    """
    curr_dir = os.path.abspath(os.path.dirname(__file__))
    p_backend = os.path.dirname(os.path.dirname(curr_dir))
    p_root = os.path.dirname(p_backend)
    candidates = [
        os.path.join(p_root, "frontend", "assets", "logo_lagoa_da_canoa.png"),
        os.path.join(p_backend, "storage", "assets", "logo_lagoa_da_canoa.png"),
        os.path.join(p_backend, "storage", "logo_municipal.jpg"),
        os.path.join(p_root, "storage", "assets", "logo_lagoa_da_canoa.png"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            try:
                with open(c, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                ext = "png" if c.lower().endswith(".png") else "jpeg"
                return f'<img src="data:image/{ext};base64,{b64}" alt="Brasão Oficial" class="official-logo-img" />'
            except Exception:
                pass
    return CANOA_BRASAO_SVG

def render_exam_html(exam: Dict[str, Any], show_answers: bool = False) -> str:
    """
    Renders complete HTML document for the exam with Google Forms-like content,
    mathematical KaTeX support, circular alternatives, and 1 or 2 column layout.
    """
    title = html.escape(exam.get("title") or "AVALIAÇÃO")
    institution = html.escape(exam.get("institution") or "PREFEITURA MUNICIPAL DE LAGOA DA CANOA - SEMED")
    school_name = html.escape(exam.get("school_name") or "SEMED - LAGOA DA CANOA")
    discipline = html.escape(exam.get("discipline") or "MATEMÁTICA")
    teacher_name = html.escape(exam.get("teacher_name") or "")
    grade_year = html.escape(exam.get("grade_year") or "9º ANO")
    classroom = html.escape(exam.get("classroom") or "TURMA A")
    shift = html.escape(exam.get("shift") or "MATUTINO")
    exam_date = html.escape(exam.get("exam_date") or "")
    columns_layout = int(exam.get("columns_layout") or exam.get("columns") or 2)
    footer_text = html.escape(exam.get("footer_text") or "Boa Prova!")
    include_answer_sheet = bool(exam.get("include_answer_sheet", 1))
    
    questions = exam.get("questions", [])
    calc_score = sum(float(q.get("points") or 1.0) for q in questions) if questions else 0.0
    max_score = calc_score if calc_score > 0 else float(exam.get("max_score", 10.0))
    
    raw_top = float(exam.get("margin_top") if exam.get("margin_top") is not None else 3.0)
    raw_bottom = float(exam.get("margin_bottom") if exam.get("margin_bottom") is not None else 2.0)
    raw_left = float(exam.get("margin_left") if exam.get("margin_left") is not None else 3.0)
    raw_right = float(exam.get("margin_right") if exam.get("margin_right") is not None else 2.0)

    margin_top = raw_top / 10.0 if raw_top > 5.0 else raw_top
    margin_bottom = raw_bottom / 10.0 if raw_bottom > 5.0 else raw_bottom
    margin_left = raw_left / 10.0 if raw_left > 5.0 else raw_left
    margin_right = raw_right / 10.0 if raw_right > 5.0 else raw_right

    # Column configuration
    col_style = """
    .exam-page-body {
        flex: 1 1 0;
        min-height: 0;
        overflow: hidden;
    }
    .exam-page-body.columns-2 {
        column-count: 2;
        column-gap: 8mm;
        column-rule: 1px solid #cbd5e1;
        column-fill: auto;
    }
    .exam-page-body.columns-1 {
        column-count: 1;
    }
    """

    # Questions markup
    q_html_list = []
    for q in questions:
        q_num = q.get("question_number", 1)
        points = float(q.get("points", 1.0))
        raw_statement = embed_images_in_html(q.get("statement", ""))
        # Format points display
        pts_str = f"({points:g} ponto{'s' if points > 1.0 else ''})" if points > 0 else ""
        
        # Images handling - converter para Base64 para garantir carregamento no Chrome PDF
        img_url = resolve_image_to_base64(q.get("image_url", "").strip())
        img_pos = q.get("image_position", "after_statement")
        img_width = q.get("image_width", "50%")
        img_caption = html.escape(q.get("image_caption", ""))

        img_tag = ""
        if img_url:
            caption_tag = f'<div class="img-caption">{img_caption}</div>' if img_caption else ""
            img_tag = f"""
            <div class="q-image-box pos-{img_pos}" style="max-width: {img_width};">
                <img src="{img_url}" alt="Imagem da Questão {q_num}" />
                {caption_tag}
            </div>
            """

        # Alternatives markup (letras circulares)
        alts = q.get("alternatives", [])
        alts_html = []
        for a in alts:
            letter = html.escape(a.get("letter", "A"))
            text = html.escape(a.get("text", ""))
            is_corr = bool(a.get("is_correct")) and show_answers
            correct_class = " correct-answer" if is_corr else ""
            
            # Suporte a imagem nas alternativas com conversão Base64
            alt_img = a.get("image") or {}
            raw_alt_url = alt_img.get("url") or a.get("image_url", "")
            alt_img_url = resolve_image_to_base64(raw_alt_url)
            alt_img_tag = ""
            if alt_img_url:
                alt_align = alt_img.get("align", "left")
                alt_width = alt_img.get("width", "180px")
                alt_img_tag = f'<div class="alt-img-display align-{alt_align}" style="width: {alt_width}; max-width: 100%;"><img src="{alt_img_url}" alt="Imagem alternativa {letter}" style="width: 100%; border-radius: 4px;" /></div>'
            
            alts_html.append(f"""
            <div class="alt-row{correct_class}">
                <div class="alt-circle">{letter}</div>
                <div class="alt-text-col">
                    <div class="alt-text">{text}</div>
                    {alt_img_tag}
                </div>
            </div>
            """)
        
        alts_block = "".join(alts_html)

        # Assemble question with image positioning
        q_content = ""
        if img_pos == "before_statement":
            q_content = f"{img_tag}\n<div class='q-statement'>{raw_statement}</div>"
        elif img_pos == "right":
            q_content = f"""
            <div class="q-row-flex">
                <div class="q-statement flex-grow">{raw_statement}</div>
                {img_tag}
            </div>
            """
        else: # after_statement or center
            q_content = f"<div class='q-statement'>{raw_statement}</div>\n{img_tag}"

        q_html_list.append(f"""
        <div class="question-card" id="q-{q_num}">
            <div class="q-header">
                <span class="q-number">QUESTÃO {q_num:02d}</span>
                <span class="q-points">{pts_str}</span>
            </div>
            {q_content}
            <div class="q-alternatives">
                {alts_block}
            </div>
        </div>
        """)

    all_questions_html = "\n".join(q_html_list)

    # Mini Answer Sheet / Folha de Gabarito de Rascunho
    answer_sheet_html = ""
    if include_answer_sheet and questions:
        rows_bubbles = []
        for q in questions:
            qn = q.get("question_number", 1)
            bubbles = ""
            for ltr in ["A", "B", "C", "D", "E"][:len(q.get("alternatives", [])) or 4]:
                bubbles += f'<span class="as-bubble">{ltr}</span>'
            rows_bubbles.append(f"""
            <div class="as-row">
                <span class="as-num">{qn:02d}</span>
                <span class="as-bubbles-wrap">{bubbles}</span>
            </div>
            """)
        
        answer_sheet_html = f"""
        <div class="answer-sheet-card">
            <div class="as-title">GABARITO DE RESPOSTAS (RASCUNHO DO ALUNO)</div>
            <div class="as-subtitle">Preencha totalmente a bolha da alternativa correta a caneta azul ou preta.</div>
            <div class="as-grid">
                {"".join(rows_bubbles)}
            </div>
        </div>
        """

    header_style = exam.get("header_style") or "title_only"
    include_header = exam.get("include_header")
    if include_header is None:
        include_header = (header_style == "standard")
    else:
        include_header = bool(include_header)

    if include_header:
        raw_inst = (exam.get("institution") or "").strip()
        if not raw_inst:
            inst_pref = "PREFEITURA MUNICIPAL DE LAGOA DA CANOA"
            inst_sec = "SECRETARIA MUNICIPAL DE EDUCAÇÃO – SEMED"
        elif " - " in raw_inst:
            parts = raw_inst.split(" - ", 1)
            inst_pref = parts[0].strip()
            inst_sec = parts[1].strip()
            if "SECRETARIA" not in inst_sec.upper() and "SEMED" in inst_sec.upper():
                inst_sec = "SECRETARIA MUNICIPAL DE EDUCAÇÃO – SEMED"
        else:
            inst_pref = raw_inst
            inst_sec = "SECRETARIA MUNICIPAL DE EDUCAÇÃO – SEMED"

        school_display = (exam.get("school_name") or "ESCOLA MUNICIPAL DE ENSINO FUNDAMENTAL").strip()

        disp_title = title.upper()
        if discipline and discipline.upper() not in disp_title:
            banner_title = f"{disp_title} • {discipline.upper()}"
        else:
            banner_title = disp_title

        logo_html = get_official_logo_html()

        header_html = f"""<div class="exam-header">
    <div class="header-top">
        <div class="header-logo">
            {logo_html}
        </div>
        <div class="header-inst-box">
            <div class="inst-prefeitura">{html.escape(inst_pref.upper())}</div>
            <div class="inst-secretaria">{html.escape(inst_sec.upper())}</div>
            <div class="inst-escola">{html.escape(school_display.upper())}</div>
        </div>
    </div>

    <div class="header-title-banner">
        <span>{banner_title}</span>
    </div>

    <div class="header-meta-row">
        <div class="meta-item meta-grow">
            <span class="meta-lbl">PROFESSOR(A):</span>
            <span class="meta-val">{teacher_name or "___________________________"}</span>
        </div>
        <div class="meta-item meta-fixed">
            <span class="meta-lbl">DATA:</span>
            <span class="meta-val">{exam_date or "__/__/2026"}</span>
        </div>
        <div class="meta-item meta-fixed">
            <span class="meta-lbl">ANO/SÉRIE:</span>
            <span class="meta-val">{grade_year}</span>
        </div>
        <div class="meta-item meta-fixed">
            <span class="meta-lbl">TURMA:</span>
            <span class="meta-val">{classroom}</span>
        </div>
        <div class="meta-item meta-fixed">
            <span class="meta-lbl">TURNO:</span>
            <span class="meta-val">{shift}</span>
        </div>
    </div>

    <div class="header-student-row">
        <div class="student-info-group">
            <span class="student-lbl">ESTUDANTE:</span>
            <div class="student-name-line"></div>
            <span class="student-num-lbl">Nº:</span>
            <div class="student-num-line"></div>
        </div>
        <div class="student-grade-badge">
            <span class="grade-lbl">NOTA:</span>
            <span class="grade-fill">______</span>
            <span class="grade-max">/ {max_score:g}</span>
        </div>
    </div>
</div>"""
    else:
        header_html = f"""<div class="exam-header-title-only">
    <h1 class="exam-title-clean">{title}</h1>
</div>"""

    footer_brand = f"{school_display if include_header else school_name} • {title}" if include_header else title

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<!-- KaTeX CSS & JS para fórmulas matemáticas de alta fidelidade -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {{
        delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}},
            {{left: '\\\\(', right: '\\\\)', display: false}},
            {{left: '\\\\[', right: '\\\\]', display: true}}
        ],
        macros: {{}},
        throwOnError: false
    }});"></script>

<style>
@page {{
    size: 210mm 297mm;
    margin: 0;
}}

*, *:before, *:after {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}}

body {{
    font-family: "Liberation Sans", "Helvetica Neue", Arial, sans-serif;
    color: #1e293b;
    font-size: 10pt;
    line-height: 1.35;
    margin: 0;
    padding: 0;
}}

/* Modo Tela / Pré-visualização Fiel com Margens Reais do A4 e Páginas Independentes */
@media screen {{
    html {{
        background-color: #64748b;
        padding: 24px 0;
        min-height: 100vh;
    }}
    body {{
        background: transparent;
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 0 auto;
        padding: 0;
    }}
    #exam-pages-root {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 36px;
        padding: 24px 0 60px 0;
        width: 100%;
    }}
    .a4-page-wrapper {{
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
        width: 210mm;
    }}
    .a4-page-header-bar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        padding: 0 4px;
    }}
    .a4-page-tag {{
        background: #0f172a;
        color: #f8fafc;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 12px;
        border-radius: 6px;
        letter-spacing: 0.6px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }}
    .a4-page-dimensions {{
        font-size: 10px;
        font-weight: 600;
        color: #cbd5e1;
        letter-spacing: 0.4px;
    }}
    .a4-page {{
        width: 210mm;
        height: 297mm;
        min-height: 297mm;
        max-height: 297mm;
        box-sizing: border-box;
        padding: {margin_top:g}cm {margin_right:g}cm {margin_bottom:g}cm {margin_left:g}cm;
        background: #ffffff;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(0, 0, 0, 0.08);
        border-radius: 4px;
        position: relative;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }}
}}

/* Modo de Impressão e PDF Oficial */
@media print {{
    html, body, #exam-pages-root, .a4-page-wrapper {{
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        box-shadow: none !important;
        display: block !important;
        gap: 0 !important;
    }}
    .a4-page-header-bar {{
        display: none !important;
    }}
    .a4-page {{
        width: 210mm !important;
        height: 297mm !important;
        min-height: 297mm !important;
        max-height: 297mm !important;
        padding: {margin_top:g}cm {margin_right:g}cm {margin_bottom:g}cm {margin_left:g}cm !important;
        margin: 0 !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        page-break-after: always !important;
        break-after: page !important;
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
    }}
    .a4-page-wrapper:last-child .a4-page {{
        page-break-after: avoid !important;
        break-after: avoid !important;
    }}
}}

.exam-running-header {{
    flex-shrink: 0;
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    font-weight: 700;
    color: #64748b;
    border-bottom: 1px dashed #cbd5e1;
    padding-bottom: 1.5mm;
    margin-bottom: 3.5mm;
    text-transform: uppercase;
}}

/* Cabeçalho Apenas Título (quando vinculado à turma/capa) */
.exam-header-title-only {{
    text-align: center;
    border-bottom: 2px solid #0f172a;
    padding-bottom: 3mm;
    margin-bottom: 5mm;
}}

.exam-title-clean {{
    font-size: 13pt;
    font-weight: 800;
    text-transform: uppercase;
    color: #0f172a;
    margin: 0;
    letter-spacing: 0.5px;
    line-height: 1.3;
}}

/* Cabeçalho Institucional Oficial Padrão Relatórios */
.exam-header {{
    border: 1.5px solid #1e293b;
    border-radius: 4px;
    margin-bottom: 4.5mm;
    background: #ffffff;
    overflow: hidden;
}}

.header-top {{
    display: flex;
    align-items: center;
    gap: 4mm;
    padding: 2.5mm 3.5mm;
    background: #ffffff;
}}

.header-logo {{
    flex-shrink: 0;
    width: 14mm;
    height: 14mm;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.header-logo img, .official-logo-img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}}

.header-inst-box {{
    flex-grow: 1;
    text-align: left;
}}

.inst-prefeitura {{
    font-size: 10pt;
    font-weight: 800;
    text-transform: uppercase;
    color: #0f172a;
    letter-spacing: 0.4px;
    line-height: 1.25;
}}

.inst-secretaria {{
    font-size: 8.5pt;
    font-weight: 600;
    text-transform: uppercase;
    color: #334155;
    letter-spacing: 0.3px;
    line-height: 1.25;
    margin: 0.4mm 0;
}}

.inst-escola {{
    font-size: 9.5pt;
    font-weight: 800;
    text-transform: uppercase;
    color: #1e3a8a;
    letter-spacing: 0.4px;
    line-height: 1.25;
}}

/* Faixa do Título do Documento */
.header-title-banner {{
    background: #1e293b;
    color: #ffffff;
    text-align: center;
    font-weight: 800;
    font-size: 9.2pt;
    padding: 1.8mm 3mm;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    line-height: 1.2;
}}

/* Linha de Metadados Institucionais (Sem quebra indevida) */
.header-meta-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5mm 3mm;
    background: #f8fafc;
    border-top: 1px solid #cbd5e1;
    border-bottom: 1px solid #cbd5e1;
    padding: 1.8mm 4mm;
    font-size: 7.8pt;
    flex-wrap: nowrap;
}}

.meta-item {{
    display: inline-flex;
    align-items: center;
    gap: 1.2mm;
    white-space: nowrap;
}}

.meta-item.meta-grow {{
    flex: 1 1 auto;
    min-width: 30mm;
}}

.meta-item.meta-fixed {{
    flex: 0 0 auto;
}}

.meta-lbl {{
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    font-size: 7.2pt;
    letter-spacing: 0.3px;
}}

.meta-val {{
    font-weight: 700;
    color: #0f172a;
    font-size: 7.8pt;
}}

/* Linha do Estudante e Caixa de Nota */
.header-student-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 3.5mm;
    padding: 2.2mm 4mm;
    background: #ffffff;
}}

.student-info-group {{
    flex-grow: 1;
    display: flex;
    align-items: flex-end;
    gap: 2mm;
    font-size: 8.5pt;
    font-weight: 800;
    color: #0f172a;
}}

.student-lbl, .student-num-lbl {{
    flex-shrink: 0;
    font-weight: 800;
    font-size: 8.5pt;
    color: #0f172a;
    letter-spacing: 0.3px;
}}

.student-name-line {{
    flex-grow: 1;
    border-bottom: 1.2px solid #0f172a;
    min-height: 12px;
}}

.student-num-line {{
    width: 14mm;
    border-bottom: 1.2px solid #0f172a;
    min-height: 12px;
}}

.student-grade-badge {{
    flex-shrink: 0;
    display: inline-flex;
    align-items: center;
    gap: 1.5mm;
    border: 1.4px solid #1e293b;
    border-radius: 3px;
    padding: 1.2mm 3mm;
    background: #f8fafc;
    font-weight: 800;
    font-size: 8.5pt;
    color: #0f172a;
    white-space: nowrap;
}}

.grade-lbl {{
    font-size: 8pt;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: 0.4px;
}}

.grade-fill {{
    font-size: 8.5pt;
    font-weight: 700;
    color: #64748b;
}}

.grade-max {{
    font-size: 8.5pt;
    font-weight: 800;
    color: #0f172a;
}}

/* Regras de Colunas */
{col_style}

/* Cartão da Questão - Permite quebrar entre colunas para economizar espaço */
.question-card {{
    break-inside: auto;
    page-break-inside: auto;
    -webkit-column-break-inside: auto;
    box-decoration-break: clone;
    -webkit-box-decoration-break: clone;
    margin-bottom: 3.5mm;
    padding: 2.5mm 3mm;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    background: #ffffff;
}}

.question-card.q-continuation {{
    border-top: 2px dashed #93c5fd;
}}

.question-card.q-continuation .q-header {{
    background: #eff6ff;
    border-radius: 3px 3px 0 0;
}}

.q-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5mm;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 1mm;
    break-after: avoid;
    page-break-after: avoid;
    -webkit-column-break-after: avoid;
}}

.q-number {{
    font-weight: 800;
    font-size: 9pt;
    color: #1e3a8a;
    background: #eff6ff;
    padding: 0.8mm 2.2mm;
    border-radius: 3px;
    border: 1px solid #bfdbfe;
}}

.q-points {{
    font-size: 8pt;
    font-weight: 600;
    color: #64748b;
}}

.q-statement {{
    font-size: 9.5pt;
    color: #1e293b;
    margin-bottom: 2mm;
    text-align: justify;
    line-height: 1.4;
    break-inside: avoid;
    page-break-inside: avoid;
    -webkit-column-break-inside: avoid;
}}

/* Imagens */
.q-image-box {{
    margin: 2mm auto;
    text-align: center;
    break-inside: avoid;
    page-break-inside: avoid;
    -webkit-column-break-inside: avoid;
}}

.q-image-box img {{
    max-width: 100%;
    height: auto;
    border: 1px solid #e2e8f0;
    border-radius: 3px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}}

.img-caption {{
    font-size: 7.5pt;
    font-style: italic;
    color: #64748b;
    margin-top: 1mm;
}}

.q-row-flex {{
    display: flex;
    gap: 3mm;
    align-items: flex-start;
}}

.flex-grow {{
    flex: 1;
}}

/* Alternativas com Letras Circulares */
.q-alternatives {{
    display: flex;
    flex-direction: column;
    gap: 1.5mm;
    margin-top: 1.5mm;
}}

.alt-row {{
    display: flex;
    align-items: flex-start;
    gap: 2.2mm;
    font-size: 9pt;
    break-inside: avoid;
    page-break-inside: avoid;
    -webkit-column-break-inside: avoid;
}}

.alt-circle {{
    width: 5.5mm;
    height: 5.5mm;
    border: 1.2px solid #0f172a;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 7.5pt;
    font-weight: 800;
    color: #0f172a;
    flex-shrink: 0;
    margin-top: 0.3mm;
    background: #ffffff;
}}

.alt-row.correct-answer .alt-circle {{
    background: #15803d;
    color: #ffffff;
    border-color: #15803d;
}}

.alt-row.correct-answer .alt-text {{
    font-weight: 700;
    color: #15803d;
}}

.alt-text {{
    flex-grow: 1;
    color: #1e293b;
    line-height: 1.3;
}}

.alt-text-col {{
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 1mm;
}}

.alt-img-display {{
    display: block;
    margin-top: 1mm;
}}

.alt-img-display.align-left {{
    margin-right: auto;
}}

.alt-img-display.align-center {{
    margin-left: auto;
    margin-right: auto;
}}

.alt-img-display.align-right {{
    margin-left: auto;
}}

.exam-img-figure {{
    border-radius: 4px;
    height: auto;
}}

.exam-img-figure.align-left {{
    float: left;
    margin: 1.5mm 3.5mm 1.5mm 0;
    max-width: 100%;
}}

.exam-img-figure.align-center {{
    display: block;
    margin: 2.5mm auto;
    text-align: center;
    clear: both;
    max-width: 100%;
}}

.exam-img-figure.align-right {{
    float: right;
    margin: 1.5mm 0 1.5mm 3.5mm;
    max-width: 100%;
}}

/* Gabarito de Respostas / Rascunho */
.answer-sheet-card {{
    break-inside: avoid;
    page-break-inside: avoid;
    border: 1.5px solid #0f172a;
    border-radius: 4px;
    padding: 2.5mm 3mm;
    margin-top: 4mm;
    background: #f8fafc;
}}

.as-title {{
    font-weight: 800;
    font-size: 8.5pt;
    text-align: center;
    color: #0f172a;
    text-transform: uppercase;
}}

.as-subtitle {{
    font-size: 7pt;
    color: #64748b;
    text-align: center;
    margin-bottom: 2mm;
}}

.as-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 2mm 4mm;
    justify-content: center;
}}

.as-row {{
    display: flex;
    align-items: center;
    gap: 1.5mm;
    border: 1px solid #cbd5e1;
    background: #ffffff;
    padding: 1mm 2mm;
    border-radius: 3px;
}}

.as-num {{
    font-weight: 700;
    font-size: 8pt;
    width: 5mm;
    color: #1e3a8a;
}}

.as-bubbles-wrap {{
    display: flex;
    gap: 1.2mm;
}}

.as-bubble {{
    width: 4.8mm;
    height: 4.8mm;
    border: 1px solid #475569;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 6.5pt;
    font-weight: 700;
    color: #475569;
}}

/* Rodapé */
.exam-footer {{
    flex-shrink: 0;
    margin-top: auto;
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: #94a3b8;
    border-top: 1px solid #e2e8f0;
    padding-top: 1.5mm;
}}
</style>
</head>
<body>

<div id="exam-flow-source" style="display: none;">
    <div id="flow-header">
        {header_html}
    </div>
    <div id="flow-items">
        {all_questions_html}
        {answer_sheet_html}
    </div>
</div>

<div id="exam-pages-root"></div>

<script>
function paginateExam() {{
    if (window.__examPaginated) return;
    window.__examPaginated = true;

    if (window.renderMathInElement) {{
        try {{
            renderMathInElement(document.getElementById('exam-flow-source'), {{
                delimiters: [
                    {{left: '$$', right: '$$', display: true}},
                    {{left: '$', right: '$', display: false}},
                    {{left: '\\\\(', right: '\\\\)', display: false}},
                    {{left: '\\\\[', right: '\\\\]', display: true}}
                ],
                throwOnError: false
            }});
        }} catch (e) {{}}
    }}

    var flowSource = document.getElementById('exam-flow-source');
    var pagesRoot = document.getElementById('exam-pages-root');
    var flowHeader = document.getElementById('flow-header');
    var flowItemsContainer = document.getElementById('flow-items');
    if (!flowItemsContainer) return;

    var items = Array.from(flowItemsContainer.children);
    var isTwoCols = { "true" if columns_layout == 2 else "false" };
    var pageNum = 1;

    function createPage() {{
        var wrapper = document.createElement('div');
        wrapper.className = 'a4-page-wrapper';

        var bar = document.createElement('div');
        bar.className = 'a4-page-header-bar';
        bar.innerHTML = '<span class="a4-page-tag">PÁGINA ' + pageNum + '</span><span class="a4-page-dimensions">FOLHA A4 • 210 × 297 mm</span>';
        wrapper.appendChild(bar);

        var page = document.createElement('div');
        page.className = 'a4-page';
        page.setAttribute('data-page', pageNum);
        wrapper.appendChild(page);

        if (pageNum === 1) {{
            if (flowHeader) {{
                page.appendChild(flowHeader.cloneNode(true));
            }}
        }} else {{
            var runHdr = document.createElement('div');
            runHdr.className = 'exam-running-header';
            runHdr.innerHTML = '<span>{title}</span><span>(Continuação)</span>';
            page.appendChild(runHdr);
        }}

        var body = document.createElement('div');
        body.className = 'exam-page-body' + (isTwoCols ? ' columns-2' : ' columns-1');
        page.appendChild(body);

        var footer = document.createElement('div');
        footer.className = 'exam-footer';
        footer.innerHTML = '<span>{footer_brand}</span><span class="pg-counter">Página ' + pageNum + '</span><span>{footer_text}</span>';
        page.appendChild(footer);

        pagesRoot.appendChild(wrapper);
        return {{ wrapper: wrapper, page: page, body: body, footer: footer, bar: bar }};
    }}

    function doesItemOverflow(body, item) {{
        if (body.scrollWidth > body.clientWidth + 2) return true;
        if (body.scrollHeight > body.clientHeight + 2) return true;
        var bRect = body.getBoundingClientRect();
        
        var rects = item.getClientRects();
        for (var r = 0; r < rects.length; r++) {{
            if (rects[r].right > bRect.right + 2) return true;
            if (rects[r].bottom > bRect.bottom + 2) return true;
        }}

        var alts = item.querySelectorAll('.alt-row');
        for (var a = 0; a < alts.length; a++) {{
            var aRects = alts[a].getClientRects();
            for (var ar = 0; ar < aRects.length; ar++) {{
                if (aRects[ar].right > bRect.right + 2 || aRects[ar].bottom > bRect.bottom + 2) {{
                    return true;
                }}
            }}
        }}

        if (!isTwoCols && (item.offsetTop + item.offsetHeight > body.clientHeight + 2)) return true;
        return false;
    }}

    var cur = createPage();

    for (var i = 0; i < items.length; i++) {{
        var item = items[i];
        cur.body.appendChild(item);

        if (doesItemOverflow(cur.body, item) && cur.body.children.length > 1) {{
            var altsContainer = item.querySelector('.q-alternatives');
            var altRows = altsContainer ? Array.from(altsContainer.querySelectorAll('.alt-row')) : [];
            var canSplit = false;

            if (altsContainer && altRows.length >= 2) {{
                var removedAlts = [];
                for (var a = altRows.length - 1; a >= 0; a--) {{
                    altsContainer.removeChild(altRows[a]);
                    removedAlts.unshift(altRows[a]);
                }}

                if (doesItemOverflow(cur.body, item)) {{
                    // O enunciado por si só já não cabe nesta página
                    for (var ra = 0; ra < removedAlts.length; ra++) {{
                        altsContainer.appendChild(removedAlts[ra]);
                    }}
                }} else {{
                    // O enunciado cabe! Vamos verificar quantas alternativas cabem nesta página
                    var fitCount = 0;
                    for (var ra = 0; ra < removedAlts.length; ra++) {{
                        altsContainer.appendChild(removedAlts[ra]);
                        if (doesItemOverflow(cur.body, item)) {{
                            altsContainer.removeChild(removedAlts[ra]);
                            break;
                        }}
                        fitCount++;
                    }}

                    if (fitCount >= 1 && fitCount < altRows.length) {{
                        canSplit = true;
                        var remainingAlts = removedAlts.slice(fitCount);

                        pageNum++;
                        cur = createPage();

                        var contCard = document.createElement('div');
                        contCard.className = 'question-card q-continuation';
                        
                        var qNumEl = item.querySelector('.q-number');
                        var qNumText = (qNumEl ? qNumEl.textContent : '') + ' (Continuação)';
                        var qPtsEl = item.querySelector('.q-points');
                        var qPtsText = qPtsEl ? qPtsEl.textContent : '';

                        contCard.innerHTML = '<div class="q-header"><span class="q-number">' + qNumText + '</span><span class="q-points">' + qPtsText + '</span></div><div class="q-alternatives"></div>';
                        var contAltsContainer = contCard.querySelector('.q-alternatives');
                        for (var rem = 0; rem < remainingAlts.length; rem++) {{
                            contAltsContainer.appendChild(remainingAlts[rem]);
                        }}

                        cur.body.appendChild(contCard);
                    }} else {{
                        altsContainer.innerHTML = '';
                        for (var ra = 0; ra < removedAlts.length; ra++) {{
                            altsContainer.appendChild(removedAlts[ra]);
                        }}
                    }}
                }}
            }}

            if (!canSplit) {{
                cur.body.removeChild(item);
                pageNum++;
                cur = createPage();
                cur.body.appendChild(item);
            }}
        }}
    }}

    var totalPages = pageNum;
    var counters = pagesRoot.querySelectorAll('.pg-counter');
    for (var j = 0; j < counters.length; j++) {{
        counters[j].textContent = 'Página ' + (j + 1) + ' de ' + totalPages;
    }}
}}

function initPagination() {{
    var images = Array.from(document.images);
    var pending = images.filter(function(img) {{ return !img.complete; }});
    if (pending.length === 0) {{
        paginateExam();
    }} else {{
        var count = pending.length;
        var done = function() {{
            count--;
            if (count <= 0) paginateExam();
        }};
        pending.forEach(function(img) {{
            img.addEventListener('load', done);
            img.addEventListener('error', done);
        }});
        setTimeout(function() {{
            paginateExam();
        }}, 500);
    }}
}}

if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initPagination);
}} else {{
    initPagination();
}}
</script>

</body>
</html>"""
    return full_html

def generate_exam_pdf_bytes(exam: Dict[str, Any], show_answers: bool = False) -> bytes:
    """
    Compiles the exam into an A4 PDF using the local/VPS Chrome headless engine
    with KaTeX mathematical formulas rendered perfectly.
    """
    html_content = render_exam_html(exam, show_answers=show_answers)
    
    chrome_bin = get_chrome_executable()
    if not chrome_bin:
        raise RuntimeError("Navegador Chrome/Chromium não localizado para renderização do PDF.")

    temp_dir = tempfile.mkdtemp(prefix="builder_pdf_")
    html_file = os.path.join(temp_dir, "exam.html")
    pdf_file = os.path.join(temp_dir, "exam.pdf")
    user_data_dir = os.path.join(temp_dir, "ud")
    os.makedirs(user_data_dir, exist_ok=True)

    try:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        cmd = [
            chrome_bin,
            "--headless=new",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--allow-file-access-from-files",
            "--enable-local-file-accesses",
            "--no-zygote",
            "--no-first-run",
            f"--user-data-dir={user_data_dir}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_file}",
            os.path.abspath(html_file)
        ]

        proc_env = os.environ.copy()
        proc_env["HOME"] = temp_dir
        proc_env["TMPDIR"] = temp_dir

        res = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            timeout=60,
            env=proc_env
        )

        if not os.path.exists(pdf_file) or os.path.getsize(pdf_file) == 0:
            err = (res.stderr or b"").decode("utf-8", errors="ignore")
            raise RuntimeError(f"Falha na compilação do PDF pelo Chrome: {err[:300]}")

        with open(pdf_file, "rb") as f:
            return f.read()

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
