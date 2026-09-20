import os
import sys
import base64
import io
import subprocess
import qrcode
import fitz  # PyMuPDF
import cv2
import shutil
from PIL import Image

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
workspace_sheets = os.path.join(backend_dir, "storage", "sheets")
project_root = os.path.dirname(backend_dir)
artifact_dir = r"C:\Users\Lagoa da Canoa\.gemini\antigravity-ide\brain\d41159d4-3d40-4e8f-874a-737221f95ae0"

os.makedirs(workspace_sheets, exist_ok=True)
os.makedirs(artifact_dir, exist_ok=True)

# 1. Gerar Marcadores ArUco Base64
def make_aruco_base64(marker_id: int, size: int = 140) -> str:
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

aruco_0 = make_aruco_base64(0)  # TL
aruco_1 = make_aruco_base64(1)  # TR
aruco_2 = make_aruco_base64(2)  # BR
aruco_3 = make_aruco_base64(3)  # BL

# 2. Gerar QR Code do Estudante Base64
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

# 3. Gerador de Tabela OMR (Itens 01-12 e 13-22 conforme Imagem 2)
def build_table_omr_image2(header_bg="#1e3a5f"):
    options = ["A", "B", "C", "D"]
    
    def render_col(start_q, end_q):
        h = f"""
        <table class="omr-table">
            <thead>
                <tr>
                    <th class="th-item" style="background: {header_bg};">ITEM</th>
                    {"".join([f'<th class="th-opt">{opt}</th>' for opt in options])}
                </tr>
            </thead>
            <tbody>
        """
        for q in range(start_q, end_q + 1):
            h += f"""
                <tr>
                    <td class="td-item">{q:02d}</td>
                    {"".join([f'<td class="td-opt"><span class="bubble">{opt}</span></td>' for opt in options])}
                </tr>
            """
        h += "</tbody></table>"
        return h

    col1 = render_col(1, 12)
    col2 = render_col(13, 22)

    return f"""
    <div class="omr-tables-container">
        <div class="omr-col-wrap">{col1}</div>
        <div class="omr-col-wrap">{col2}</div>
    </div>
    """

COMMON_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Poppins:wght@600;700;800;900&family=Space+Mono:wght@700&display=swap');

@page {{
    size: 210mm 297mm;
    margin: 0;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: #ffffff;
    font-family: 'Montserrat', Arial, sans-serif;
    color: #1e293b;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
}}
.capa {{
    width: 210mm;
    height: 297mm;
    position: relative;
    overflow: hidden;
    margin: 0 auto;
    background: #ffffff;
}}

/* =========================================================================
   PARTE SUPERIOR: MARCAÇÃO 2026 E PROVA CANOA (Sem slogans)
   ========================================================================= */
.top-brand {{
    position: absolute;
    top: 13mm;
    left: 16mm;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2.5mm;
}}
.ano-pill {{
    display: inline-block;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 2.5px;
    padding: 1.8mm 5mm;
    border-radius: 20px;
    line-height: 1;
}}
.titulo-prova {{
    font-size: 25px;
    font-weight: 900;
    letter-spacing: 0.5px;
    line-height: 1;
    text-transform: uppercase;
}}

/* Badge do Caderno à Direita (3 níveis: CADERNO / MATEMÁTICA / 8º ANO) */
.badge-caderno-3tier {{
    position: absolute;
    top: 12mm;
    right: 16mm;
    width: 48mm;
    border-radius: 4mm;
    overflow: hidden;
    z-index: 10;
    box-shadow: 0 3mm 8mm rgba(0,0,0,0.22);
    text-align: center;
    border: 1px solid rgba(255,255,255,0.4);
}}
.bc-top {{
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 2.2px;
    padding: 2.2mm 0;
    text-transform: uppercase;
}}
.bc-mid {{
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.2px;
    padding: 2.5mm 0;
    text-transform: uppercase;
}}
.bc-bot {{
    background: #ffffff;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 1.5px;
    padding: 2.2mm 0;
    text-transform: uppercase;
}}

/* =========================================================================
   PARTE DO MEIO: IDENTIFICAÇÃO DO ESTUDANTE (Largo, sem QR Code ao lado)
   ========================================================================= */
