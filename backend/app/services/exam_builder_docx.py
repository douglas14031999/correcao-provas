import os
import re
import io
import html
import base64
from typing import Dict, Any, Optional, List, Tuple

try:
    import docx
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.enum.section import WD_SECTION_START
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    HAVE_DOCX = True
except ImportError:
    HAVE_DOCX = False

from PIL import Image, ImageDraw, ImageFont

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAVE_MATPLOTLIB = True
except ImportError:
    HAVE_MATPLOTLIB = False

from app.services.exam_builder_pdf import resolve_image_to_base64

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
BUILDER_IMAGES_DIR = os.path.join(STORAGE_DIR, "builder_images")

# Cache de ícones circulares de alternativas para evitar reprocessamento gráfico
_BADGE_CACHE: Dict[Tuple[str, bool], bytes] = {}

def get_official_logo_path() -> Optional[str]:
    """Localiza o arquivo físico do brasão/logo municipal no servidor."""
    candidates = [
        os.path.join(STORAGE_DIR, "assets", "logo_lagoa_da_canoa.png"),
        os.path.join(STORAGE_DIR, "logo_municipal.jpg"),
        os.path.join(os.path.dirname(BASE_DIR), "frontend", "assets", "logo_lagoa_da_canoa.png"),
        os.path.join(BASE_DIR, "app", "storage", "assets", "logo_lagoa_da_canoa.png"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

def set_cell_background(cell, hex_color: str):
    """Define a cor de fundo de uma célula de tabela no Word."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color.replace("#", ""))
    tcPr.append(shd)

def set_cell_margins(cell, top=40, bottom=40, left=70, right=70):
    """Define margens internas da célula em twips (1 pt = 20 twips)."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m_name, m_val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m_name}')
        node.set(qn('w:w'), str(m_val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_borders(cell, **kwargs):
    """Configura bordas específicas em uma célula. Ex: top={'val': 'single', 'sz': '4', 'color': 'CBD5E1'}"""
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = OxmlElement(tag)
            for key, val in edge_data.items():
                element.set(qn(f'w:{key}'), str(val))
            tcBorders.append(element)
    tcPr.append(tcBorders)

def set_table_borders_none(table):
    """Remove bordas padrão da tabela."""
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        tblBorders = OxmlElement('w:tblBorders')
        for b_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            b = OxmlElement(f'w:{b_name}')
            b.set(qn('w:val'), 'none')
            tblBorders.append(b)
        tblPr[0].append(tblBorders)

def get_circle_badge_stream(letter: str, is_correct: bool = False) -> io.BytesIO:
    """
    Gera um selo circular (badge) nítido em PNG para a letra da alternativa.
    Substitui glifos como Ⓐ que no Word do Windows aparecem como [?] por falta de fonte.
    """
    key = (letter.upper(), is_correct)
    if key in _BADGE_CACHE:
        buf = io.BytesIO(_BADGE_CACHE[key])
        buf.seek(0)
        return buf

    size = 56
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    bg_color = (21, 128, 61, 255) if is_correct else (255, 255, 255, 255)
    border_color = (21, 128, 61, 255) if is_correct else (15, 23, 42, 255)
    text_color = (255, 255, 255, 255) if is_correct else (15, 23, 42, 255)

    draw.ellipse([2, 2, size - 3, size - 3], fill=bg_color, outline=border_color, width=3)

    font = None
    for font_name in ['arialbd.ttf', 'Arial-Bold.ttf', 'calibrib.ttf', 'arial.ttf']:
        try:
            font = ImageFont.truetype(font_name, 28)
            break
        except Exception:
            continue
    if not font:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter.upper(), font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), letter.upper(), fill=text_color, font=font)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    data = buf.getvalue()
    _BADGE_CACHE[key] = data
    buf.seek(0)
    return buf

def render_math_to_png(latex_str: str, fontsize=11) -> Optional[io.BytesIO]:
    """Renderiza uma fórmula matemática LaTeX/KaTeX em imagem PNG de alta resolução com bounding-box recortado."""
    if not latex_str or not HAVE_MATPLOTLIB:
        return None
    try:
        clean = latex_str.strip()
        if clean.startswith('$$') and clean.endswith('$$'):
            clean = clean[2:-2].strip()
        elif clean.startswith(r'\[') and clean.endswith(r'\]'):
            clean = clean[2:-2].strip()
        elif clean.startswith('$') and clean.endswith('$'):
            clean = clean[1:-1].strip()
        elif clean.startswith(r'\(') and clean.endswith(r'\)'):
            clean = clean[2:-2].strip()

        clean = re.sub(r'\\text\{([^{}]+)\}', r'\1', clean)
        clean = clean.replace(r'\mathbb{R}', r'\mathbf{R}')
        clean = clean.replace(r'\mathbb{N}', r'\mathbf{N}')
        clean = clean.replace(r'\mathbb{Z}', r'\mathbf{Z}')
        clean = clean.replace(r'\mathbb{Q}', r'\mathbf{Q}')

        fig = plt.figure(figsize=(2.5, 0.5), dpi=220)
        fig.text(0.5, 0.5, f"${clean}$", fontsize=fontsize, ha='center', va='center')
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=220, bbox_inches='tight', transparent=True, pad_inches=0.01)
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception:
        return None

# Mapeamentos de KaTeX para texto Unicode universal (substitui ℝ por R para evitar quadrado de glifo ausente no Word)
MATH_REPLACEMENTS = [
    (r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1 / \2)'),
    (r'\\sqrt\{([^{}]+)\}', r'√(\1)'),
    (r'\\sqrt', '√'),
    (r'\\pm', '±'),
    (r'\\times', '×'),
    (r'\\cdot', '·'),
    (r'\\div', '÷'),
    (r'\\le', '≤'),
    (r'\\ge', '≥'),
    (r'\\ne', '≠'),
    (r'\\approx', '≈'),
    (r'\\Delta', 'Δ'),
    (r'\\pi', 'π'),
    (r'\\theta', 'θ'),
    (r'\\circ', '°'),
    (r'\\mathbb\{R\}', 'R'),
    (r'\\mathbb\{N\}', 'N'),
    (r'\\mathbb\{Z\}', 'Z'),
    (r'\\mathbb\{Q\}', 'Q'),
    (r'\\mathbf\{R\}', 'R'),
    (r'\\text\{([^{}]+)\}', r'\1'),
    (r'\^2', '²'),
    (r'\^3', '³'),
    (r'_1', '₁'),
    (r'_2', '₂'),
    (r'_c', '꜀'),
]

def clean_inline_math(m_str: str) -> str:
    """Limpa delimitadores matemáticos e converte símbolos KaTeX preservando espaços adjacentes."""
    s = m_str
    if s.startswith('$') and s.endswith('$') and len(s) >= 2:
        s = s[1:-1]
    elif s.startswith(r'\(') and s.endswith(r'\)') and len(s) >= 4:
        s = s[2:-2]
    for p, r in MATH_REPLACEMENTS:
        s = re.sub(p, r, s)
    # Substituir símbolos fora do charset ANSI do Word que causam glifo de quadrado [?]
    s = s.replace('ℝ', 'R').replace('ℕ', 'N').replace('ℤ', 'Z').replace('ℚ', 'Q')
    return s

def is_complex_math(m_str: str) -> bool:
    """Identifica se uma expressão matemática inline requer renderização gráfica por frações ou raízes."""
    clean = m_str
    if clean.startswith('$') and clean.endswith('$'):
        clean = clean[1:-1]
    elif clean.startswith(r'\(') and clean.endswith(r'\)'):
        clean = clean[2:-2]
    return (r'\frac' in clean) or (r'\sqrt' in clean)

def clean_html_tags_keep_spaces(html_text: str) -> str:
    """Remove tags HTML mantendo quebras de linha e sem remover espaços entre palavras."""
    if not html_text:
        return ""
    s = html.unescape(html_text)
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.IGNORECASE)
    s = re.sub(r'</p>', '\n', s, flags=re.IGNORECASE)
    s = re.sub(r'<[^>]+>', '', s)
    return s

