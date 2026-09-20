import os
import sys
import base64
import io
import subprocess
import qrcode
import fitz  # PyMuPDF
import shutil

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
workspace_sheets = os.path.join(backend_dir, "storage", "sheets")
project_root = os.path.dirname(backend_dir)
artifact_dir = r"C:\Users\Lagoa da Canoa\.gemini\antigravity-ide\brain\d41159d4-3d40-4e8f-874a-737221f95ae0"

os.makedirs(workspace_sheets, exist_ok=True)
os.makedirs(artifact_dir, exist_ok=True)

# 1. Base64 QR Code
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

qr_b64 = make_qr_base64("E:M0402|S:2026040921")

# 2. OMR Grid Builder (22 questions, 4 alternatives A-D)
def build_omr_columns():
    cols = 4
    num_questions = 22
    rows_per_col = 6
    options = ["A", "B", "C", "D"]
    
    html = '<div class="omr">'
    for c_idx in range(cols):
        start_q = c_idx * rows_per_col + 1
        end_q = min((c_idx + 1) * rows_per_col, num_questions)
        q_count = max(0, end_q - start_q + 1)
        if q_count == 0:
            continue
            
        html += '<div class="omr-col">'
        html += '<div class="lets">'
        html += '<span class="let-spacer"></span>'
        html += ''.join([f'<span class="let-char">{opt}</span>' for opt in options])
        html += '</div>'
        for r in range(q_count):
            q_num = start_q + r
            html += f'<div class="q"><span class="n">{q_num:02d}</span>'
            html += ''.join(['<span class="b"></span>' for _ in options])
            html += '</div>'
        html += '</div>'
    html += '</div>'
    return html

omr_grid_html = build_omr_columns()

COMMON_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Poppins:wght@600;700;800;900&family=Nunito:wght@700;800;900&family=Space+Mono:wght@700&display=swap');

@page {
    size: 210mm 297mm;
    margin: 0;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #fff;
    font-family: 'Montserrat', Arial, sans-serif;
    color: #1e293b;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
}
.capa {
    width: 210mm;
    height: 297mm;
    position: relative;
    overflow: hidden;
    margin: 0 auto;
    background: #fff;
}

/* Marcadores de Registro OMR 7mm x 7mm */
.mark {
    position: absolute;
    width: 7mm;
    height: 7mm;
    background: #000;
    z-index: 50;
}
.mark.tl { top: 8mm; left: 8mm; }
.mark.tr { top: 8mm; right: 8mm; }
.mark.bl { bottom: 8mm; left: 8mm; }
.mark.br { bottom: 8mm; right: 8mm; }

/* Bloco do Topo Esquerdo: 2026 e logo abaixo PROVA CANOA */
.top-brand {
    position: absolute;
    top: 14mm;
    left: 17mm;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2mm;
}
.ano-pill {
    display: inline-block;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2.5px;
    padding: 1.5mm 5mm;
    border-radius: 20px;
    line-height: 1;
}
.titulo-prova {
    font-size: 24px;
    font-weight: 900;
    letter-spacing: 0.5px;
    line-height: 1;
    text-transform: uppercase;
}

/* Card com Dados do Aluno Preenchidos & QR Code */
.student-card {
    position: absolute;
    left: 14mm;
    right: 14mm;
    background: #fff;
    border-radius: 4.5mm;
    padding: 4.5mm 5.5mm;
    box-shadow: 0 2.5mm 7mm rgba(0,0,0,0.07);
    z-index: 15;
}
.card-subj {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 3.5mm;
    padding-bottom: 2mm;
}
.student-grid {
    display: grid;
    grid-template-columns: 1fr 27mm;
    gap: 4mm;
    align-items: center;
}
.data-fields {
    display: flex;
    flex-direction: column;
    gap: 2.2mm;
}
.row-dual {
    display: flex;
    gap: 3.5mm;
}
.field-block {
    background: #f8fafc;
    border: 1.2px solid #cbd5e1;
    border-radius: 2.2mm;
    padding: 1.8mm 2.8mm;
}
.field-block.highlight {
    background: #f1f5f9;
    border-color: #94a3b8;
}
.field-label {
    font-size: 7.2px;
    font-weight: 800;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    display: block;
    margin-bottom: 1.5px;
}
.field-val {
    font-size: 10px;
    font-weight: 700;
    color: #0f172a;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.field-val.name {
    font-size: 11.5px;
    font-weight: 900;
    color: #0b192c;
    letter-spacing: 0.3px;
}
.field-val.highlight-badge {
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

/* QR Code */
.qr-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #fff;
    border: 1.2px solid #cbd5e1;
    border-radius: 2.5mm;
    padding: 2mm;
}
.qr-container img {
    width: 21mm;
    height: 21mm;
    display: block;
}
.qr-label {
    font-family: 'Space Mono', monospace;
    font-size: 6.8px;
    font-weight: 700;
    color: #334155;
    margin-top: 1.2mm;
    letter-spacing: 0.3px;
}