.student-card {{
    position: absolute;
    top: 80mm;
    left: 12mm;
    right: 12mm;
    background: #ffffff;
    border-radius: 3.5mm;
    padding: 3.5mm 5mm 4mm 5mm;
    box-shadow: 0 2mm 8mm rgba(0,0,0,0.06);
    border: 1.2px solid #e2e8f0;
    z-index: 15;
}}
.student-card-header {{
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 2mm;
    padding-bottom: 1.5mm;
    border-bottom: 1px solid #f1f5f9;
}}
.student-card-fields {{
    display: flex;
    flex-direction: column;
    gap: 2mm;
}}
.field-block {{
    background: #f8fafc;
    border: 1.2px solid #cbd5e1;
    border-radius: 2mm;
    padding: 1.6mm 3mm;
}}
.field-block.highlight {{
    background: #f1f5f9;
    border-color: #94a3b8;
}}
.field-lbl {{
    font-size: 7px;
    font-weight: 800;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    display: block;
    margin-bottom: 1px;
}}
.field-txt {{
    font-size: 9.8px;
    font-weight: 700;
    color: #0f172a;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.field-txt.name {{
    font-size: 11.5px;
    font-weight: 900;
    color: #0b192c;
    letter-spacing: 0.2px;
}}
.field-row-dual {{
    display: flex;
    gap: 3mm;
}}

/* =========================================================================
   PARTE INFERIOR: ÁREA DE LEITURA ESCANEÁVEL (Apenas a metade inferior)
   ========================================================================= */
.reading-area {{
    position: absolute;
    top: 135mm;
    bottom: 8mm;
    left: 8mm;
    right: 8mm;
    z-index: 20;
}}

/* Marcadores de Registro ArUco nos 4 cantos da Área de Leitura */
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
.aruco-mark.tl {{ top: 2mm; left: 2mm; }}
.aruco-mark.tr {{ top: 2mm; right: 2mm; }}
.aruco-mark.bl {{ bottom: 2mm; left: 2mm; }}
.aruco-mark.br {{ bottom: 2mm; right: 2mm; }}

/* Faixa de Orientações entre os Marcadores Superiores */
.omr-instructions {{
    position: absolute;
    top: 3.5mm;
    left: 20mm;
    right: 20mm;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 7.2px;
    font-weight: 700;
    padding: 2.2mm 4.5mm;
    border-radius: 2mm;
    border: 1px solid #c9e2f2;
    background: #eef7fc;
    color: #1e3a5f;
}}

/* Tabelas de Questões (Item 01-12 e 13-22 conforme Imagem 2) */
.omr-tables-container {{
    position: absolute;
    top: 17mm;
    left: 10mm;
    display: flex;
    gap: 7mm;
    align-items: flex-start;
}}
.omr-col-wrap {{
    width: 72mm;
}}
.omr-table {{
    width: 100%;
    border-collapse: collapse;
    background: #ffffff;
    border: 1.2px solid #b8d5e5;
    table-layout: fixed;
}}
.omr-table th, .omr-table td {{
    border: 1px solid #cce3ef;
    text-align: center;
}}
.th-item {{
    color: #ffffff;
    font-size: 8px;
    font-weight: 900;
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
    padding: 1.6mm 0;
}}
.td-opt {{
    padding: 1.6mm 0;
    background: #ffffff;
}}
.bubble {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 5.2mm;
    height: 5.2mm;
    border: 1.3px solid #557a95;
    border-radius: 50%;
    font-size: 7.2px;
    font-weight: 700;
    color: #557a95;
    background: #ffffff;
}}

