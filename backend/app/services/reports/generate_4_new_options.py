import os
import sys
import base64
import io
import subprocess
import qrcode
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
workspace_sheets = os.path.join(backend_dir, "storage", "sheets")
project_root = os.path.dirname(backend_dir)
artifact_dir = r"C:\Users\Lagoa da Canoa\.gemini\antigravity-ide\brain\d41159d4-3d40-4e8f-874a-737221f95ae0"

os.makedirs(workspace_sheets, exist_ok=True)
os.makedirs(artifact_dir, exist_ok=True)

# 1. Generate ArUco Marker Base64
def make_aruco_base64(marker_id: int, size: int = 120) -> str:
    try:
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        marker_img = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
    except AttributeError:
        dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        marker_img = cv2.aruco.drawMarker(dictionary, marker_id, size)
    pil_img = Image.fromarray(marker_img)
    buffered = io.BytesIO()
    pil_img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

aruco_0 = make_aruco_base64(0)
aruco_1 = make_aruco_base64(1)
aruco_2 = make_aruco_base64(2)
aruco_3 = make_aruco_base64(3)

# 2. Generate Student QR Code Base64
def make_qr_base64(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

qr_b64 = make_qr_base64("E:M0802|S:2026.08.10492")

# 3. Build Table OMR Grid matching Image 2 (2 columns of 11 questions = 22 questions)
def build_table_omr(num_questions=22, num_alts=4, theme_header="#1e3a5f"):
    options = ["A", "B", "C", "D"][:num_alts]
    half = (num_questions + 1) // 2
    
    def render_col(start_idx, end_idx):
        h = f"""
        <table class="omr-table">
            <thead>
                <tr>
                    <th class="th-item" style="background: {theme_header};">ITEM</th>
                    {"".join([f'<th class="th-opt">{opt}</th>' for opt in options])}
                </tr>
            </thead>
            <tbody>
        """
        for q in range(start_idx, end_idx + 1):
            h += f"""
                <tr>
                    <td class="td-item">{q:02d}</td>
                    {"".join([f'<td class="td-opt"><span class="bubble">{opt}</span></td>' for opt in options])}
                </tr>
            """
        h += "</tbody></table>"
        return h

    col1 = render_col(1, half)
    col2 = render_col(half + 1, num_questions)

    return f"""
    <div class="table-omr-wrapper">
        <div class="omr-half">{col1}</div>
        <div class="omr-half">{col2}</div>
    </div>
    """

omr_table_html = build_table_omr(22, 4, theme_header="#1d3557")

# Shared base CSS for all 4 new options
BASE_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Poppins:wght@600;700;800&family=Space+Mono:wght@700&display=swap');

@page {{
    size: 210mm 297mm;
    margin: 0;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: #fff;
    font-family: 'Montserrat', Arial, sans-serif;
    color: #333;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
}}
.capa {{
    width: 210mm;
    height: 297mm;
    position: relative;
    overflow: hidden;
    margin: 0 auto;
    background: #fff;
}}

/* Marcadores ArUco nos 4 cantos */
.aruco-mark {{
    position: absolute;
    width: 14mm;
    height: 14mm;
    z-index: 50;
}}
.aruco-mark img {{
    width: 100%;
    height: 100%;
    display: block;
}}
.aruco-mark.tl {{ top: 8mm; left: 8mm; }}
.aruco-mark.tr {{ top: 8mm; right: 8mm; }}
.aruco-mark.bl {{ bottom: 8mm; left: 8mm; }}
.aruco-mark.br {{ bottom: 8mm; right: 8mm; }}

/* 3-Tier Caderno Badge (conforme Imagem 1) */
.caderno-badge-3tier {{
    position: absolute;
    top: 14mm;
    right: 18mm;
    width: 48mm;
    border-radius: 4mm;
    overflow: hidden;
    box-shadow: 0 3mm 8mm rgba(0,0,0,0.25);
    z-index: 10;
    text-align: center;
    border: 1.2px solid rgba(255,255,255,0.4);
}}
.cb-top {{
    background: #10243e;
    color: #fff;
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 2px;
    padding: 2.2mm 0;
    text-transform: uppercase;
}}
.cb-mid {{
    background: #3a6b88;
    color: #fff;
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 2.5mm 0;
    text-transform: uppercase;
}}
.cb-bot {{
    background: #ffffff;
    color: #10243e;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 1.5px;
    padding: 2.5mm 0;
    text-transform: uppercase;
}}

/* Card do Aluno Adaptado: UNIDADE ESCOLAR, NOME, TURMA, TURNO */
.student-card {{
    position: absolute;
    left: 14mm;
    right: 14mm;
    background: #fff;
    border-radius: 3.5mm;
    padding: 4mm 5mm;
    box-shadow: 0 2mm 6mm rgba(0,0,0,0.08);
    z-index: 10;
}}
.student-card-grid {{
    display: flex;
    flex-direction: column;
    gap: 2mm;
}}
.field-row-dual {{
    display: flex;
    gap: 3mm;
}}
.field-box {{
    flex: 1;
    background: #f8fafc;
    border: 1.2px solid #cbd5e1;
    border-radius: 1.8mm;
    padding: 1.6mm 2.8mm;
}}
.field-box.highlight {{
    background: #f1f5f9;
    border-color: #94a3b8;
}}
.field-lbl {{
    font-size: 7.2px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    display: block;
    margin-bottom: 1px;
}}
.field-txt {{
    font-size: 10px;
    font-weight: 700;
    color: #0f172a;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.field-txt.name {{
    font-size: 11.5px;
    font-weight: 800;
    color: #0b192c;
}}

/* Seção de Instruções e Tabela OMR (conforme Imagem 2) */
.omr-section {{
    position: absolute;
    left: 14mm;
    right: 14mm;
    bottom: 24mm;
    z-index: 10;
}}
.omr-instructions-bar {{
    background: #eef7fc;
    border: 1px solid #c9e2f2;
    border-radius: 2mm;
    padding: 2mm 4mm;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 7.5px;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 4mm;
}}
.table-omr-wrapper {{
    display: flex;
    gap: 6mm;
    align-items: flex-start;
}}
.omr-half {{
    flex: 1;
}}
.omr-table {{
    width: 100%;
    border-collapse: collapse;
    background: #fff;
    border: 1px solid #b8d5e5;
    table-layout: fixed;
}}
.omr-table th, .omr-table td {{
    border: 1px solid #cce3ef;
    text-align: center;
}}
.th-item {{
    color: #fff;
    font-size: 8px;
    font-weight: 800;
    padding: 2mm 0;
    width: 22%;
}}
.th-opt {{
    background: #e2eef6;
    color: #1e3a5f;
    font-size: 8.5px;
    font-weight: 800;
    padding: 2mm 0;
    width: 19.5%;
}}
.td-item {{
    background: #f8fafc;
    font-size: 8.5px;
    font-weight: 800;
    color: #1e293b;
    padding: 1.8mm 0;
}}
.td-opt {{
    padding: 1.8mm 0;
    background: #fff;
}}
.bubble {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 5mm;
    height: 5mm;
    border: 1.2px solid #557a95;
    border-radius: 50%;
    font-size: 7px;
    font-weight: 700;
    color: #557a95;
    background: #fff;
}}