/* OMR Section */
.omr-wrap {
    position: absolute;
    left: 14mm;
    right: 14mm;
    z-index: 10;
}
.omr-instructions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 7.2px;
    font-weight: 700;
    padding: 2mm 3.5mm;
    border-radius: 1.5mm;
    margin-bottom: 3.5mm;
}
.omr {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 3.5mm;
    width: 100%;
}
.omr-col {
    background: #fff;
    border: 1px dashed #cbd5e1;
    border-radius: 2mm;
    padding: 2mm 2.5mm;
    width: 100%;
}
.lets {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2mm;
    padding: 0 1mm;
}
.let-spacer {
    width: 6.5mm;
}
.let-char {
    width: 4.8mm;
    font-size: 8px;
    font-weight: 800;
    text-align: center;
    color: #475569;
}
.q {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.8mm;
    padding: 0 1mm;
}
.q .n {
    width: 6.5mm;
    font-size: 7.5px;
    font-weight: 800;
    text-align: center;
    padding: 1.2mm 0;
    border-radius: 0.8mm;
}
.q .b {
    width: 4.8mm;
    height: 4.8mm;
    border: 1.3px solid #333;
    border-radius: 50%;
    background: #fff;
}
.footer-code {
    position: absolute;
    bottom: 9.5mm;
    right: 22mm;
    font-family: 'Space Mono', monospace;
    font-size: 8.5px;
    font-weight: 700;
    letter-spacing: 0.5px;
    z-index: 10;
}
"""

# =========================================================================
# MODELO 1: MONTANHAS EM ZIGUEZAGUE & CANOA DOURADA (INSPIRADO NA REFERÊNCIA)
# =========================================================================
html_op1 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.m1 {{ background: #f4f9fc; }}
.m1 .topo-art {{ position: absolute; top: 0; left: 0; width: 100%; height: 86mm; z-index: 1; }}
.m1 .ano-pill {{ background: #0e2a47; color: #ffffff; border: 1.5px solid rgba(255,255,255,0.4); }}
.m1 .titulo-prova {{ color: #ffffff; font-family: 'Montserrat', sans-serif; text-shadow: 0 2px 5px rgba(10,25,45,0.5); }}

.m1 .badge-caderno {{
    position: absolute;
    top: 12mm;
    right: 15mm;
    width: 45mm;
    background: #0e2a47;
    border-radius: 3.5mm;
    overflow: hidden;
    z-index: 10;
    box-shadow: 0 3mm 8mm rgba(14,42,71,0.35);
    text-align: center;
}}
.m1 .badge-caderno .bc-head {{
    font-size: 8.5px;
    font-weight: 800;
    color: #93c5fd;
    letter-spacing: 2px;
    padding: 2mm 0 1mm 0;
}}
.m1 .badge-caderno .bc-sub {{
    font-size: 11px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: 1px;
    padding-bottom: 2mm;
}}
.m1 .badge-caderno .bc-stage {{
    background: #ffffff;
    color: #0e2a47;
    font-size: 10px;
    font-weight: 800;
    padding: 1.5mm 0;
    letter-spacing: 1px;
    border-radius: 0 0 3.5mm 3.5mm;
}}

.m1 .student-card {{ top: 92mm; border-left: 3.5mm solid #1d4ed8; box-shadow: 0 3mm 8mm rgba(14,42,71,0.12); }}
.m1 .card-subj {{ border-bottom: 1px solid #e2e8f0; }}
.m1 .card-subj b {{ color: #0e2a47; font-size: 13.5px; font-weight: 900; }}
.m1 .card-subj span {{ font-size: 10px; color: #475569; font-weight: 700; }}
.m1 .omr-wrap {{ top: 164mm; }}
.m1 .omr-instructions {{ background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }}
.m1 .q .n {{ background: #e0f2fe; color: #0369a1; }}
.m1 .q .b {{ border-color: #1d4ed8; }}
.m1 .footer-code {{ color: #0e2a47; }}
</style>
</head>
<body>
<div class="capa m1">
    <div class="mark tl"></div><div class="mark tr"></div><div class="mark bl"></div><div class="mark br"></div>
    
    <!-- Arte Vetorial de Montanhas e Rio Canoa -->
    <svg class="topo-art" viewBox="0 0 800 320" preserveAspectRatio="none">
        <rect width="800" height="320" fill="#a5d8ea"/>
        <!-- Montanhas de fundo -->
        <polygon points="0,210 150,90 300,220 440,70 590,210 700,120 800,210 800,320 0,320" fill="#437b9b"/>
        <!-- Montanhas da frente -->
        <polygon points="0,250 120,150 260,255 420,135 560,250 680,170 800,255 800,320 0,320" fill="#0e2a47"/>
        <!-- Rio em curva inferior -->
        <path d="M0 285 Q 220 255 400 285 T 800 285 V 320 H 0 Z" fill="#e2f3f8"/>
        <!-- Canoa Dourada -->
        <path d="M330 274 Q 400 295 470 274 Q 400 286 330 274 Z" fill="#f59e0b"/>
    </svg>

    <div class="top-brand">
        <div class="ano-pill">2026</div>
        <div class="titulo-prova">PROVA CANOA</div>
    </div>

    <div class="badge-caderno">
        <div class="bc-head">CADERNO</div>
        <div class="bc-sub">MATEMÁTICA</div>
        <div class="bc-stage">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="card-subj">
            <b>IDENTIFICAÇÃO DO(A) ESTUDANTE</b>
            <span>CADERNO M0402 &bull; 8º ANO</span>
        </div>
        <div class="student-grid">
            <div class="data-fields">
                <div class="field-block">
                    <span class="field-label">Unidade Escolar:</span>
                    <span class="field-val">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
                </div>
                <div class="field-block highlight">
                    <span class="field-label">Nome Completo do(a) Estudante:</span>
                    <span class="field-val name">LUCAS GABRIEL DOS SANTOS SILVA</span>
                </div>
                <div class="row-dual">
                    <div class="field-block" style="flex: 1;">
                        <span class="field-label">Turma:</span>
                        <span class="field-val highlight-badge">8º ANO A</span>
                    </div>
                    <div class="field-block" style="flex: 1;">
                        <span class="field-label">Turno:</span>
                        <span class="field-val highlight-badge">MATUTINO</span>
                    </div>
                </div>
            </div>
            <div class="qr-container" style="border-color: #93c5fd;">
                <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
                <span class="qr-label">ID: 2026.04.0921</span>
            </div>
        </div>
    </div>

    <div class="omr-wrap">
        <div class="omr-instructions">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ⬤ ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>
        {omr_grid_html}
    </div>

    <div class="footer-code">4454197329</div>
</div>
</body>
</html>
"""