/* QR Code de Identificação no Canto Inferior Direito (conforme Imagem 2) */
.scan-qr-box {{
    position: absolute;
    bottom: 2mm;
    right: 22mm;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 45;
}}
.scan-qr-box img {{
    width: 23mm;
    height: 23mm;
    display: block;
}}
"""

# =========================================================================
# OPÇÃO 1: MONTANHAS EM ZIGUEZAGUE & CANOA DOURADA (Fiel às Imagens 1 e 2)
# =========================================================================
table_html_op1 = build_table_omr_image2(header_bg="#0e2a47")

html_op1 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.m1 .topo-art {{ position: absolute; top: 0; left: 0; width: 100%; height: 75mm; z-index: 1; }}
.m1 .ano-pill {{ background: #0e2a47; color: #ffffff; border: 1.5px solid rgba(255,255,255,0.4); }}
.m1 .titulo-prova {{ color: #ffffff; font-family: 'Montserrat', sans-serif; text-shadow: 0 2px 5px rgba(14,42,71,0.5); }}

.m1 .bc-top {{ background: #0e2a47; color: #93c5fd; }}
.m1 .bc-mid {{ background: #2d5a82; color: #ffffff; }}
.m1 .bc-bot {{ color: #0e2a47; }}

.m1 .student-card {{ border-left: 3.5mm solid #1d4ed8; }}
.m1 .omr-instructions {{ background: #e0f2fe; color: #0369a1; border-color: #bae6fd; }}
.m1 .bubble {{ border-color: #1d4ed8; color: #1d4ed8; }}
</style>
</head>
<body>
<div class="capa m1">
    <!-- Topo Vetorial Montanhas e Canoa Dourada -->
    <svg class="topo-art" viewBox="0 0 800 290" preserveAspectRatio="none">
        <rect width="800" height="290" fill="#a5d8ea"/>
        <polygon points="0,190 150,80 300,200 440,60 590,190 700,105 800,190 800,290 0,290" fill="#437b9b"/>
        <polygon points="0,230 120,135 260,235 420,120 560,230 680,150 800,235 800,290 0,290" fill="#0e2a47"/>
        <path d="M0 260 Q 220 232 400 260 T 800 260 V 290 H 0 Z" fill="#e2f3f8"/>
        <path d="M330 250 Q 400 270 470 250 Q 400 260 330 250 Z" fill="#f59e0b"/>
    </svg>

    <!-- Topo Esquerdo: 2026 e PROVA CANOA -->
    <div class="top-brand">
        <div class="ano-pill">2026</div>
        <div class="titulo-prova">PROVA CANOA</div>
    </div>

    <!-- Topo Direito: Badge Caderno 3 Níveis -->
    <div class="badge-caderno-3tier">
        <div class="bc-top">CADERNO</div>
        <div class="bc-mid">MATEMÁTICA</div>
        <div class="bc-bot">8º ANO</div>
    </div>

    <!-- Parte do Meio: Card de Identificação Completo -->
    <div class="student-card">
        <div class="student-card-header">DADOS DO(A) ESTUDANTE &bull; CADERNO M0802</div>
        <div class="student-card-fields">
            <div class="field-block">
                <span class="field-lbl">Unidade Escolar:</span>
                <span class="field-txt">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
            </div>
            <div class="field-block highlight">
                <span class="field-lbl">Nome Completo do(a) Estudante:</span>
                <span class="field-txt name">LUCAS GABRIEL DOS SANTOS SILVA</span>
            </div>
            <div class="field-row-dual">
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turma:</span>
                    <span class="field-txt">8º ANO A</span>
                </div>
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turno:</span>
                    <span class="field-txt">MATUTINO</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Parte Inferior: ÁREA DE LEITURA ESCANEÁVEL (Com 4 Marcadores ArUco e QR Code) -->
    <div class="reading-area">
        <div class="aruco-mark tl"><img src="data:image/png;base64,{aruco_0}" alt="ArUco 0"></div>
        <div class="aruco-mark tr"><img src="data:image/png;base64,{aruco_1}" alt="ArUco 1"></div>
        <div class="aruco-mark bl"><img src="data:image/png;base64,{aruco_3}" alt="ArUco 3"></div>
        <div class="aruco-mark br"><img src="data:image/png;base64,{aruco_2}" alt="ArUco 2"></div>

        <div class="omr-instructions">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ⬤ ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>

        {table_html_op1}

        <div class="scan-qr-box">
            <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
        </div>
    </div>
</div>
</body>
</html>
"""

# =========================================================================
# OPÇÃO 2: RIO ONDULADO SUAVE & CANOA VERDE PETRÓLEO
# =========================================================================
table_html_op2 = build_table_omr_image2(header_bg="#0b5d5c")