def get_image_stream(url_or_path: str) -> Optional[io.BytesIO]:
    """Retorna um stream BytesIO contendo a imagem para inserção no DOCX."""
    if not url_or_path:
        return None
    try:
        b64_uri = resolve_image_to_base64(url_or_path)
        if b64_uri and b64_uri.startswith("data:image/"):
            data_part = b64_uri.split(",", 1)[1]
            image_data = base64.b64decode(data_part)
            return io.BytesIO(image_data)
    except Exception:
        pass
    return None

def generate_exam_docx_bytes(exam: Dict[str, Any], show_answers: bool = False) -> bytes:
    """
    Gera um arquivo Microsoft Word (.docx) oficial que replica EXATAMENTE o visual do PDF:
    - O Cabeçalho Institucional completo SÓ É EXIBIDO se o usuário tiver configurado/marcado isso;
    - Se desmarcado, exibe apenas o título centralizado limpo com divisor sólido idêntico ao PDF;
    - Cartões de questão ultracompactos, eliminando parágrafos vazios e espaços mortos;
    - Selos circulares nítidos para alternativas sem [?];
    - Sem corte de cartões pela metade entre colunas (<w:cantSplit/>).
    """
    if not HAVE_DOCX:
        raise RuntimeError("O módulo python-docx não está instalado no servidor. Execute: pip install python-docx")

    doc = Document()

    # 1. Configurações de Página (A4) e Margens definidas pelo usuário
    raw_top = float(exam.get("margin_top") if exam.get("margin_top") is not None else (exam.get("margins", {}).get("top") or 3.0))
    raw_bottom = float(exam.get("margin_bottom") if exam.get("margin_bottom") is not None else (exam.get("margins", {}).get("bottom") or 2.0))
    raw_left = float(exam.get("margin_left") if exam.get("margin_left") is not None else (exam.get("margins", {}).get("left") or 3.0))
    raw_right = float(exam.get("margin_right") if exam.get("margin_right") is not None else (exam.get("margins", {}).get("right") or 2.0))

    top_cm = raw_top / 10.0 if raw_top > 5.0 else raw_top
    bottom_cm = raw_bottom / 10.0 if raw_bottom > 5.0 else raw_bottom
    left_cm = raw_left / 10.0 if raw_left > 5.0 else raw_left
    right_cm = raw_right / 10.0 if raw_right > 5.0 else raw_right

    header_section = doc.sections[0]
    header_section.page_width = Inches(8.27)   # 21.0 cm (A4)
    header_section.page_height = Inches(11.69) # 29.7 cm (A4)
    header_section.top_margin = Inches(top_cm / 2.54)
    header_section.bottom_margin = Inches(bottom_cm / 2.54)
    header_section.left_margin = Inches(left_cm / 2.54)
    header_section.right_margin = Inches(right_cm / 2.54)

    # Largura útil total da página em inches
    usable_width = 8.27 - (left_cm + right_cm) / 2.54

    title = exam.get("title") or "AVALIAÇÃO BIMESTRAL"

    # Verificar estritamente se o usuário configurou para exibir o cabeçalho completo:
    # Se o usuário não marcou ou marcou falso, NÃO exibe o cabeçalho institucional!
    raw_inc = exam.get("include_header")
    if raw_inc is not None:
        include_header = bool(raw_inc) and str(raw_inc).lower() not in ("false", "0")
    else:
        # Se não fornecido explicitamente, só exibe se header_style for expressamente standard
        include_header = (exam.get("header_style") == "standard")

    if not include_header:
        # Padrão Limpo (Título Centralizado com linha divisória sólida - idêntico ao PDF!)
        p_th = doc.add_paragraph()
        p_th.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_th.paragraph_format.space_before = Pt(0)
        p_th.paragraph_format.space_after = Pt(8)

        # Borda inferior sólida de 2pt cor #0F172A
        pPr = p_th._element.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        b_bottom = OxmlElement('w:bottom')
        b_bottom.set(qn('w:val'), 'single')
        b_bottom.set(qn('w:sz'), '16') # 2pt
        b_bottom.set(qn('w:space'), '6')
        b_bottom.set(qn('w:color'), '0F172A')
        pBdr.append(b_bottom)
        pPr.append(pBdr)

        r_th = p_th.add_run(title.upper())
        r_th.bold = True
        r_th.font.name = "Arial"
        r_th.font.size = Pt(13.0)
        r_th.font.color.rgb = RGBColor(15, 23, 42)
    else:
        # Cabeçalho Institucional Oficial Completo Alinhado e Sem Quebra Indevida de Linha
        school_name = exam.get("school_name") or exam.get("institution_line3") or "ESCOLA MUNICIPAL DE EDUCAÇÃO BÁSICA"
        inst1 = exam.get("institution_line1") or exam.get("institution") or "PREFEITURA MUNICIPAL DE LAGOA DA CANOA"
        inst2 = exam.get("institution_line2") or "SECRETARIA MUNICIPAL DE EDUCAÇÃO"
        discipline = exam.get("discipline") or "MATEMÁTICA"
        class_name = exam.get("grade_year") or exam.get("class_name") or exam.get("grade") or "9º ANO"
        classroom = exam.get("classroom") or "TURMA A"
        shift = exam.get("shift") or "MATUTINO"
        teacher = exam.get("teacher_name") or ""
        date_val = exam.get("exam_date") or exam.get("date") or "2026"
        score_val = float(exam.get("max_score") or exam.get("total_score") or 10.0)
        score_label = f"{score_val:g}".replace(".", ",")

        header_table = doc.add_table(rows=4, cols=2)
        header_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        logo_w = Inches(1.15)
        rest_w = Inches(usable_width - 1.15)

        # Borda externa sutil 1.0pt (#1E293B) no cabeçalho institucional
        tblPr = header_table._element.xpath('w:tblPr')
        if tblPr:
            tblBorders = OxmlElement('w:tblBorders')
            for b_name in ['top', 'left', 'bottom', 'right']:
                b = OxmlElement(f'w:{b_name}')
                b.set(qn('w:val'), 'single')
                b.set(qn('w:sz'), '8') # 1.0pt
                b.set(qn('w:color'), '1E293B')
                tblBorders.append(b)
            for b_name in ['insideH', 'insideV']:
                b = OxmlElement(f'w:{b_name}')
                b.set(qn('w:val'), 'none')
                tblBorders.append(b)
            tblPr[0].append(tblBorders)

        # Linha 0: Brasão Municipal + Hierarquia de Ensino
        row0 = header_table.rows[0]
        c0_0 = row0.cells[0]
        c0_1 = row0.cells[1]
        c0_0.width = logo_w
        c0_1.width = rest_w
        set_cell_margins(c0_0, top=40, bottom=40, left=50, right=50)
        set_cell_margins(c0_1, top=40, bottom=40, left=50, right=50)
        c0_0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        c0_1.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        logo_path = get_official_logo_path()
        if logo_path:
            p_logo = c0_0.paragraphs[0]
            p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_logo.paragraph_format.space_before = Pt(0)
            p_logo.paragraph_format.space_after = Pt(0)
            p_logo.add_run().add_picture(logo_path, width=Inches(0.9))

        p_inst = c0_1.paragraphs[0]
        p_inst.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_inst.paragraph_format.space_before = Pt(0)
        p_inst.paragraph_format.space_after = Pt(0)
        p_inst.paragraph_format.line_spacing = 1.12

        r1 = p_inst.add_run(inst1.upper() + "\n")
        r1.bold = True
        r1.font.name = "Arial"
        r1.font.size = Pt(9.0)
        r1.font.color.rgb = RGBColor(15, 23, 42)

        r2 = p_inst.add_run(inst2.upper() + "\n")
        r2.bold = True
        r2.font.name = "Arial"
        r2.font.size = Pt(7.5)
        r2.font.color.rgb = RGBColor(71, 85, 105)

        r3 = p_inst.add_run(school_name.upper())
        r3.bold = True
        r3.font.name = "Arial"
        r3.font.size = Pt(9.0)
        r3.font.color.rgb = RGBColor(30, 58, 138)

        # Linha 1: Faixa de Título em Azul Escuro (#1E293B) com Texto Branco
        row1 = header_table.rows[1]
        c1 = row1.cells[0]
        c1.merge(row1.cells[1])
        c1.width = Inches(usable_width)
        set_cell_background(c1, "1E293B")
        set_cell_margins(c1, top=30, bottom=30, left=50, right=50)
        p_banner = c1.paragraphs[0]
        p_banner.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_banner.paragraph_format.space_before = Pt(0)
        p_banner.paragraph_format.space_after = Pt(0)
        banner_text = title.upper()
        if discipline and discipline.upper() not in banner_text:
            banner_text = f"{banner_text} • {discipline.upper()}"
        rb = p_banner.add_run(banner_text)
        rb.bold = True
        rb.font.name = "Arial"
        rb.font.size = Pt(9.0)
        rb.font.color.rgb = RGBColor(255, 255, 255)

        # Linha 2: Metadados com Fundo Cinza Claro (#F8FAFC)
        row2 = header_table.rows[2]
        c2 = row2.cells[0]
        c2.merge(row2.cells[1])
        c2.width = Inches(usable_width)
        set_cell_background(c2, "F8FAFC")
        set_cell_borders(c2,
            top={'val': 'single', 'sz': '4', 'color': 'CBD5E1'},
            bottom={'val': 'single', 'sz': '4', 'color': 'CBD5E1'}
        )
        set_cell_margins(c2, top=30, bottom=30, left=60, right=60)
        p_meta = c2.paragraphs[0]
        p_meta.paragraph_format.space_before = Pt(0)
        p_meta.paragraph_format.space_after = Pt(0)
        p_meta.paragraph_format.line_spacing = 1.15

        def add_meta_item(p, lbl, val):
            r_l = p.add_run(lbl + " ")
            r_l.bold = True
            r_l.font.name = "Arial"
            r_l.font.size = Pt(7.0)
            r_l.font.color.rgb = RGBColor(71, 85, 105)
            r_v = p.add_run(str(val) + "     ")
            r_v.bold = True
            r_v.font.name = "Arial"
            r_v.font.size = Pt(7.5)
            r_v.font.color.rgb = RGBColor(15, 23, 42)

        prof_display = teacher.strip() if teacher.strip() else "Prof. Não Informado"
        add_meta_item(p_meta, "PROFESSOR(A):", prof_display)
        add_meta_item(p_meta, "DATA:", date_val or "__/__/2026")
        add_meta_item(p_meta, "ANO/SÉRIE:", class_name or "9º ANO")
        add_meta_item(p_meta, "TURMA:", classroom)
        add_meta_item(p_meta, "TURNO:", shift)

        # Linha 3: Linha do Estudante & Caixa de Nota à Direita (Sem quebra de linha de underscores)
        row3 = header_table.rows[3]
        c3_0 = row3.cells[0]
        c3_1 = row3.cells[1]
        c3_0.width = Inches(usable_width - 1.5)
        c3_1.width = Inches(1.5)
        set_cell_background(c3_0, "FFFFFF")
        set_cell_background(c3_1, "FFFFFF")
        set_cell_margins(c3_0, top=35, bottom=35, left=60, right=40)
        set_cell_margins(c3_1, top=35, bottom=35, left=40, right=60)
        c3_0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        c3_1.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        p_stud = c3_0.paragraphs[0]
        p_stud.paragraph_format.space_before = Pt(0)
        p_stud.paragraph_format.space_after = Pt(0)
        r_sl = p_stud.add_run("ESTUDANTE: ")
        r_sl.bold = True
        r_sl.font.name = "Arial"
        r_sl.font.size = Pt(8.0)
        r_sl.font.color.rgb = RGBColor(15, 23, 42)

        # 30 underscores cabem perfeitamente na célula sem quebrar para a linha 2
        r_sline = p_stud.add_run("______________________________  ")
        r_sline.font.name = "Arial"
        r_sline.font.size = Pt(8.0)
        r_sline.font.color.rgb = RGBColor(15, 23, 42)

        r_sn = p_stud.add_run("Nº: ")
        r_sn.bold = True
        r_sn.font.name = "Arial"
        r_sn.font.size = Pt(8.0)
        r_sn.font.color.rgb = RGBColor(15, 23, 42)

        r_snline = p_stud.add_run("____")
        r_snline.font.name = "Arial"
        r_snline.font.size = Pt(8.0)
        r_snline.font.color.rgb = RGBColor(15, 23, 42)

        # Box de nota à direita
        p_grade = c3_1.paragraphs[0]
        p_grade.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_grade.paragraph_format.space_before = Pt(0)
        p_grade.paragraph_format.space_after = Pt(0)
        r_gl = p_grade.add_run("NOTA: [ ____ / ")
        r_gl.bold = True
        r_gl.font.name = "Arial"
        r_gl.font.size = Pt(7.8)
        r_gl.font.color.rgb = RGBColor(15, 23, 42)

        r_gv = p_grade.add_run(f"{score_label} ]")
        r_gv.bold = True
        r_gv.font.name = "Arial"
        r_gv.font.size = Pt(7.8)
        r_gv.font.color.rgb = RGBColor(15, 23, 42)

        # Espaçador sutil após o cabeçalho institucional
        p_sep = doc.add_paragraph()
        p_sep.paragraph_format.space_before = Pt(0)
        p_sep.paragraph_format.space_after = Pt(3)
        p_sep.paragraph_format.line_spacing = Pt(3)

    # 2. Configurar Seção das Questões com Colunas e Divisor Vertical (column-rule)
    columns_layout = int(exam.get("columns_layout") or exam.get("columns") or 2)
    gap_in = 0.315 # 8mm

    if columns_layout == 2:
        body_section = doc.add_section(WD_SECTION_START.CONTINUOUS)
        body_section.top_margin = Inches(top_cm / 2.54)
        body_section.bottom_margin = Inches(bottom_cm / 2.54)
        body_section.left_margin = Inches(left_cm / 2.54)
        body_section.right_margin = Inches(right_cm / 2.54)

        sectPr = body_section._sectPr
        cols = sectPr.xpath('./w:cols')
        if not cols:
            cols = [OxmlElement('w:cols')]
            sectPr.append(cols[0])
        cols[0].set(qn('w:num'), '2')
        cols[0].set(qn('w:space'), '454') # ~8mm
        cols[0].set(qn('w:sep'), '1')     # Traço vertical column-rule
        cols[0].set(qn('w:equalWidth'), '1')
        col_width_in = (usable_width - gap_in) / 2.0
    else:
        col_width_in = usable_width

    # 3. Renderização Fiel das Questões em Cartões (.question-card) ULTRACOMPACTOS
    questions = exam.get("questions") or []
    for idx, q in enumerate(questions, 1):
        q_num = q.get("question_number") or q.get("number") or idx
        pts = float(q.get("points") or 1.0)
        pts_str = f"({pts:g} ponto{'s' if pts != 1.0 else ''})".replace(".", ",")

        # Criar a Tabela-Cartão com Borda Cinza Sutil (#E2E8F0)
        card_table = doc.add_table(rows=1, cols=1)
        card_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        card_cell = card_table.rows[0].cells[0]
        card_cell.width = Inches(col_width_in)

        # PREVENIR QUEBRA DO CARTÃO AO MEIO ENTRE COLUNAS (<w:cantSplit/>)
        trPr = card_table.rows[0]._tr.get_or_add_trPr()
        trPr.append(OxmlElement('w:cantSplit'))

        set_cell_background(card_cell, "FFFFFF")
        # Margens internas ultracompactas (sem espaço morto)
        set_cell_margins(card_cell, top=40, bottom=40, left=70, right=70)
        set_cell_borders(card_cell,
            top={'val': 'single', 'sz': '4', 'color': 'E2E8F0'},
            bottom={'val': 'single', 'sz': '4', 'color': 'E2E8F0'},
            left={'val': 'single', 'sz': '4', 'color': 'E2E8F0'},
            right={'val': 'single', 'sz': '4', 'color': 'E2E8F0'}
        )

        # REUTILIZAR o primeiro parágrafo existente na célula (elimina os 3 parágrafos vazios que causavam espaço excessivo!)
        p_hdr = card_cell.paragraphs[0]
        p_hdr.paragraph_format.space_before = Pt(0)
        p_hdr.paragraph_format.space_after = Pt(2.5)
        # Parada de tabulação à direita para alinhar os pontos no final da linha
        p_hdr.paragraph_format.tab_stops.add_tab_stop(Inches(col_width_in - 0.12), WD_TAB_ALIGNMENT.RIGHT)

        # Borda inferior divisória sutil (#F1F5F9) no próprio cabeçalho
        pPr = p_hdr._element.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bbdr = OxmlElement('w:bottom')
        bbdr.set(qn('w:val'), 'single')
        bbdr.set(qn('w:sz'), '4')
        bbdr.set(qn('w:space'), '2')
        bbdr.set(qn('w:color'), 'F1F5F9')
        pBdr.append(bbdr)
        pPr.append(pBdr)

        # Tag [QUESTÃO 01] com fundo azul-claro (#EFF6FF)
        rq = p_hdr.add_run(f" QUESTÃO {q_num:02d} ")
        rq.bold = True
        rq.font.name = "Arial"
        rq.font.size = Pt(8.5)
        rq.font.color.rgb = RGBColor(30, 58, 138)
        rPr = rq._element.get_or_add_rPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), 'EFF6FF')
        rPr.append(shd)

        # Tabulação para empurrar os pontos para a direita
        p_hdr.add_run("\t")

        # Pontuação à direita
        rp = p_hdr.add_run(pts_str)
        rp.font.name = "Arial"
        rp.font.size = Pt(8.0)
        rp.font.color.rgb = RGBColor(100, 116, 139)

        # Renderização do Enunciado (.q-statement)
        raw_stmt = q.get("statement") or ""

        # Dividir enunciado em blocos matemáticos ($$...$$ ou \[...\]), imagens inline (<img...>) e texto
        parts = re.split(r'(\$\$.*?\$\$|\\\[.*?\\\]|<img\s+[^>]*?src=["\'][^"\']+["\'][^>]*?>)', raw_stmt, flags=re.DOTALL | re.IGNORECASE)
        for part in parts:
            if not part:
                continue
            part_str = part.strip()
            if (part_str.startswith('$$') and part_str.endswith('$$')) or (part_str.startswith(r'\[') and part_str.endswith(r'\]')):
                # Fórmula matemática em destaque/bloco
                buf = render_math_to_png(part_str, fontsize=12)
                p_math = card_cell.add_paragraph()
                p_math.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_math.paragraph_format.space_before = Pt(1.0)
                p_math.paragraph_format.space_after = Pt(2.0)
                if buf:
                    p_math.add_run().add_picture(buf)
                else:
                    r = p_math.add_run(clean_inline_math(part_str))
                    r.font.name = "Arial"
                    r.font.size = Pt(9.5)
            elif part_str.startswith('<img') or part_str.startswith('<IMG'):
                # Imagem inline inserida no enunciado
                src_match = re.search(r'src=["\']([^"\']+)["\']', part_str, flags=re.IGNORECASE)
                if src_match:
                    src = src_match.group(1)
                    img_buf = get_image_stream(src)
                    if img_buf:
                        p_iimg = card_cell.add_paragraph()
                        p_iimg.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_iimg.paragraph_format.space_before = Pt(1.5)
                        p_iimg.paragraph_format.space_after = Pt(1.5)
                        max_w = Inches(min(col_width_in * 0.85, 2.0))
                        p_iimg.add_run().add_picture(img_buf, width=max_w)
            else:
                # Bloco de texto com suporte a KaTeX inline sem perda de espaçamento
                cleaned_block = clean_html_tags_keep_spaces(part)
                lines = re.split(r'\n+', cleaned_block)
                for line in lines:
                    if not line.strip():
                        continue
                    p_txt = card_cell.add_paragraph()
                    p_txt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p_txt.paragraph_format.space_before = Pt(0)
                    p_txt.paragraph_format.space_after = Pt(1.5)
                    p_txt.paragraph_format.line_spacing = 1.14

                    inlines = re.split(r'(\$.*?\$|\\\(.*?\\\))', line)
                    for seg in inlines:
                        if not seg:
                            continue
                        is_m = (seg.startswith('$') and seg.endswith('$') and len(seg) > 2) or (seg.startswith(r'\(') and seg.endswith(r'\)') and len(seg) > 4)
                        if is_m:
                            if is_complex_math(seg):
                                buf = render_math_to_png(seg, fontsize=10.0)
                                if buf:
                                    p_txt.add_run().add_picture(buf, height=Pt(13.0))
                                else:
                                    r = p_txt.add_run(clean_inline_math(seg))
                                    r.font.name = "Arial"
                                    r.font.size = Pt(9.5)
                                    r.font.color.rgb = RGBColor(30, 41, 59)
                            else:
                                r = p_txt.add_run(clean_inline_math(seg))
                                r.font.name = "Arial"
                                r.font.size = Pt(9.5)
                                r.font.color.rgb = RGBColor(30, 41, 59)
                        else:
                            r = p_txt.add_run(seg)
                            r.font.name = "Arial"
                            r.font.size = Pt(9.5)
                            r.font.color.rgb = RGBColor(30, 41, 59)

        # Imagem anexada à questão (.q-image-box)
        img_url = q.get("image_url")
        if img_url:
            img_stream = get_image_stream(img_url)
            if img_stream:
                p_img = card_cell.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(1.5)
                p_img.paragraph_format.space_after = Pt(1.5)
                raw_w = q.get("image_width") or "50%"
                try:
                    pct = float(str(raw_w).replace("%", "")) / 100.0 if "%" in str(raw_w) else 0.8
                    w_calc = max(col_width_in * pct, 1.2)
                except Exception:
                    w_calc = col_width_in * 0.8
                max_w = Inches(min(w_calc, 2.2))
                p_img.add_run().add_picture(img_stream, width=max_w)

                if q.get("image_caption"):
                    p_cap = card_cell.add_paragraph()
                    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_cap.paragraph_format.space_before = Pt(0)
                    p_cap.paragraph_format.space_after = Pt(1.5)
                    r_cap = p_cap.add_run(q.get("image_caption"))
                    r_cap.font.name = "Arial"
                    r_cap.font.size = Pt(7.5)
                    r_cap.font.italic = True
                    r_cap.font.color.rgb = RGBColor(100, 116, 139)

        # Alternativas (.alt-row) com Selos Circulares Gráficos
        alts = q.get("alternatives") or []
        correct_ans = str(q.get("correct_letter") or q.get("answer") or "").upper()

        for alt in alts:
            alt_letter = str(alt.get("letter") or "").upper()
            raw_alt_text = alt.get("text") or ""
            is_correct = (alt_letter == correct_ans) and show_answers

            p_alt = card_cell.add_paragraph()
            p_alt.paragraph_format.space_before = Pt(0.5)
            p_alt.paragraph_format.space_after = Pt(0.8)
            p_alt.paragraph_format.line_spacing = 1.12
            p_alt.paragraph_format.left_indent = Inches(0.04)

            # Formato textual requerido pelo usuário no .docx: "( A )  ", "( B )  ", "( C )  ", "( D )  "
            r_circ = p_alt.add_run(f"( {alt_letter} )  ")
            r_circ.bold = True
            r_circ.font.name = "Arial"
            r_circ.font.size = Pt(8.5)
            if is_correct:
                r_circ.font.color.rgb = RGBColor(21, 128, 61)
            else:
                r_circ.font.color.rgb = RGBColor(15, 23, 42)

            # Texto da alternativa com preservação de matemática
            if raw_alt_text:
                cleaned_alt = clean_html_tags_keep_spaces(raw_alt_text)
                inlines = re.split(r'(\$.*?\$|\\\(.*?\\\))', cleaned_alt)
                for seg in inlines:
                    if not seg:
                        continue
                    is_m = (seg.startswith('$') and seg.endswith('$') and len(seg) > 2) or (seg.startswith(r'\(') and seg.endswith(r'\)') and len(seg) > 4)
                    if is_m:
                        if is_complex_math(seg):
                            buf = render_math_to_png(seg, fontsize=9.0)
                            if buf:
                                p_alt.add_run().add_picture(buf, height=Pt(12.0))
                            else:
                                r = p_alt.add_run(clean_inline_math(seg))
                                r.font.name = "Arial"
                                r.font.size = Pt(9.0)
                                if is_correct:
                                    r.font.bold = True
                                    r.font.color.rgb = RGBColor(21, 128, 61)
                                else:
                                    r.font.color.rgb = RGBColor(30, 41, 59)
                        else:
                            r = p_alt.add_run(clean_inline_math(seg))
                            r.font.name = "Arial"
                            r.font.size = Pt(9.0)
                            if is_correct:
                                r.font.bold = True
                                r.font.color.rgb = RGBColor(21, 128, 61)
                            else:
                                r.font.color.rgb = RGBColor(30, 41, 59)
                    else:
                        r = p_alt.add_run(seg)
                        r.font.name = "Arial"
                        r.font.size = Pt(9.0)
                        if is_correct:
                            r.font.bold = True
                            r.font.color.rgb = RGBColor(21, 128, 61)
                        else:
                            r.font.color.rgb = RGBColor(30, 41, 59)

            if is_correct:
                r_tag = p_alt.add_run("  [GABARITO]")
                r_tag.bold = True
                r_tag.font.name = "Arial"
                r_tag.font.size = Pt(8.0)
                r_tag.font.color.rgb = RGBColor(21, 128, 61)

            # Imagem anexada à alternativa
            raw_aimg = alt.get("image_url") or (alt.get("image", {}).get("url") if isinstance(alt.get("image"), dict) else "")
            if raw_aimg:
                alt_stream = get_image_stream(raw_aimg)
                if alt_stream:
                    p_aimg = card_cell.add_paragraph()
                    p_aimg.paragraph_format.left_indent = Inches(0.2)
                    p_aimg.paragraph_format.space_before = Pt(1)
                    p_aimg.paragraph_format.space_after = Pt(1.5)
                    p_aimg.add_run().add_picture(alt_stream, width=Inches(min(col_width_in * 0.7, 1.4)))

        # Espaçador ultracompacto entre cartões
        p_sp = doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(0)
        p_sp.paragraph_format.space_after = Pt(2.5)
        p_sp.paragraph_format.line_spacing = Pt(2.5)

    # 4. Tabela de Gabarito (Rascunho do Aluno)
    include_answer_sheet = exam.get("include_answer_sheet")
    if include_answer_sheet is None:
        include_answer_sheet = exam.get("show_gabarito", True)
    else:
        include_answer_sheet = bool(include_answer_sheet)

    if include_answer_sheet and questions:
        p_gab = doc.add_paragraph()
        p_gab.paragraph_format.space_before = Pt(4)
        p_gab.paragraph_format.space_after = Pt(2)
        r_gt = p_gab.add_run("GABARITO DE RESPOSTAS (RASCUNHO DO ALUNO)")
        r_gt.bold = True
        r_gt.font.name = "Arial"
        r_gt.font.size = Pt(8.0)
        r_gt.font.color.rgb = RGBColor(15, 23, 42)

        q_count = len(questions)
        rows_count = (q_count + 1) // 2
        gab_table = doc.add_table(rows=rows_count, cols=4)
        gab_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders_none(gab_table)

        for r_idx in range(rows_count):
            q1_idx = r_idx
            q2_idx = r_idx + rows_count

            if q1_idx < q_count:
                q_num = questions[q1_idx].get("question_number") or questions[q1_idx].get("number") or (q1_idx + 1)
                c_lbl = gab_table.cell(r_idx, 0)
                c_lbl.width = Inches(0.45)
                c_lbl.paragraphs[0].text = f"Q{q_num:02d}:"
                c_lbl.paragraphs[0].runs[0].font.name = "Arial"
                c_lbl.paragraphs[0].runs[0].font.size = Pt(7.5)
                c_lbl.paragraphs[0].runs[0].bold = True

                c_opt = gab_table.cell(r_idx, 1)
                c_opt.width = Inches(1.2)
                p_opt = c_opt.paragraphs[0]
                p_opt.text = "( A )  ( B )  ( C )  ( D )  ( E )" if len(questions[q1_idx].get("alternatives") or []) >= 5 else "( A )  ( B )  ( C )  ( D )"
                p_opt.runs[0].font.name = "Arial"
                p_opt.runs[0].font.size = Pt(7.5)
                p_opt.runs[0].font.color.rgb = RGBColor(71, 85, 105)

            if q2_idx < q_count:
                q_num2 = questions[q2_idx].get("question_number") or questions[q2_idx].get("number") or (q2_idx + 1)
                c_lbl2 = gab_table.cell(r_idx, 2)
                c_lbl2.width = Inches(0.45)
                c_lbl2.paragraphs[0].text = f"Q{q_num2:02d}:"
                c_lbl2.paragraphs[0].runs[0].font.name = "Arial"
                c_lbl2.paragraphs[0].runs[0].font.size = Pt(7.5)
                c_lbl2.paragraphs[0].runs[0].bold = True

                c_opt2 = gab_table.cell(r_idx, 3)
                c_opt2.width = Inches(1.2)
                p_opt2 = c_opt2.paragraphs[0]
                p_opt2.text = "( A )  ( B )  ( C )  ( D )  ( E )" if len(questions[q2_idx].get("alternatives") or []) >= 5 else "( A )  ( B )  ( C )  ( D )"
                p_opt2.runs[0].font.name = "Arial"
                p_opt2.runs[0].font.size = Pt(7.5)
                p_opt2.runs[0].font.color.rgb = RGBColor(71, 85, 105)

    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()