# =========================================================================
# MODELO 2: RIO ONDULADO SUAVE & CANOA VERDE PETRÓLEO (INSPIRADO EM PROVA-CANOA)
# =========================================================================
html_op2 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.m2 {{ background: #f2fbf9; }}
.m2 .topo-art {{ position: absolute; top: 0; left: 0; width: 100%; height: 86mm; z-index: 1; }}
.m2 .ano-pill {{ background: #0b5d5c; color: #ffffff; border: 1.5px solid rgba(255,255,255,0.4); }}
.m2 .titulo-prova {{ color: #ffffff; font-family: 'Poppins', sans-serif; text-shadow: 0 2px 5px rgba(11,93,92,0.5); }}

.m2 .badge-caderno {{
    position: absolute;
    top: 12mm;
    right: 15mm;
    width: 45mm;
    background: #0b5d5c;
    border-radius: 3.5mm;
    overflow: hidden;
    z-index: 10;
    box-shadow: 0 3mm 8mm rgba(11,93,92,0.35);
    text-align: center;
}}
.m2 .badge-caderno .bc-head {{
    font-size: 8.5px;
    font-weight: 800;
    color: #a7f3d0;
    letter-spacing: 2px;
    padding: 2mm 0 1mm 0;
}}
.m2 .badge-caderno .bc-sub {{
    font-size: 11px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: 1px;
    padding-bottom: 2mm;
}}
.m2 .badge-caderno .bc-stage {{
    background: #ffffff;
    color: #0b5d5c;
    font-size: 10px;
    font-weight: 800;
    padding: 1.5mm 0;
    letter-spacing: 1px;
    border-radius: 0 0 3.5mm 3.5mm;
}}

.m2 .student-card {{ top: 92mm; border-left: 3.5mm solid #0e7c7b; box-shadow: 0 3mm 8mm rgba(14,124,123,0.12); }}
.m2 .card-subj {{ border-bottom: 1px solid #e2e8f0; }}
.m2 .card-subj b {{ color: #0b5d5c; font-size: 13.5px; font-weight: 900; }}
.m2 .card-subj span {{ font-size: 10px; color: #475569; font-weight: 700; }}
.m2 .omr-wrap {{ top: 164mm; }}
.m2 .omr-instructions {{ background: #e6f7f6; color: #0e7c7b; border: 1px solid #b2e6e3; }}
.m2 .q .n {{ background: #e6f7f6; color: #0b5d5c; }}
.m2 .q .b {{ border-color: #0e7c7b; }}
.m2 .footer-code {{ color: #0e7c7b; }}
</style>
</head>
<body>
<div class="capa m2">
    <div class="mark tl"></div><div class="mark tr"></div><div class="mark bl"></div><div class="mark br"></div>

    <!-- Rio e Vegetação Fluvial Vetorial -->
    <svg class="topo-art" viewBox="0 0 800 320" preserveAspectRatio="none">
        <rect width="800" height="320" fill="#cbf1e7"/>
        <path d="M0 160 Q200 110 400 150 T800 130 V320 H0 Z" fill="#7ed4c1"/>
        <path d="M0 210 Q180 160 380 200 T800 180 V320 H0 Z" fill="#38a390"/>
        <path d="M0 250 Q220 215 440 250 T800 240 V320 H0 Z" fill="#0e7c7b"/>
        <path d="M0 285 Q 220 255 400 285 T 800 285 V 320 H 0 Z" fill="#e8fbf6"/>
        <!-- Canoa com vela -->
        <path d="M330 268 Q400 292 470 268 Q400 280 330 268Z" fill="#f4a261"/>
        <line x1="400" y1="266" x2="400" y2="228" stroke="#78350f" stroke-width="3"/>
        <path d="M400 228 Q430 238 400 258Z" fill="#ffffff"/>
    </svg>

    <div class="top-brand">
        <div class="ano-pill">2026</div>
        <div class="titulo-prova">PROVA CANOA</div>
    </div>

    <div class="badge-caderno">
        <div class="bc-head">CADERNO</div>
        <div class="bc-sub">MATEMÁTICA</div>
        <div class="bc-stage">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="card-subj">
            <b>IDENTIFICAÇÃO DO(A) ESTUDANTE</b>
            <span>CADERNO M0402 &bull; 8º ANO</span>
        </div>
        <div class="student-grid">
            <div class="data-fields">
                <div class="field-block">
                    <span class="field-label">Unidade Escolar:</span>
                    <span class="field-val">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
                </div>
                <div class="field-block highlight">
                    <span class="field-label">Nome Completo do(a) Estudante:</span>
                    <span class="field-val name">LUCAS GABRIEL DOS SANTOS SILVA</span>
                </div>
                <div class="row-dual">
                    <div class="field-block" style="flex: 1;">
                        <span class="field-label">Turma:</span>
                        <span class="field-val highlight-badge">8º ANO A</span>
                    </div>
                    <div class="field-block" style="flex: 1;">
                        <span class="field-label">Turno:</span>
                        <span class="field-val highlight-badge">MATUTINO</span>
                    </div>
                </div>
            </div>
            <div class="qr-container" style="border-color: #a7f3d0;">
                <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
                <span class="qr-label" style="color: #0b5d5c;">ID: 2026.04.0921</span>
            </div>
        </div>
    </div>

    <div class="omr-wrap">
        <div class="omr-instructions">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ⬤ ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>
        {omr_grid_html}
    </div>

    <div class="footer-code">4454197329</div>
</div>
</body>
</html>
"""

# =========================================================================
# MODELO 3: PÔR DO SOL SOLAR & ÂMBAR (INSPIRADO EM PROVA-CANOA2 MODELO 1)
# =========================================================================
html_op3 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.m3 {{ background: #fffcf8; }}
.m3 .topo-art {{ position: absolute; top: 0; left: 0; width: 100%; height: 86mm; z-index: 1; }}
.m3 .ano-pill {{ background: #c2410c; color: #ffffff; border: 1.5px solid rgba(255,255,255,0.4); }}
.m3 .titulo-prova {{ color: #ffffff; font-family: 'Poppins', sans-serif; text-shadow: 0 2px 5px rgba(194,65,12,0.5); }}

.m3 .badge-caderno {{
    position: absolute;
    top: 12mm;
    right: 15mm;
    width: 45mm;
    background: #c2410c;
    border-radius: 3.5mm;
    overflow: hidden;
    z-index: 10;
    box-shadow: 0 3mm 8mm rgba(194,65,12,0.35);
    text-align: center;
}}
.m3 .badge-caderno .bc-head {{
    font-size: 8.5px;
    font-weight: 800;
    color: #fed7aa;
    letter-spacing: 2px;
    padding: 2mm 0 1mm 0;
}}
.m3 .badge-caderno .bc-sub {{
    font-size: 11px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: 1px;
    padding-bottom: 2mm;
}}
.m3 .badge-caderno .bc-stage {{
    background: #ffffff;
    color: #c2410c;
    font-size: 10px;
    font-weight: 800;
    padding: 1.5mm 0;
    letter-spacing: 1px;
    border-radius: 0 0 3.5mm 3.5mm;
}}

.m3 .student-card {{ top: 92mm; border-left: 3.5mm solid #ea580c; box-shadow: 0 3mm 8mm rgba(194,65,12,0.12); }}
.m3 .card-subj {{ border-bottom: 1px solid #fed7aa; }}
.m3 .card-subj b {{ color: #c2410c; font-size: 13.5px; font-weight: 900; }}
.m3 .card-subj span {{ font-size: 10px; color: #475569; font-weight: 700; }}
.m3 .omr-wrap {{ top: 164mm; }}
.m3 .omr-instructions {{ background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }}
.m3 .q .n {{ background: #ffedd5; color: #9a3412; }}
.m3 .q .b {{ border-color: #ea580c; }}
.m3 .footer-code {{ color: #c2410c; }}
</style>
</head>
<body>
<div class="capa m3">
    <div class="mark tl"></div><div class="mark tr"></div><div class="mark bl"></div><div class="mark br"></div>

    <svg class="topo-art" viewBox="0 0 800 320" preserveAspectRatio="none">
        <rect width="800" height="320" fill="#fde68a"/>
        <!-- Sol radiante suave -->
        <circle cx="560" cy="85" r="70" fill="#f59e0b" opacity="0.85"/>
        <circle cx="560" cy="85" r="100" fill="#fbbf24" opacity="0.35"/>
        <!-- Ondulações quentes de relevo -->
        <path d="M0 170 Q220 120 450 160 T800 140 V320 H0 Z" fill="#fdba74"/>
        <path d="M0 215 Q200 165 420 205 T800 185 V320 H0 Z" fill="#f97316"/>
        <path d="M0 252 Q240 215 460 250 T800 240 V320 H0 Z" fill="#c2410c"/>
        <path d="M0 285 Q 220 255 400 285 T 800 285 V 320 H 0 Z" fill="#fff7ed"/>
        <!-- Canoa iluminada -->
        <path d="M330 268 Q400 292 470 268 Q400 280 330 268Z" fill="#fef08a"/>
        <line x1="400" y1="266" x2="400" y2="228" stroke="#451a03" stroke-width="3"/>
        <path d="M400 228 Q430 238 400 258Z" fill="#ffffff"/>
    </svg>

    <div class="top-brand">
        <div class="ano-pill">2026</div>
        <div class="titulo-prova">PROVA CANOA</div>
    </div>

    <div class="badge-caderno">
        <div class="bc-head">CADERNO</div>
        <div class="bc-sub">MATEMÁTICA</div>
        <div class="bc-stage">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="card-subj">
            <b>IDENTIFICAÇÃO DO(A) ESTUDANTE</b>
            <span>CADERNO M0402 &bull; 8º ANO</span>
        </div>
        <div class="student-grid">
            <div class="data-fields">
                <div class="field-block">
                    <span class="field-label">Unidade Escolar:</span>
                    <span class="field-val">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
                </div>
                <div class="field-block highlight">
                    <span class="field-label">Nome Completo do(a) Estudante:</span>
                    <span class="field-val name">LUCAS GABRIEL DOS SANTOS SILVA</span>
                </div>
                <div class="row-dual">
                    <div class="field-block" style="flex: 1;">
                        <span class="field-label">Turma:</span>
                        <span class="field-val highlight-badge">8º ANO A</span>
                    </div>
                    <div class="field-block" style="flex: 1;">
                        <span class="field-label">Turno:</span>
                        <span class="field-val highlight-badge">MATUTINO</span>
                    </div>
                </div>
            </div>
            <div class="qr-container" style="border-color: #fed7aa;">
                <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
                <span class="qr-label" style="color: #c2410c;">ID: 2026.04.0921</span>
            </div>
        </div>
    </div>

    <div class="omr-wrap">
        <div class="omr-instructions">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ⬤ ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>
        {omr_grid_html}
    </div>

    <div class="footer-code">4454197329</div>
</div>
</body>
</html>
"""

# =========================================================================
# MODELO 4: LAGOA SERENA & NÁUTICO REAL (AZUL MARINHO REAL & DOURADO)
# =========================================================================
html_op4 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.m4 {{ background: #f8fafc; }}
.m4 .topo-art {{ position: absolute; top: 0; left: 0; width: 100%; height: 86mm; z-index: 1; }}
.m4 .ano-pill {{ background: #1e3a8a; color: #ffffff; border: 1.5px solid rgba(255,255,255,0.4); }}
.m4 .titulo-prova {{ color: #ffffff; font-family: 'Montserrat', sans-serif; letter-spacing: 1px; text-shadow: 0 2px 5px rgba(30,58,138,0.5); }}

.m4 .badge-caderno {{
    position: absolute;
    top: 12mm;
    right: 15mm;
    width: 45mm;
    background: #1e3a8a;
    border-radius: 3.5mm;
    overflow: hidden;
    z-index: 10;
    box-shadow: 0 3mm 8mm rgba(30,58,138,0.35);
    text-align: center;
}}
.m4 .badge-caderno .bc-head {{
    font-size: 8.5px;
    font-weight: 800;
    color: #93c5fd;
    letter-spacing: 2px;
    padding: 2mm 0 1mm 0;
}}
.m4 .badge-caderno .bc-sub {{
    font-size: 11px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: 1px;
    padding-bottom: 2mm;
}}
.m4 .badge-caderno .bc-stage {{
    background: #ffffff;
    color: #1e3a8a;
    font-size: 10px;
    font-weight: 800;
    padding: 1.5mm 0;
    letter-spacing: 1px;
    border-radius: 0 0 3.5mm 3.5mm;
}}

.m4 .student-card {{ top: 92mm; border-left: 3.5mm solid #2563eb; box-shadow: 0 3mm 8mm rgba(30,58,138,0.12); }}
.m4 .card-subj {{ border-bottom: 1px solid #e2e8f0; }}
.m4 .card-subj b {{ color: #1e3a8a; font-size: 13.5px; font-weight: 900; }}
.m4 .card-subj span {{ font-size: 10px; color: #475569; font-weight: 700; }}
.m4 .omr-wrap {{ top: 164mm; }}
.m4 .omr-instructions {{ background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }}
.m4 .q .n {{ background: #dbeafe; color: #1e40af; }}
.m4 .q .b {{ border-color: #2563eb; }}
.m4 .footer-code {{ color: #1e3a8a; }}
</style>
</head>
<body>
<div class="capa m4">
    <div class="mark tl"></div><div class="mark tr"></div><div class="mark bl"></div><div class="mark br"></div>

    <svg class="topo-art" viewBox="0 0 800 320" preserveAspectRatio="none">
        <rect width="800" height="320" fill="#93c5fd"/>
        <!-- Ondas estilizadas de lagoa -->
        <path d="M0 160 C 220 120, 420 200, 620 140 C 720 110, 770 130, 800 120 V320 H0 Z" fill="#3b82f6"/>
        <path d="M0 210 C 200 170, 440 240, 640 190 C 720 170, 770 190, 800 180 V320 H0 Z" fill="#1d4ed8"/>
        <path d="M0 250 C 240 215, 460 270, 660 235 C 730 225, 780 235, 800 225 V320 H0 Z" fill="#1e3a8a"/>
        <path d="M0 285 Q 220 255 400 285 T 800 285 V 320 H 0 Z" fill="#eff6ff"/>
        <!-- Canoa Minimalista Dourada -->
        <path d="M330 270 Q 400 293 470 270 Q 400 282 330 270 Z" fill="#facc15"/>
        <line x1="400" y1="268" x2="400" y2="230" stroke="#ffffff" stroke-width="2.5"/>
        <path d="M400 230 Q 425 240 400 260 Z" fill="#fef08a"/>
    </svg>

    <div class="top-brand">
        <div class="ano-pill">2026</div>
        <div class="titulo-prova">PROVA CANOA</div>
    </div>

    <div class="badge-caderno">
        <div class="bc-head">CADERNO</div>
        <div class="bc-sub">MATEMÁTICA</div>
        <div class="bc-stage">8º ANO</div>
    </div>

    <div class="student-card">
        <div class="card-subj">
            <b>IDENTIFICAÇÃO DO(A) ESTUDANTE</b>
            <span>CADERNO M0402 &bull; 8º ANO</span>
        </div>
        <div class="student-grid">
            <div class="data-fields">
                <div class="field-block">
                    <span class="field-label">Unidade Escolar:</span>
                    <span class="field-val">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
                </div>
                <div class="field-block highlight">
                    <span class="field-label">Nome Completo do(a) Estudante:</span>
                    <span class="field-val name">LUCAS GABRIEL DOS SANTOS SILVA</span>
                </div>
                <div class="row-dual">
                    <div class="field-block" style="flex: 1;">
                        <span class="field-label">Turma:</span>
                        <span class="field-val highlight-badge">8º ANO A</span>
                    </div>
                    <div class="field-block" style="flex: 1;">
                        <span class="field-label">Turno:</span>
                        <span class="field-val highlight-badge">MATUTINO</span>
                    </div>
                </div>
            </div>
            <div class="qr-container" style="border-color: #bfdbfe;">
                <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
                <span class="qr-label" style="color: #1e3a8a;">ID: 2026.04.0921</span>
            </div>
        </div>
    </div>

    <div class="omr-wrap">
        <div class="omr-instructions">
            <span>ORIENTAÇÕES: Preencha totalmente a bolha com caneta azul ou preta.</span>
            <span>CORRETO: [ ⬤ ] &nbsp; ERRADO: [ ✕ ] [ ✓ ]</span>
        </div>
        {omr_grid_html}
    </div>

    <div class="footer-code">4454197329</div>
</div>
</body>
</html>
"""

proposals = [
    ("opcao_1_montanhas_canoa.html", "opcao_1_montanhas_canoa", "Opção 1: Montanhas em Ziguezague & Canoa Dourada", html_op1),
    ("opcao_2_rio_verde_petroleo.html", "opcao_2_rio_verde_petroleo", "Opção 2: Rio Ondulado Suave & Canoa Verde Petróleo", html_op2),
    ("opcao_3_por_do_sol_solar.html", "opcao_3_por_do_sol_solar", "Opção 3: Pôr do Sol Solar & Âmbar", html_op3),
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
        shutil.copy2(pdf_ws, pdf_art)
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

# 3. Create Merged Multi-page PDF
merged_pdf_ws = os.path.join(workspace_sheets, "propostas_4_capas_prova_canoa.pdf")
merged_pdf_art = os.path.join(artifact_dir, "propostas_4_capas_prova_canoa.pdf")
merged_legacy_ws = os.path.join(workspace_sheets, "propostas_capas_canoa.pdf")
merged_legacy_art = os.path.join(artifact_dir, "propostas_capas_canoa.pdf")

merged_doc = fitz.open()
for pdf_file in generated_pdfs:
    src_doc = fitz.open(pdf_file)
    merged_doc.insert_pdf(src_doc)
    src_doc.close()

merged_doc.save(merged_pdf_ws)
shutil.copy2(merged_pdf_ws, merged_pdf_art)
print(f"Merged PDF created with {len(generated_pdfs)} pages -> {merged_pdf_ws}")

try:
    merged_doc.save(merged_legacy_ws)
    shutil.copy2(merged_legacy_ws, merged_legacy_art)
except Exception as e:
    print(f"Notice: Could not overwrite legacy file {merged_legacy_ws} (likely open in PDF viewer): {e}")

merged_doc.close()

# 4. Master Visualizer HTML in project root
catalog_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>4 Novas Opções de Capa Oficial - Prova Canoa 2026</title>
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
        <h1>4 Novas Opções de Capa Oficial Prova Canoa</h1>
        <p>Ajustadas rigorosamente às suas especificações</p>
        <div class="spec-box">
            <strong>Critérios Aplicados nas 4 Opções:</strong>
            <ul>
                <li><strong>Topo:</strong> Ano <code>2026</code> e diretamente abaixo apenas o nome <strong><code>PROVA CANOA</code></strong> (sem slogans).</li>
                <li><strong>Parte do Meio:</strong> Bloco de Identificação com <code>Unidade Escolar</code>, <code>Nome Completo do(a) Estudante</code>, <code>Turma</code> e <code>Turno</code> (substituindo data de nascimento).</li>
                <li><strong>Identificação Óptica:</strong> QR Code pré-alinhado com ID do estudante.</li>
                <li><strong>Base OMR:</strong> 4 Marcadores de canto de 7mm, gabarito de 22 questões com bolhas A-D e orientações de preenchimento.</li>
            </ul>
        </div>
        <div class="merged-cta">
            <a href="backend/storage/sheets/propostas_4_capas_prova_canoa.pdf" target="_blank" class="btn-main">📑 Abrir PDF com as 4 Opções Juntas (4 Páginas)</a>
        </div>
    </header>

    <main class="grid">
        <!-- Opção 1 -->
        <div class="proposal-card">
            <div class="p-header">
                <span class="badge b-blue">Opção 1 &bull; Fiel à Imagem de Referência</span>
                <h2>Opção 1: Montanhas em Ziguezague & Canoa Dourada</h2>
                <p>Silhueta pontiaguda em azul marinho e azul médio com a canoa dourada no rio curvo inferior. Badge lateral clássico com Caderno, Disciplina e Ano.</p>
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
                <p>Harmonia orgânica com ondas suaves de rio, canoa com vela âmbar e visual verde petróleo esmeralda límpido e institucional.</p>
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
                <h2>Opção 3: Pôr do Sol Solar & Âmbar</h2>
                <p>Atmosfera calorosa com sol radiante, tons solares quentes em âmbar/terracota e reflexo no rio com canoa navegando.</p>
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
                <p>Gradiente azul náutico real com ondas fluidas translúcidas, canoa geométrica em amarelo ouro e alto contraste corporativo.</p>
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

print("Todas as 4 propostas geradas, renderizadas e salvas com sucesso!")