/* QR Code no canto inferior direito ao lado do marcador ArUco (conforme Imagem 2) */
.bottom-qr-box {{
    position: absolute;
    bottom: 8mm;
    right: 25mm;
    display: flex;
    align-items: center;
    gap: 2mm;
    z-index: 50;
}}
.bottom-qr-box img {{
    width: 18mm;
    height: 18mm;
    display: block;
}}
"""

# =========================================================================
# OPÇÃO A: CANOA & MONTANHAS AZUL (Fiel às Imagens 1 e 2)
# =========================================================================
html_opA = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{BASE_CSS}
.opA {{ background: #ffffff; }}
.opA .banner-mount {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 74mm;
    background: #c6e6ee;
    z-index: 1;
}}
.opA .year-pill {{
    position: absolute;
    top: 14mm; left: 24mm;
    background: #10243e; color: #fff;
    font-size: 10.5px; font-weight: 800;
    padding: 1.8mm 4.5mm; border-radius: 2mm;
    letter-spacing: 2px; z-index: 10;
}}
.opA h1.title-canoa {{
    position: absolute;
    top: 26mm; left: 24mm;
    font-size: 28px; font-weight: 900;
    color: #ffffff; letter-spacing: 0.5px;
    z-index: 10;
    text-shadow: 0 1.5mm 3mm rgba(16,36,62,0.6);
}}
.opA .student-card {{
    top: 78mm;
    border-left: 3.5mm solid #3a6b88;
    box-shadow: 0 2.5mm 7mm rgba(16,36,62,0.12);
}}
</style>
</head>
<body>
<div class="capa opA">
    <!-- 4 Marcadores ArUco nos cantos -->
    <div class="aruco-mark tl"><img src="data:image/png;base64,{aruco_0}"></div>
    <div class="aruco-mark tr"><img src="data:image/png;base64,{aruco_1}"></div>
    <div class="aruco-mark bl"><img src="data:image/png;base64,{aruco_3}"></div>
    <div class="aruco-mark br"><img src="data:image/png;base64,{aruco_2}"></div>

    <!-- Topo: Montanhas & Canoa (Fiel à Imagem 1) -->
    <div class="banner-mount">
        <svg viewBox="0 0 800 280" preserveAspectRatio="none" style="width:100%; height:100%;">
            <rect width="800" height="280" fill="#c6e6ee"/>
            <!-- Montanhas intermediárias -->
            <path d="M-50 200 L160 70 L340 210 L540 40 L710 180 L850 110 L850 280 L-50 280 Z" fill="#3a6b88"/>
            <!-- Montanhas frontais escuras -->
            <path d="M-50 240 L120 130 L270 240 L410 120 L570 230 L700 150 L850 230 L850 280 L-50 280 Z" fill="#10243e"/>
            <!-- Base da água clara -->
            <path d="M-50 260 Q400 235 850 260 L850 280 L-50 280 Z" fill="#e2f5f8"/>
            <!-- Silhueta da Canoa Dourada -->
            <path d="M330 250 Q400 266 470 250 Q400 258 330 250 Z" fill="#f4b236"/>
        </svg>
    </div>

    <!-- Pílula 2026 e Nome Solicitado PROVA CANOA -->
    <div class="year-pill">2026</div>
    <h1 class="title-canoa">PROVA CANOA</h1>

    <!-- Badge 3 Níveis (conforme Imagem 1) -->
    <div class="caderno-badge-3tier">
        <div class="cb-top">CADERNO</div>
        <div class="cb-mid">MATEMÁTICA</div>
        <div class="cb-bot">8º ANO</div>
    </div>

    <!-- Card do Aluno com os 4 Campos Solicitados -->
    <div class="student-card">
        <div class="student-card-grid">
            <div class="field-box">
                <span class="field-lbl">Unidade Escolar:</span>
                <span class="field-txt">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
            </div>
            <div class="field-box highlight">
                <span class="field-lbl">Nome Completo do(a) Estudante:</span>
                <span class="field-txt name">LUCAS GABRIEL DOS SANTOS SILVA</span>
            </div>
            <div class="field-row-dual">
                <div class="field-box" style="flex: 1.2;">
                    <span class="field-lbl">Turma:</span>
                    <span class="field-txt">8º ANO A</span>
                </div>
                <div class="field-box" style="flex: 1.2;">
                    <span class="field-lbl">Turno:</span>
                    <span class="field-txt">MANHÃ</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Seção OMR com Tabela e Instruções (conforme Imagem 2) -->
    <div class="omr-section">
        <div class="omr-instructions-bar">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ● ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>
        {omr_table_html}
    </div>

    <!-- QR Code de Identificação no Rodapé Direito (ao lado do ArUco) -->
    <div class="bottom-qr-box">
        <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
    </div>
</div>
</body>
</html>
"""