html_op2 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.m2 .topo-art {{ position: absolute; top: 0; left: 0; width: 100%; height: 75mm; z-index: 1; }}
.m2 .ano-pill {{ background: #0b5d5c; color: #ffffff; border: 1.5px solid rgba(255,255,255,0.4); }}
.m2 .titulo-prova {{ color: #ffffff; font-family: 'Poppins', sans-serif; text-shadow: 0 2px 5px rgba(11,93,92,0.5); }}

.m2 .bc-top {{ background: #0b5d5c; color: #a7f3d0; }}
.m2 .bc-mid {{ background: #267c6e; color: #ffffff; }}
.m2 .bc-bot {{ color: #0b5d5c; }}

.m2 .student-card {{ border-left: 3.5mm solid #0e7c7b; }}
.m2 .omr-instructions {{ background: #e6f7f6; color: #0e7c7b; border-color: #b2e6e3; }}
.m2 .bubble {{ border-color: #0e7c7b; color: #0e7c7b; }}
</style>
</head>
<body>
<div class="capa m2">
    <svg class="topo-art" viewBox="0 0 800 290" preserveAspectRatio="none">
        <rect width="800" height="290" fill="#cbf1e7"/>
        <path d="M0 140 Q200 95 400 135 T800 115 V290 H0 Z" fill="#7ed4c1"/>
        <path d="M0 185 Q180 145 380 180 T800 160 V290 H0 Z" fill="#38a390"/>
        <path d="M0 225 Q220 190 440 225 T800 215 V290 H0 Z" fill="#0e7c7b"/>
        <path d="M0 258 Q 220 230 400 258 T 800 258 V 290 H 0 Z" fill="#e8fbf6"/>
        <path d="M330 244 Q400 266 470 244 Q400 255 330 244Z" fill="#f4a261"/>
        <line x1="400" y1="242" x2="400" y2="208" stroke="#78350f" stroke-width="2.5"/>
        <path d="M400 208 Q428 218 400 234Z" fill="#ffffff"/>
    </svg>

    <div class="top-brand">
        <div class="ano-pill">2026</div>
        <div class="titulo-prova">PROVA CANOA</div>
    </div>

    <div class="badge-caderno-3tier">
        <div class="bc-top">CADERNO</div>
        <div class="bc-mid">MATEMÁTICA</div>
        <div class="bc-bot">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="student-card-header">DADOS DO(A) ESTUDANTE &bull; CADERNO M0802</div>
        <div class="student-card-fields">
            <div class="field-block">
                <span class="field-lbl">Unidade Escolar:</span>
                <span class="field-txt">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
            </div>
            <div class="field-block highlight">
                <span class="field-lbl">Nome Completo do(a) Estudante:</span>
                <span class="field-txt name">LUCAS GABRIEL DOS SANTOS SILVA</span>
            </div>
            <div class="field-row-dual">
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turma:</span>
                    <span class="field-txt">8º ANO A</span>
                </div>
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turno:</span>
                    <span class="field-txt">MATUTINO</span>
                </div>
            </div>
        </div>
    </div>

    <div class="reading-area">
        <div class="aruco-mark tl"><img src="data:image/png;base64,{aruco_0}" alt="ArUco 0"></div>
        <div class="aruco-mark tr"><img src="data:image/png;base64,{aruco_1}" alt="ArUco 1"></div>
        <div class="aruco-mark bl"><img src="data:image/png;base64,{aruco_3}" alt="ArUco 3"></div>
        <div class="aruco-mark br"><img src="data:image/png;base64,{aruco_2}" alt="ArUco 2"></div>

        <div class="omr-instructions">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ⬤ ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>

        {table_html_op2}

        <div class="scan-qr-box">
            <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
        </div>
    </div>
</div>
</body>
</html>
"""

# =========================================================================
# OPÇÃO 3: PÔR DO SOL SOLAR & DUNA DO SERTÃO
# =========================================================================
table_html_op3 = build_table_omr_image2(header_bg="#c2410c")

html_op3 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.m3 .topo-art {{ position: absolute; top: 0; left: 0; width: 100%; height: 75mm; z-index: 1; }}
.m3 .ano-pill {{ background: #c2410c; color: #ffffff; border: 1.5px solid rgba(255,255,255,0.4); }}
.m3 .titulo-prova {{ color: #ffffff; font-family: 'Poppins', sans-serif; text-shadow: 0 2px 5px rgba(194,65,12,0.5); }}

.m3 .bc-top {{ background: #c2410c; color: #fed7aa; }}
.m3 .bc-mid {{ background: #ea580c; color: #ffffff; }}
.m3 .bc-bot {{ color: #c2410c; }}

.m3 .student-card {{ border-left: 3.5mm solid #ea580c; }}
.m3 .omr-instructions {{ background: #fff7ed; color: #c2410c; border-color: #fed7aa; }}
.m3 .bubble {{ border-color: #ea580c; color: #ea580c; }}
</style>
</head>
<body>
<div class="capa m3">
    <svg class="topo-art" viewBox="0 0 800 290" preserveAspectRatio="none">
        <rect width="800" height="290" fill="#fde68a"/>
        <circle cx="560" cy="75" r="60" fill="#f59e0b" opacity="0.85"/>
        <circle cx="560" cy="75" r="90" fill="#fbbf24" opacity="0.35"/>
        <path d="M0 150 Q220 105 450 145 T800 125 V290 H0 Z" fill="#fdba74"/>
        <path d="M0 195 Q200 150 420 185 T800 165 V290 H0 Z" fill="#f97316"/>
        <path d="M0 230 Q240 195 460 228 T800 218 V290 H0 Z" fill="#c2410c"/>
        <path d="M0 260 Q 220 232 400 260 T 800 260 V 290 H 0 Z" fill="#fff7ed"/>
        <path d="M330 244 Q400 266 470 244 Q400 255 330 244Z" fill="#fef08a"/>
        <line x1="400" y1="242" x2="400" y2="208" stroke="#451a03" stroke-width="2.5"/>
        <path d="M400 208 Q428 218 400 234Z" fill="#ffffff"/>
    </svg>

    <div class="top-brand">
        <div class="ano-pill">2026</div>
        <div class="titulo-prova">PROVA CANOA</div>
    </div>

    <div class="badge-caderno-3tier">
        <div class="bc-top">CADERNO</div>
        <div class="bc-mid">MATEMÁTICA</div>
        <div class="bc-bot">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="student-card-header">DADOS DO(A) ESTUDANTE &bull; CADERNO M0802</div>
        <div class="student-card-fields">
            <div class="field-block">
                <span class="field-lbl">Unidade Escolar:</span>
                <span class="field-txt">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
            </div>
            <div class="field-block highlight">
                <span class="field-lbl">Nome Completo do(a) Estudante:</span>
                <span class="field-txt name">LUCAS GABRIEL DOS SANTOS SILVA</span>
            </div>
            <div class="field-row-dual">
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turma:</span>
                    <span class="field-txt">8º ANO A</span>
                </div>
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turno:</span>
                    <span class="field-txt">MATUTINO</span>
                </div>
            </div>
        </div>
    </div>

    <div class="reading-area">
        <div class="aruco-mark tl"><img src="data:image/png;base64,{aruco_0}" alt="ArUco 0"></div>
        <div class="aruco-mark tr"><img src="data:image/png;base64,{aruco_1}" alt="ArUco 1"></div>
        <div class="aruco-mark bl"><img src="data:image/png;base64,{aruco_3}" alt="ArUco 3"></div>
        <div class="aruco-mark br"><img src="data:image/png;base64,{aruco_2}" alt="ArUco 2"></div>

        <div class="omr-instructions">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ⬤ ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>

        {table_html_op3}

        <div class="scan-qr-box">
            <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
        </div>
    </div>
</div>
</body>
</html>
"""

# =========================================================================
# OPÇÃO 4: LAGOA SERENA & NÁUTICO REAL (AZUL MARINHO REAL & DOURADO)
# =========================================================================
table_html_op4 = build_table_omr_image2(header_bg="#1e3a8a")

html_op4 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.m4 .topo-art {{ position: absolute; top: 0; left: 0; width: 100%; height: 75mm; z-index: 1; }}
.m4 .ano-pill {{ background: #1e3a8a; color: #ffffff; border: 1.5px solid rgba(255,255,255,0.4); }}
.m4 .titulo-prova {{ color: #ffffff; font-family: 'Montserrat', sans-serif; letter-spacing: 1px; text-shadow: 0 2px 5px rgba(30,58,138,0.5); }}

.m4 .bc-top {{ background: #1e3a8a; color: #93c5fd; }}
.m4 .bc-mid {{ background: #2563eb; color: #ffffff; }}
.m4 .bc-bot {{ color: #1e3a8a; }}

.m4 .student-card {{ border-left: 3.5mm solid #2563eb; }}
.m4 .omr-instructions {{ background: #eff6ff; color: #1e40af; border-color: #bfdbfe; }}
.m4 .bubble {{ border-color: #2563eb; color: #2563eb; }}
</style>
</head>
<body>
<div class="capa m4">
    <svg class="topo-art" viewBox="0 0 800 290" preserveAspectRatio="none">
        <rect width="800" height="290" fill="#93c5fd"/>
        <path d="M0 140 C 220 100, 420 180, 620 120 C 720 95, 770 115, 800 105 V290 H0 Z" fill="#3b82f6"/>
        <path d="M0 185 C 200 150, 440 215, 640 170 C 720 150, 770 170, 800 160 V290 H0 Z" fill="#1d4ed8"/>
        <path d="M0 225 C 240 190, 460 245, 660 210 C 730 200, 780 210, 800 200 V290 H0 Z" fill="#1e3a8a"/>
        <path d="M0 260 Q 220 232 400 260 T 800 260 V 290 H 0 Z" fill="#eff6ff"/>
        <path d="M330 245 Q 400 268 470 245 Q 400 256 330 245 Z" fill="#facc15"/>
        <line x1="400" y1="243" x2="400" y2="208" stroke="#ffffff" stroke-width="2.5"/>
        <path d="M400 208 Q 425 218 400 236 Z" fill="#fef08a"/>
    </svg>

    <div class="top-brand">
        <div class="ano-pill">2026</div>
        <div class="titulo-prova">PROVA CANOA</div>
    </div>

    <div class="badge-caderno-3tier">
        <div class="bc-top">CADERNO</div>
        <div class="bc-mid">MATEMÁTICA</div>
        <div class="bc-bot">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="student-card-header">DADOS DO(A) ESTUDANTE &bull; CADERNO M0802</div>
        <div class="student-card-fields">
            <div class="field-block">
                <span class="field-lbl">Unidade Escolar:</span>
                <span class="field-txt">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
            </div>
            <div class="field-block highlight">
                <span class="field-lbl">Nome Completo do(a) Estudante:</span>
                <span class="field-txt name">LUCAS GABRIEL DOS SANTOS SILVA</span>
            </div>
            <div class="field-row-dual">
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turma:</span>
                    <span class="field-txt">8º ANO A</span>
                </div>
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turno:</span>
                    <span class="field-txt">MATUTINO</span>
                </div>
            </div>
        </div>
    </div>

    <div class="reading-area">
        <div class="aruco-mark tl"><img src="data:image/png;base64,{aruco_0}" alt="ArUco 0"></div>
        <div class="aruco-mark tr"><img src="data:image/png;base64,{aruco_1}" alt="ArUco 1"></div>
        <div class="aruco-mark bl"><img src="data:image/png;base64,{aruco_3}" alt="ArUco 3"></div>
        <div class="aruco-mark br"><img src="data:image/png;base64,{aruco_2}" alt="ArUco 2"></div>

        <div class="omr-instructions">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ⬤ ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>

        {table_html_op4}

        <div class="scan-qr-box">
            <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
        </div>
    </div>
</div>
</body>
</html>
"""

proposals = [
    ("opcao_1_montanhas_canoa.html", "opcao_1_montanhas_canoa", "Opção 1: Montanhas em Ziguezague & Canoa Dourada", html_op1),
    ("opcao_2_rio_verde_petroleo.html", "opcao_2_rio_verde_petroleo", "Opção 2: Rio Ondulado Suave & Canoa Verde Petróleo", html_op2),
    ("opcao_3_por_do_sol_solar.html", "opcao_3_por_do_sol_solar", "Opção 3: Pôr do Sol Solar & Dunas", html_op3),
    ("opcao_4_azul_nautico_lagoa.html", "opcao_4_azul_nautico_lagoa", "Opção 4: Lagoa Serena & Náutico Real", html_op4),
]

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

generated_pdfs = []

for filename, base_id, label, content in proposals:
    html_p = os.path.join(workspace_sheets, filename)
    with open(html_p, "w", encoding="utf-8") as f:
        f.write(content)
        
    pdf_ws = os.path.join(workspace_sheets, f"{base_id}.pdf")
    pdf_art = os.path.join(artifact_dir, f"{base_id}.pdf")
    
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_ws}",
        html_p
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(pdf_ws):
        try:
            shutil.copy2(pdf_ws, pdf_art)
        except Exception:
            pass
        generated_pdfs.append(pdf_ws)
        
        doc = fitz.open(pdf_ws)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(180/72.0, 180/72.0), alpha=False)
        png_ws = os.path.join(workspace_sheets, f"{base_id}.png")
        png_art = os.path.join(artifact_dir, f"{base_id}.png")
        pix.save(png_ws)
        pix.save(png_art)
        doc.close()
        print(f"Rendered: {base_id} -> {png_ws}")

# 4. Create Merged Multi-page PDF
merged_pdf_ws = os.path.join(workspace_sheets, "propostas_4_capas_prova_canoa.pdf")
merged_pdf_art = os.path.join(artifact_dir, "propostas_4_capas_prova_canoa.pdf")

merged_doc = fitz.open()
for pdf_file in generated_pdfs:
    src_doc = fitz.open(pdf_file)
    merged_doc.insert_pdf(src_doc)
    src_doc.close()

try:
    merged_doc.save(merged_pdf_ws)
    shutil.copy2(merged_pdf_ws, merged_pdf_art)
    print(f"Merged PDF created with {len(generated_pdfs)} pages -> {merged_pdf_ws}")
except Exception as e:
    print(f"Notice: Could not save merged pdf to {merged_pdf_ws}: {e}")

merged_doc.close()

# 5. Master Visualizer HTML in project root
catalog_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>4 Opções Oficiais com Área de Leitura na Metade Inferior - Prova Canoa 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #0b0f19;
        --surface: #151d2c;
        --border: #233044;
        --text: #f8fafc;
        --text-muted: #94a3b8;
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
    .spec-box {{
        margin-top: 18px;
        display: inline-block;
        background: rgba(14, 165, 233, 0.1);
        border: 1px solid rgba(14, 165, 233, 0.35);
        border-radius: 10px;
        padding: 12px 24px;
        color: #e0f2fe;
        font-size: 0.92rem;
        line-height: 1.6;
        text-align: left;
    }}
    .spec-box ul {{
        margin-left: 20px;
        margin-top: 6px;
    }}
    .merged-cta {{
        margin-top: 20px;
        display: flex;
        justify-content: center;
        gap: 15px;
    }}
    .btn-main {{
        background: linear-gradient(135deg, #0284c7, #0369a1);
        color: #fff;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 700;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 4px 15px rgba(2,132,199,0.4);
        transition: transform 0.2s;
    }}
    .btn-main:hover {{
        transform: translateY(-2px);
    }}
    .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
        gap: 30px;
        max-width: 1500px;
        margin: 35px auto 0 auto;
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
        background: #192233;
    }}
    .badge {{
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 12px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .b-blue {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }}
    .b-green {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }}
    .b-orange {{ background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.4); }}
    .b-navy {{ background: rgba(147, 197, 253, 0.2); color: #93c5fd; border: 1px solid rgba(147, 197, 253, 0.4); }}
    .p-header h2 {{
        font-size: 1.25rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 6px;
    }}
    .p-header p {{
        font-size: 0.88rem;
        color: var(--text-muted);
        margin-bottom: 16px;
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
        <h1>4 Modelos Oficiais — Prova Canoa 2026</h1>
        <p>Área de Leitura delimitada exclusivamente na metade inferior &bull; QR Code ao lado do marcador inferior direito</p>
        <div class="spec-box">
            <strong>Especificações Fielmente Aplicadas:</strong>
            <ul>
                <li><strong>Área de Leitura:</strong> Apenas a metade inferior da página, com os 4 marcadores ArUco delimitando exclusivamente essa zona escaneável.</li>
                <li><strong>QR Code:</strong> Posicionado na parte inferior da área escaneável, imediatamente à esquerda do marcador ArUco inferior direito (conforme Imagem 2).</li>
                <li><strong>Tabela de Respostas:</strong> 2 colunas de questões (Itens 01 a 12 e 13 a 22) com bolhas circulares identificadas e barra superior de orientações.</li>
                <li><strong>Identificação do Aluno:</strong> Ocupando toda a largura na metade superior com <code>Unidade Escolar</code>, <code>Nome Completo do(a) Estudante</code>, <code>Turma</code> e <code>Turno</code> (sem QR Code ao lado).</li>
                <li><strong>Topo:</strong> Ano <code>2026</code> e exclusivamente o nome <code>PROVA CANOA</code> abaixo, com Badge de 3 níveis do Caderno à direita.</li>
            </ul>
        </div>
        <div class="merged-cta">
            <a href="backend/storage/sheets/propostas_4_capas_prova_canoa.pdf" target="_blank" class="btn-main">📑 Abrir PDF com os 4 Modelos (4 Páginas)</a>
        </div>
    </header>

    <main class="grid">
        <!-- Opção 1 -->
        <div class="proposal-card">
            <div class="p-header">
                <span class="badge b-blue">Opção 1 &bull; Montanhas & Canoa Dourada</span>
                <h2>Opção 1: Montanhas em Ziguezague & Canoa Dourada</h2>
                <p>Silhueta em ziguezague idêntica à referência original em azul marinho e ciano com a canoa dourada. Cartão-resposta em tabela com ArUco e QR Code inferior.</p>
                <div class="btn-group">
                    <a href="backend/storage/sheets/opcao_1_montanhas_canoa.pdf" target="_blank" class="btn btn-p">📄 Abrir PDF</a>
                    <a href="backend/storage/sheets/opcao_1_montanhas_canoa.html" target="_blank" class="btn btn-s">🌐 Abrir HTML</a>
                </div>
            </div>
            <div class="p-body">
                <img src="backend/storage/sheets/opcao_1_montanhas_canoa.png" class="preview-img" alt="Opção 1">
            </div>
        </div>

        <!-- Opção 2 -->
        <div class="proposal-card">
            <div class="p-header">
                <span class="badge b-green">Opção 2 &bull; Verde Petróleo</span>
                <h2>Opção 2: Rio Ondulado Suave & Canoa Verde Petróleo</h2>
                <p>Estética fluvial limpa em verde petróleo e verde esmeralda com ondas suaves e canoa com vela âmbar.</p>
                <div class="btn-group">
                    <a href="backend/storage/sheets/opcao_2_rio_verde_petroleo.pdf" target="_blank" class="btn btn-p">📄 Abrir PDF</a>
                    <a href="backend/storage/sheets/opcao_2_rio_verde_petroleo.html" target="_blank" class="btn btn-s">🌐 Abrir HTML</a>
                </div>
            </div>
            <div class="p-body">
                <img src="backend/storage/sheets/opcao_2_rio_verde_petroleo.png" class="preview-img" alt="Opção 2">
            </div>
        </div>

        <!-- Opção 3 -->
        <div class="proposal-card">
            <div class="p-header">
                <span class="badge b-orange">Opção 3 &bull; Pôr do Sol Solar</span>
                <h2>Opção 3: Pôr do Sol Solar & Dunas</h2>
                <p>Visual solar vibrante em âmbar, laranja e terracota com sol poente e relevo ondulado do sertão.</p>
                <div class="btn-group">
                    <a href="backend/storage/sheets/opcao_3_por_do_sol_solar.pdf" target="_blank" class="btn btn-p">📄 Abrir PDF</a>
                    <a href="backend/storage/sheets/opcao_3_por_do_sol_solar.html" target="_blank" class="btn btn-s">🌐 Abrir HTML</a>
                </div>
            </div>
            <div class="p-body">
                <img src="backend/storage/sheets/opcao_3_por_do_sol_solar.png" class="preview-img" alt="Opção 3">
            </div>
        </div>

        <!-- Opção 4 -->
        <div class="proposal-card">
            <div class="p-header">
                <span class="badge b-navy">Opção 4 &bull; Náutico Real</span>
                <h2>Opção 4: Lagoa Serena & Náutico Real</h2>
                <p>Linhas náuticas elegantes com ondas em azul marinho real, azul cobalto e a canoa estilizada em amarelo ouro.</p>
                <div class="btn-group">
                    <a href="backend/storage/sheets/opcao_4_azul_nautico_lagoa.pdf" target="_blank" class="btn btn-p">📄 Abrir PDF</a>
                    <a href="backend/storage/sheets/opcao_4_azul_nautico_lagoa.html" target="_blank" class="btn btn-s">🌐 Abrir HTML</a>
                </div>
            </div>
            <div class="p-body">
                <img src="backend/storage/sheets/opcao_4_azul_nautico_lagoa.png" class="preview-img" alt="Opção 4">
            </div>
        </div>
    </main>
</body>
</html>
"""

master_html_p = os.path.join(project_root, "propostas_capas_canoa.html")
with open(master_html_p, "w", encoding="utf-8") as f:
    f.write(catalog_html)

print("Novos 4 modelos gerados e renderizados com total fidelidade às instruções!")