# =========================================================================
# OPÇÃO B: RIO & CANOA VERDE ESMERALDA (Com Badge 3 Níveis & Rio)
# =========================================================================
omr_table_html_teal = build_table_omr(22, 4, theme_header="#0e7c7b")
html_opB = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{BASE_CSS}
.opB {{ background: #ffffff; }}
.opB .banner-rio {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 74mm;
    background: linear-gradient(180deg, #d8f3ec 0%, #edf9f6 100%);
    z-index: 1;
}}
.opB .year-pill {{
    position: absolute;
    top: 14mm; left: 24mm;
    background: #0b5d5c; color: #fff;
    font-size: 10.5px; font-weight: 800;
    padding: 1.8mm 4.5mm; border-radius: 2mm;
    letter-spacing: 2px; z-index: 10;
}}
.opB h1.title-canoa {{
    position: absolute;
    top: 26mm; left: 24mm;
    font-size: 28px; font-weight: 900;
    color: #0b5d5c; letter-spacing: 0.5px;
    z-index: 10;
}}
.opB .student-card {{
    top: 78mm;
    border-left: 3.5mm solid #0e7c7b;
    box-shadow: 0 2.5mm 7mm rgba(14,124,123,0.12);
}}
.opB .caderno-badge-3tier .cb-top {{ background: #0b5d5c; }}
.opB .caderno-badge-3tier .cb-mid {{ background: #0e7c7b; }}
.opB .caderno-badge-3tier .cb-bot {{ color: #0b5d5c; }}
.opB .omr-instructions-bar {{
    background: #e6f7f4; border-color: #b2e6db; color: #0b5d5c;
}}
.opB .bubble {{ border-color: #0e7c7b; color: #0e7c7b; }}
.opB .th-opt {{ background: #e6f7f4; color: #0b5d5c; }}
.opB .omr-table {{ border-color: #b2e6db; }}
.opB .omr-table th, .opB .omr-table td {{ border-color: #c9efe7; }}
</style>
</head>
<body>
<div class="capa opB">
    <div class="aruco-mark tl"><img src="data:image/png;base64,{aruco_0}"></div>
    <div class="aruco-mark tr"><img src="data:image/png;base64,{aruco_1}"></div>
    <div class="aruco-mark bl"><img src="data:image/png;base64,{aruco_3}"></div>
    <div class="aruco-mark br"><img src="data:image/png;base64,{aruco_2}"></div>

    <div class="banner-rio">
        <svg viewBox="0 0 800 280" preserveAspectRatio="none" style="width:100%; height:100%;">
            <path d="M0 160 Q180 80 400 160 T800 160 L800 280 L0 280 Z" fill="#a7e3d6"/>
            <path d="M0 190 Q220 120 420 190 T800 190 L800 280 L0 280 Z" fill="#0e7c7b"/>
            <!-- Canoa com Vela -->
            <path d="M340 165 Q400 188 460 165 Q400 178 340 165 Z" fill="#f4a261"/>
            <line x1="400" y1="163" x2="400" y2="135" stroke="#7a4419" stroke-width="2.5"/>
            <path d="M400 135 Q425 145 400 160 Z" fill="#ffffff"/>
        </svg>
    </div>

    <div class="year-pill">2026</div>
    <h1 class="title-canoa">PROVA CANOA</h1>

    <div class="caderno-badge-3tier">
        <div class="cb-top">CADERNO</div>
        <div class="cb-mid">LÍNGUA PORTUGUESA</div>
        <div class="cb-bot">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="student-card-grid">
            <div class="field-box">
                <span class="field-lbl">Unidade Escolar:</span>
                <span class="field-txt">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
            </div>
            <div class="field-box highlight">
                <span class="field-lbl">Nome Completo do(a) Estudante:</span>
                <span class="field-txt name">LUCAS GABRIEL DOS SANTOS SILVA</span>
            </div>
            <div class="field-row-dual">
                <div class="field-box" style="flex: 1.2;">
                    <span class="field-lbl">Turma:</span>
                    <span class="field-txt">8º ANO B</span>
                </div>
                <div class="field-box" style="flex: 1.2;">
                    <span class="field-lbl">Turno:</span>
                    <span class="field-txt">MANHÃ</span>
                </div>
            </div>
        </div>
    </div>

    <div class="omr-section">
        <div class="omr-instructions-bar">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ● ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>
        {omr_table_html_teal}
    </div>

    <div class="bottom-qr-box">
        <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
    </div>
</div>
</body>
</html>
"""

# =========================================================================
# OPÇÃO C: PÔR DO SOL SOLAR (Laranja e Terracota)
# =========================================================================
omr_table_html_orange = build_table_omr(22, 4, theme_header="#c05621")
html_opC = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{BASE_CSS}
.opC {{ background: #ffffff; }}
.opC .banner-sunset {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 74mm;
    background: linear-gradient(180deg, #ffedd5 0%, #fff7ed 100%);
    z-index: 1;
}}
.opC .sun-shape {{
    position: absolute;
    top: 10mm; right: 72mm;
    width: 24mm; height: 24mm;
    background: radial-gradient(circle, #ffb703 0%, #fb8500 75%);
    border-radius: 50%;
    box-shadow: 0 0 16mm #ffd166;
    z-index: 2;
}}
.opC .year-pill {{
    position: absolute;
    top: 14mm; left: 24mm;
    background: #9a3412; color: #fff;
    font-size: 10.5px; font-weight: 800;
    padding: 1.8mm 4.5mm; border-radius: 2mm;
    letter-spacing: 2px; z-index: 10;
}}
.opC h1.title-canoa {{
    position: absolute;
    top: 26mm; left: 24mm;
    font-size: 28px; font-weight: 900;
    color: #9a3412; letter-spacing: 0.5px;
    z-index: 10;
}}
.opC .student-card {{
    top: 78mm;
    border-left: 3.5mm solid #fb8500;
    box-shadow: 0 2.5mm 7mm rgba(251,133,0,0.12);
}}
.opC .caderno-badge-3tier .cb-top {{ background: #7c2d12; }}
.opC .caderno-badge-3tier .cb-mid {{ background: #ea580c; }}
.opC .caderno-badge-3tier .cb-bot {{ color: #7c2d12; }}
.opC .omr-instructions-bar {{
    background: #fff7ed; border-color: #fed7aa; color: #9a3412;
}}
.opC .bubble {{ border-color: #ea580c; color: #ea580c; }}
.opC .th-opt {{ background: #ffedd5; color: #9a3412; }}
.opC .omr-table {{ border-color: #fed7aa; }}
.opC .omr-table th, .opC .omr-table td {{ border-color: #ffedd5; }}
</style>
</head>
<body>
<div class="capa opC">
    <div class="aruco-mark tl"><img src="data:image/png;base64,{aruco_0}"></div>
    <div class="aruco-mark tr"><img src="data:image/png;base64,{aruco_1}"></div>
    <div class="aruco-mark bl"><img src="data:image/png;base64,{aruco_3}"></div>
    <div class="aruco-mark br"><img src="data:image/png;base64,{aruco_2}"></div>

    <div class="banner-sunset">
        <div class="sun-shape"></div>
        <svg viewBox="0 0 800 280" preserveAspectRatio="none" style="width:100%; height:100%; position:relative; z-index:3;">
            <path d="M0 165 Q180 90 400 165 T800 165 L800 280 L0 280 Z" fill="#fed7aa"/>
            <path d="M0 195 Q220 130 420 195 T800 195 L800 280 L0 280 Z" fill="#ea580c"/>
            <!-- Canoa Solitária -->
            <path d="M340 170 Q400 192 460 170 Q400 182 340 170 Z" fill="#78350f"/>
            <line x1="400" y1="168" x2="400" y2="140" stroke="#451a03" stroke-width="2.5"/>
            <path d="M400 140 Q425 150 400 165 Z" fill="#ffffff"/>
        </svg>
    </div>

    <div class="year-pill">2026</div>
    <h1 class="title-canoa">PROVA CANOA</h1>

    <div class="caderno-badge-3tier">
        <div class="cb-top">CADERNO</div>
        <div class="cb-mid">MATEMÁTICA</div>
        <div class="cb-bot">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="student-card-grid">
            <div class="field-box">
                <span class="field-lbl">Unidade Escolar:</span>
                <span class="field-txt">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
            </div>
            <div class="field-box highlight">
                <span class="field-lbl">Nome Completo do(a) Estudante:</span>
                <span class="field-txt name">LUCAS GABRIEL DOS SANTOS SILVA</span>
            </div>
            <div class="field-row-dual">
                <div class="field-box" style="flex: 1.2;">
                    <span class="field-lbl">Turma:</span>
                    <span class="field-txt">8º ANO A</span>
                </div>
                <div class="field-box" style="flex: 1.2;">
                    <span class="field-lbl">Turno:</span>
                    <span class="field-txt">TARDE</span>
                </div>
            </div>
        </div>
    </div>

    <div class="omr-section">
        <div class="omr-instructions-bar">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ● ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>
        {omr_table_html_orange}
    </div>

    <div class="bottom-qr-box">
        <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
    </div>
</div>
</body>
</html>
"""

# =========================================================================
# OPÇÃO D: ONDAS FLUIDAS / MODERNO NAVY & CIANO
# =========================================================================
omr_table_html_navy = build_table_omr(22, 4, theme_header="#1e293b")
html_opD = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{BASE_CSS}
.opD {{ background: #ffffff; }}
.opD .banner-fluid {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 74mm;
    background: #0f172a;
    z-index: 1;
}}
.opD .year-pill {{
    position: absolute;
    top: 14mm; left: 24mm;
    background: #2563eb; color: #fff;
    font-size: 10.5px; font-weight: 800;
    padding: 1.8mm 4.5mm; border-radius: 2mm;
    letter-spacing: 2px; z-index: 10;
}}
.opD h1.title-canoa {{
    position: absolute;
    top: 26mm; left: 24mm;
    font-size: 28px; font-weight: 900;
    color: #ffffff; letter-spacing: 0.5px;
    z-index: 10;
}}
.opD .student-card {{
    top: 78mm;
    border-left: 3.5mm solid #2563eb;
    box-shadow: 0 2.5mm 7mm rgba(15,23,42,0.12);
}}
.opD .caderno-badge-3tier .cb-top {{ background: #0f172a; }}
.opD .caderno-badge-3tier .cb-mid {{ background: #2563eb; }}
.opD .caderno-badge-3tier .cb-bot {{ color: #0f172a; }}
.opD .omr-instructions-bar {{
    background: #eff6ff; border-color: #bfdbfe; color: #1e3a8a;
}}
.opD .bubble {{ border-color: #2563eb; color: #2563eb; }}
.opD .th-opt {{ background: #eff6ff; color: #1e3a8a; }}
.opD .omr-table {{ border-color: #bfdbfe; }}
.opD .omr-table th, .opD .omr-table td {{ border-color: #dbeafe; }}
</style>
</head>
<body>
<div class="capa opD">
    <div class="aruco-mark tl"><img src="data:image/png;base64,{aruco_0}"></div>
    <div class="aruco-mark tr"><img src="data:image/png;base64,{aruco_1}"></div>
    <div class="aruco-mark bl"><img src="data:image/png;base64,{aruco_3}"></div>
    <div class="aruco-mark br"><img src="data:image/png;base64,{aruco_2}"></div>

    <div class="banner-fluid">
        <svg viewBox="0 0 800 280" preserveAspectRatio="none" style="width:100%; height:100%;">
            <!-- Camadas de ondas fluidas e gradientes -->
            <path d="M0 160 Q200 90 440 160 T800 160 L800 280 L0 280 Z" fill="#1e3a8a"/>
            <path d="M0 195 Q240 130 460 195 T800 195 L800 280 L0 280 Z" fill="#2563eb"/>
            <!-- Silhueta da Canoa Estilizada -->
            <path d="M330 170 Q400 192 470 170 Q400 180 330 170 Z" fill="#38bdf8"/>
        </svg>
    </div>

    <div class="year-pill">2026</div>
    <h1 class="title-canoa">PROVA CANOA</h1>

    <div class="caderno-badge-3tier">
        <div class="cb-top">CADERNO</div>
        <div class="cb-mid">CIÊNCIAS</div>
        <div class="cb-bot">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="student-card-grid">
            <div class="field-box">
                <span class="field-lbl">Unidade Escolar:</span>
                <span class="field-txt">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
            </div>
            <div class="field-box highlight">
                <span class="field-lbl">Nome Completo do(a) Estudante:</span>
                <span class="field-txt name">LUCAS GABRIEL DOS SANTOS SILVA</span>
            </div>
            <div class="field-row-dual">
                <div class="field-box" style="flex: 1.2;">
                    <span class="field-lbl">Turma:</span>
                    <span class="field-txt">8º ANO C</span>
                </div>
                <div class="field-box" style="flex: 1.2;">
                    <span class="field-lbl">Turno:</span>
                    <span class="field-txt">MANHÃ</span>
                </div>
            </div>
        </div>
    </div>

    <div class="omr-section">
        <div class="omr-instructions-bar">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ● ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>
        {omr_table_html_navy}
    </div>

    <div class="bottom-qr-box">
        <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
    </div>
</div>
</body>
</html>
"""

# Save and render the 4 options
options_data = [
    ("opcao_A_montanhas_azul.html", "opcao_A_montanhas_azul", html_opA, "Opção A: Canoa & Montanhas (Azul Marinho / Dourado)"),
    ("opcao_B_rio_verde.html", "opcao_B_rio_verde", html_opB, "Opção B: Rio & Canoa (Verde Esmeralda / Petróleo)"),
    ("opcao_C_sunset_laranja.html", "opcao_C_sunset_laranja", html_opC, "Opção C: Pôr do Sol Solar (Laranja / Âmbar)"),
    ("opcao_D_ondas_navy.html", "opcao_D_ondas_navy", html_opD, "Opção D: Ondas Fluidas (Moderno Navy / Azul Royal)")
]

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

for filename, base_id, content, title in options_data:
    html_file = os.path.join(workspace_sheets, filename)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    pdf_ws = os.path.join(workspace_sheets, f"{base_id}.pdf")
    pdf_art = os.path.join(artifact_dir, f"{base_id}.pdf")
    
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_ws}",
        html_file
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(pdf_ws):
        import shutil
        shutil.copy2(pdf_ws, pdf_art)
        
        doc = fitz.open(pdf_ws)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(180/72.0, 180/72.0), alpha=False)
        png_ws = os.path.join(workspace_sheets, f"{base_id}.png")
        png_art = os.path.join(artifact_dir, f"{base_id}.png")
        pix.save(png_ws)
        pix.save(png_art)
        doc.close()
        print(f"Rendered: {base_id} -> {png_ws}")

# Create Master Visualizer HTML: novas_opcoes_canoa.html
cards_html = ""
for filename, base_id, content, title in options_data:
    cards_html += f"""
    <div class="proposal-card">
        <div class="p-header">
            <h2>{title}</h2>
            <div class="btn-group">
                <a href="backend/storage/sheets/{base_id}.pdf" target="_blank" class="btn btn-p">📄 Abrir PDF (Imprimir A4)</a>
                <a href="backend/storage/sheets/{filename}" target="_blank" class="btn btn-s">🌐 Abrir HTML</a>
            </div>
        </div>
        <div class="p-body">
            <img src="backend/storage/sheets/{base_id}.png" class="preview-img" alt="{title}">
        </div>
    </div>
    """

master_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>4 Novas Opções: PROVA CANOA com Dados Preenchidos & OMR ArUco</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #090d16;
        --surface: #131b2a;
        --border: #222f46;
        --text: #f8fafc;
        --text-muted: #94a3b8;
        --accent: #0284c7;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'Inter', sans-serif;
        background: var(--bg);
        color: var(--text);
        padding: 30px 20px 60px 20px;
    }}
    header {{
        max-width: 1200px;
        margin: 0 auto 30px auto;
        text-align: center;
    }}
    header h1 {{
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8, #0ea5e9, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }}
    header p {{
        color: var(--text-muted);
        font-size: 1.05rem;
    }}
    .callout {{
        margin-top: 15px;
        display: inline-block;
        background: rgba(14, 165, 233, 0.12);
        border: 1px solid rgba(14, 165, 233, 0.35);
        border-radius: 8px;
        padding: 12px 24px;
        color: #7dd3fc;
        font-size: 0.95rem;
        text-align: left;
        max-width: 900px;
    }}
    .callout ul {{
        margin-left: 20px;
        margin-top: 6px;
    }}
    .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
        gap: 30px;
        max-width: 1600px;
        margin: 30px auto 0 auto;
    }}
    .proposal-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: 0 10px 30px -5px rgba(0,0,0,0.5);
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .proposal-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 18px 35px -5px rgba(0,0,0,0.7);
        border-color: #0284c7;
    }}
    .p-header {{
        padding: 20px 24px;
        border-bottom: 1px solid var(--border);
        background: #172235;
    }}
    .p-header h2 {{
        font-size: 1.2rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 12px;
    }}
    .btn-group {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }}
    .btn {{
        display: inline-flex;
        align-items: center;
        padding: 8px 15px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none;
        cursor: pointer;
        transition: all 0.15s;
    }}
    .btn-p {{ background: #0284c7; color: #fff; }}
    .btn-p:hover {{ background: #0369a1; }}
    .btn-s {{ background: #233044; color: #cbd5e1; border: 1px solid #334155; }}
    .btn-s:hover {{ background: #2d3d57; color: #fff; }}
    .p-body {{
        padding: 20px;
        background: #090c15;
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    .preview-img {{
        max-width: 100%;
        height: auto;
        border-radius: 4px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        background: #fff;
    }}
</style>
</head>
<body>
    <header>
        <h1>4 Novas Opções: PROVA CANOA</h1>
        <p>Montadas estritamente com base nos seus pedidos e nas imagens de referência</p>
        <div class="callout">
            <strong>✅ Requisitos Atendidos:</strong>
            <ul>
                <li><strong>Topo Limpo</strong>: Apenas o ano <code>2026</code> e abaixo o nome direto <code>PROVA CANOA</code>.</li>
                <li><strong>Badge 3 Níveis (conforme Imagem 1)</strong>: <code>CADERNO</code> / <code>DISCIPLINA</code> / <code>ANO</code>.</li>
                <li><strong>Card de Identificação</strong>: <code>UNIDADE ESCOLAR</code>, <code>NOME COMPLETO DO(A) ESTUDANTE</code>, <code>TURMA</code> e <code>TURNO</code> (substituindo data de nascimento).</li>
                <li><strong>OMR em Tabela com ArUco e QR Code (conforme Imagem 2)</strong>: Marcadores ArUco nos 4 cantos, tabela de 2 colunas com bolhas, instruções oficiais e QR Code de identificação no rodapé.</li>
            </ul>
        </div>
    </header>

    <main class="grid">
        {cards_html}
    </main>
</body>
</html>
"""

master_html_p = os.path.join(project_root, "novas_opcoes_canoa.html")
with open(master_html_p, "w", encoding="utf-8") as f:
    f.write(master_html)

print("4 Novas opções geradas com sucesso!")
