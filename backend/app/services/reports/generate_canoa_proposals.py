import os
import sys
import base64
import io
import subprocess
import qrcode
import fitz  # PyMuPDF

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

# OMR Question Columns (22 questions)
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
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&family=Poppins:wght@600;700;800&family=Nunito:wght@600;700;800&family=Space+Mono:wght@700&display=swap');

@page {
    size: 210mm 297mm;
    margin: 0;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #fff;
    font-family: 'Montserrat', Arial, sans-serif;
    color: #333;
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

/* Card com Dados do Aluno Preenchidos & QR Code */
.student-card {
    position: absolute;
    left: 14mm;
    right: 14mm;
    background: #fff;
    border-radius: 4mm;
    padding: 4.5mm 5.5mm;
    box-shadow: 0 2.5mm 6mm rgba(0,0,0,0.08);
    z-index: 10;
}
.card-subj {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 3mm;
    padding-bottom: 2mm;
}
.student-grid {
    display: grid;
    grid-template-columns: 1fr 26mm;
    gap: 3.5mm;
    align-items: center;
}
.data-fields {
    display: flex;
    flex-direction: column;
    gap: 2mm;
}
.row-dual {
    display: flex;
    gap: 3.5mm;
}
.field-block {
    flex: 1;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 2mm;
    padding: 1.5mm 2.5mm;
}
.field-block.highlight {
    background: #f1f5f9;
    border-color: #94a3b8;
}
.field-label {
    font-size: 7.2px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    display: block;
    margin-bottom: 1px;
}
.field-val {
    font-size: 9.5px;
    font-weight: 700;
    color: #0f172a;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.field-val.name {
    font-size: 11px;
    font-weight: 800;
    color: #0b192c;
    letter-spacing: 0.2px;
}
.birth-boxes {
    display: flex;
    gap: 1mm;
    margin-top: 1px;
}
.b-box {
    width: 4.5mm;
    height: 5.5mm;
    background: #fff;
    border: 1px solid #94a3b8;
    border-radius: 0.8mm;
    font-size: 8.5px;
    font-weight: 800;
    color: #0f172a;
    display: flex;
    align-items: center;
    justify-content: center;
}
.b-sep { width: 1.5mm; }

/* QR Code */
.qr-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #fff;
    border: 1.2px solid #cbd5e1;
    border-radius: 2mm;
    padding: 1.8mm;
}
.qr-container img {
    width: 20mm;
    height: 20mm;
    display: block;
}
.qr-label {
    font-family: 'Space Mono', monospace;
    font-size: 6.5px;
    font-weight: 700;
    color: #334155;
    margin-top: 1mm;
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
    padding: 1.8mm 3.5mm;
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
    bottom: 10.5mm;
    right: 14mm;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    z-index: 10;
}
"""

# Template 1: Rio & Canoa (Verde Petróleo)
html_p1 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.m1 {{ background: linear-gradient(180deg, #f0fdf9 0%, #ffffff 42%); }}
.m1 .topo {{ display: flex; justify-content: space-between; padding: 15mm 15mm 0; position: relative; z-index: 5; }}
.m1 .ano {{ border: 2px solid #0e7c7b; color: #0e7c7b; font-weight: 800; padding: 1.5mm 4.5mm; border-radius: 20px; font-size: 11px; letter-spacing: 2px; background: #fff; }}
.m1 .topo small {{ font-size: 8.5px; color: #0e7c7b; text-align: right; max-width: 60mm; font-weight: 700; line-height: 1.35; }}
.m1 h1 {{ font-size: 32px; font-weight: 800; color: #0b5d5c; line-height: 1.05; padding: 6mm 15mm 0; letter-spacing: -0.5px; position: relative; z-index: 5; }}
.m1 h1 em {{ font-style: normal; color: #f4a261; }}
.m1 .caderno {{ position: absolute; top: 62mm; right: 15mm; background: #0e7c7b; color: #fff; padding: 2.5mm 5.5mm; border-radius: 3mm; font-weight: 800; letter-spacing: 2px; z-index: 5; box-shadow: 0 2mm 5mm rgba(14,124,123,0.3); }}
.m1 .caderno small {{ display: block; font-size: 7.5px; letter-spacing: 3px; opacity: 0.85; }}
.m1 .rio {{ position: absolute; top: 68mm; left: 0; width: 100%; z-index: 2; }}
.m1 .student-card {{ top: 102mm; border-top: 2.5mm solid #0e7c7b; box-shadow: 0 3mm 8mm rgba(14,124,123,0.12); }}
.m1 .card-subj {{ border-bottom: 1px solid #e2e8f0; }}
.m1 .card-subj b {{ color: #0e7c7b; font-size: 13px; }}
.m1 .card-subj span {{ font-size: 10px; color: #475569; font-weight: 600; }}
.m1 .omr-wrap {{ top: 168mm; }}
.m1 .omr-instructions {{ background: #e6f7f6; color: #0e7c7b; border: 1px solid #b2e6e3; }}
.m1 .q .n {{ background: #e6f7f6; color: #0b5d5c; }}
.m1 .q .b {{ border-color: #0e7c7b; }}
.m1 .footer-code {{ color: #0e7c7b; }}
</style>
</head>
<body>
<div class="capa m1">
    <div class="mark tl"></div><div class="mark tr"></div><div class="mark bl"></div><div class="mark br"></div>
    <div class="topo">
        <div class="ano">2026</div>
        <small>AVALIAÇÃO CONTÍNUA DA<br>APRENDIZAGEM — CICLO II</small>
    </div>
    <h1>PROVA <em>CANOA</em><br>Navegando no<br>conhecimento</h1>
    <div class="caderno"><small>CADERNO</small>M0402</div>
    <svg class="rio" viewBox="0 0 800 120" preserveAspectRatio="none">
        <path d="M0 60 Q100 20 200 60 T400 60 T600 60 T800 60 V120 H0 Z" fill="#d5efed"/>
        <path d="M0 80 Q100 45 200 80 T400 80 T600 80 T800 80 V120 H0 Z" fill="#0e7c7b"/>
        <path d="M330 48 Q400 78 470 48 Q400 64 330 48Z" fill="#f4a261"/>
        <line x1="400" y1="46" x2="400" y2="18" stroke="#8d5a2b" stroke-width="3"/>
        <path d="M400 18 Q425 26 400 40Z" fill="#fff"/>
    </svg>
    <div class="student-card">
        <div class="card-subj">
            <b>MATEMÁTICA</b>
            <span>4º ano do Ensino Fundamental</span>
        </div>
        <div class="student-grid">
            <div class="data-fields">
                <div class="field-block">
                    <span class="field-label">Unidade Escolar / Escola:</span>
                    <span class="field-val">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
                </div>
                <div class="field-block highlight">
                    <span class="field-label">Nome Completo do(a) Estudante:</span>
                    <span class="field-val name">LUCAS GABRIEL DOS SANTOS SILVA</span>
                </div>
                <div class="row-dual">
                    <div class="field-block" style="flex: 1.1;">
                        <span class="field-label">Turma & Turno:</span>
                        <span class="field-val">4º ANO A &bull; MANHÃ</span>
                    </div>
                    <div class="field-block" style="flex: 1.3;">
                        <span class="field-label">Data de Nascimento:</span>
                        <div class="birth-boxes">
                            <div class="b-box">1</div><div class="b-box">4</div>
                            <div class="b-sep"></div>
                            <div class="b-box">0</div><div class="b-box">3</div>
                            <div class="b-sep"></div>
                            <div class="b-box">2</div><div class="b-box">0</div><div class="b-box">1</div><div class="b-box">5</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="qr-container">
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

# Template 2: Pôr do Sol (Solar / Laranja)
html_p2 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.mA {{ background: linear-gradient(180deg, #fff7ed 0%, #ffede0 35%, #ffffff 60%); }}
.mA .sun {{ position: absolute; top: 20mm; right: 25mm; width: 32mm; height: 32mm; background: radial-gradient(circle, #ffb703 0%, #fb8500 70%); border-radius: 50%; box-shadow: 0 0 20mm #ffd68a; z-index: 1; }}
.mA .topo {{ display: flex; justify-content: space-between; padding: 15mm 15mm 0; position: relative; z-index: 5; }}
.mA .ano {{ border: 2px solid #fb8500; color: #fb8500; font-weight: 800; padding: 1.5mm 4.5mm; border-radius: 20px; font-size: 11px; letter-spacing: 2px; background: #fff; }}
.mA .topo small {{ font-size: 8.5px; color: #c05621; text-align: right; max-width: 60mm; font-weight: 700; line-height: 1.35; }}
.mA h1 {{ font-family: 'Poppins', sans-serif; font-size: 32px; font-weight: 800; color: #9c3d00; line-height: 1.05; padding: 8mm 15mm 0; position: relative; z-index: 5; }}
.mA h1 em {{ font-style: normal; color: #fb8500; }}
.mA .caderno {{ position: absolute; top: 68mm; left: 15mm; background: #fb8500; color: #fff; padding: 2.5mm 5.5mm; border-radius: 3mm; font-weight: 800; letter-spacing: 2px; z-index: 5; box-shadow: 0 2mm 5mm rgba(251,133,0,0.35); }}
.mA .caderno small {{ display: block; font-size: 7.5px; letter-spacing: 3px; opacity: 0.85; }}
.mA .rio {{ position: absolute; top: 74mm; left: 0; width: 100%; z-index: 2; }}
.mA .student-card {{ top: 104mm; border-top: 2.5mm solid #fb8500; box-shadow: 0 3mm 8mm rgba(155,61,0,0.12); }}
.mA .card-subj {{ border-bottom: 1px solid #fed7aa; }}
.mA .card-subj b {{ color: #c05621; font-size: 13px; }}
.mA .card-subj span {{ font-size: 10px; color: #475569; font-weight: 600; }}
.mA .omr-wrap {{ top: 168mm; }}
.mA .omr-instructions {{ background: #fff7ed; color: #c05621; border: 1px solid #fed7aa; }}
.mA .q .n {{ background: #ffedd5; color: #9a3412; }}
.mA .q .b {{ border-color: #fb8500; }}
.mA .footer-code {{ color: #c05621; }}
</style>
</head>
<body>
<div class="capa mA">
    <div class="mark tl"></div><div class="mark tr"></div><div class="mark bl"></div><div class="mark br"></div>
    <div class="sun"></div>
    <div class="topo">
        <div class="ano">2026</div>
        <small>AVALIAÇÃO CONTÍNUA DA<br>APRENDIZAGEM — CICLO II</small>
    </div>
    <h1>PROVA <em>CANOA</em><br>Rumo ao<br>horizonte</h1>
    <div class="caderno"><small>CADERNO</small>M0402</div>
    <svg class="rio" viewBox="0 0 800 120" preserveAspectRatio="none">
        <path d="M0 60 Q100 30 200 60 T400 60 T600 60 T800 60 V120 H0Z" fill="#ffd8a8"/>
        <path d="M0 82 Q100 52 200 82 T400 82 T600 82 T800 82 V120 H0Z" fill="#fb8500"/>
        <path d="M330 50 Q400 80 470 50 Q400 66 330 50Z" fill="#7f4f24"/>
        <line x1="400" y1="48" x2="400" y2="20" stroke="#5c3a1a" stroke-width="3"/>
        <path d="M400 20 Q425 28 400 42Z" fill="#fff"/>
    </svg>
    <div class="student-card">
        <div class="card-subj">
            <b>MATEMÁTICA</b>
            <span>4º ano do Ensino Fundamental</span>
        </div>
        <div class="student-grid">
            <div class="data-fields">
                <div class="field-block">
                    <span class="field-label">Unidade Escolar / Escola:</span>
                    <span class="field-val">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
                </div>
                <div class="field-block highlight">
                    <span class="field-label">Nome Completo do(a) Estudante:</span>
                    <span class="field-val name">LUCAS GABRIEL DOS SANTOS SILVA</span>
                </div>
                <div class="row-dual">
                    <div class="field-block" style="flex: 1.1;">
                        <span class="field-label">Turma & Turno:</span>
                        <span class="field-val">4º ANO A &bull; MANHÃ</span>
                    </div>
                    <div class="field-block" style="flex: 1.3;">
                        <span class="field-label">Data de Nascimento:</span>
                        <div class="birth-boxes">
                            <div class="b-box">1</div><div class="b-box">4</div>
                            <div class="b-sep"></div>
                            <div class="b-box">0</div><div class="b-box">3</div>
                            <div class="b-sep"></div>
                            <div class="b-box">2</div><div class="b-box">0</div><div class="b-box">1</div><div class="b-box">5</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="qr-container" style="border-color: #fed7aa;">
                <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
                <span class="qr-label" style="color: #c05621;">ID: 2026.04.0921</span>
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

# Template 3: Canoa & Montanhas (Azul Marinho)
html_p3 = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
{COMMON_CSS}
.mB {{ background: #f0f7fa; }}
.mB .mount {{ position: absolute; top: 0; left: 0; width: 100%; height: 82mm; z-index: 1; }}
.mB .topo {{ display: flex; justify-content: space-between; align-items: flex-start; padding: 12mm 15mm 0; position: relative; z-index: 5; }}
.mB .ano {{ background: #1d3557; color: #fff; font-weight: 800; padding: 1.5mm 4.5mm; border-radius: 4px; font-size: 11px; letter-spacing: 2px; }}
.mB .topo-center {{ text-align: right; margin-right: 32mm; }}
.mB .topo small {{ font-size: 8.5px; color: #ffffff; text-shadow: 0 1px 2px rgba(0,0,0,0.5); text-align: right; font-weight: 700; line-height: 1.35; display: block; }}
.mB h1 {{ font-family: 'Nunito', sans-serif; font-size: 32px; font-weight: 800; color: #ffffff; line-height: 1.05; padding: 14mm 15mm 0; position: relative; z-index: 5; text-shadow: 0 1mm 3mm rgba(29,53,87,0.6); }}
.mB h1 em {{ font-style: normal; color: #ffd166; }}
.mB .caderno {{ position: absolute; top: 12mm; right: 15mm; background: #457b9d; color: #fff; padding: 2.2mm 5mm; border-radius: 3mm; font-weight: 800; letter-spacing: 2px; z-index: 5; }}
.mB .caderno small {{ display: block; font-size: 7px; letter-spacing: 3px; opacity: 0.85; }}
.mB .student-card {{ top: 94mm; border-left: 3mm solid #457b9d; box-shadow: 0 3mm 8mm rgba(29,53,87,0.12); }}
.mB .card-subj {{ border-bottom: 1px solid #e2e8f0; }}
.mB .card-subj b {{ color: #1d3557; font-size: 13px; }}
.mB .card-subj span {{ font-size: 10px; color: #475569; font-weight: 600; }}
.mB .omr-wrap {{ top: 164mm; }}
.mB .omr-instructions {{ background: #e2eef5; color: #1d3557; border: 1px solid #bcd7e6; }}
.mB .q .n {{ background: #dbeaf2; color: #1d3557; }}
.mB .q .b {{ border-color: #457b9d; }}
.mB .footer-code {{ color: #457b9d; }}
</style>
</head>
<body>
<div class="capa mB">
    <div class="mark tl"></div><div class="mark tr"></div><div class="mark bl"></div><div class="mark br"></div>
    <svg class="mount" viewBox="0 0 800 340" preserveAspectRatio="none">
        <rect width="800" height="340" fill="#a8dadc"/>
        <path d="M0 200 L150 90 L280 210 L420 70 L560 200 L680 120 L800 220 V340 H0Z" fill="#457b9d"/>
        <path d="M0 250 L120 160 L260 260 L400 150 L540 250 L680 180 L800 260 V340 H0Z" fill="#1d3557"/>
        <path d="M0 290 Q200 260 400 290 T800 290 V340 H0Z" fill="#e0fbfc"/>
        <path d="M330 278 Q400 300 470 278 Q400 292 330 278Z" fill="#ffd166"/>
    </svg>
    <div class="topo">
        <div class="ano">2026</div>
        <div class="topo-center">
            <small>AVALIAÇÃO CONTÍNUA DA<br>APRENDIZAGEM — CICLO II</small>
        </div>
    </div>
    <h1>PROVA <em>CANOA</em><br>Explorando<br>caminhos</h1>
    <div class="caderno"><small>CADERNO</small>M0402</div>
    <div class="student-card">
        <div class="card-subj">
            <b>MATEMÁTICA</b>
            <span>4º ano do Ensino Fundamental</span>
        </div>
        <div class="student-grid">
            <div class="data-fields">
                <div class="field-block">
                    <span class="field-label">Unidade Escolar / Escola:</span>
                    <span class="field-val">E. M. GOVERNADOR LUIZ CAVALCANTE</span>
                </div>
                <div class="field-block highlight">
                    <span class="field-label">Nome Completo do(a) Estudante:</span>
                    <span class="field-val name">LUCAS GABRIEL DOS SANTOS SILVA</span>
                </div>
                <div class="row-dual">
                    <div class="field-block" style="flex: 1.1;">
                        <span class="field-label">Turma & Turno:</span>
                        <span class="field-val">4º ANO A &bull; MANHÃ</span>
                    </div>
                    <div class="field-block" style="flex: 1.3;">
                        <span class="field-label">Data de Nascimento:</span>
                        <div class="birth-boxes">
                            <div class="b-box">1</div><div class="b-box">4</div>
                            <div class="b-sep"></div>
                            <div class="b-box">0</div><div class="b-box">3</div>
                            <div class="b-sep"></div>
                            <div class="b-box">2</div><div class="b-box">0</div><div class="b-box">1</div><div class="b-box">5</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="qr-container" style="border-color: #bcd7e6;">
                <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
                <span class="qr-label" style="color: #1d3557;">ID: 2026.04.0921</span>
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

props = [
    ("proposta_1_rio.html", "proposta_1_rio_canoa_verde", html_p1),
    ("proposta_2_pordosol.html", "proposta_2_por_do_sol_laranja", html_p2),
    ("proposta_3_montanhas.html", "proposta_3_canoa_montanhas_azul", html_p3),
]

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

for filename, base_id, content in props:
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

# Update Master Visualizer HTML in project root
catalog_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Propostas de Capa Oficial Prova Canoa</title>
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
        font-size: 2.1rem;
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
        padding: 10px 22px;
        color: #7dd3fc;
        font-size: 0.95rem;
    }}
    .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
        gap: 30px;
        max-width: 1500px;
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
    .b-green {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }}
    .b-orange {{ background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.4); }}
    .b-blue {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }}
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
        <h1>Propostas de Capa & Cartão-Resposta Oficial</h1>
        <p>Adaptações oficiais solicitadas das capas <em>prova-canoa.html</em> e <em>prova-canoa2.html</em></p>
        <div class="callout">
            ✅ <strong>Adaptações Realizadas:</strong> Dados do aluno já pré-preenchidos &bull; QR Code integrado para leitura óptica &bull; 4 Quadrados de Registro OMR nos cantos &bull; Gabarito calibrado de 22 questões.
        </div>
    </header>

    <main class="grid">
        <!-- Opção 1 -->
        <div class="proposal-card">
            <div class="p-header">
                <span class="badge b-green">Modelo 1 de prova-canoa.html</span>
                <h2>Opção 1: Rio & Canoa (Verde Petróleo)</h2>
                <p>Navegando no conhecimento. Visual original com rio em curvas suaves, canoa com vela laranja e tons verde petróleo oficiais.</p>
                <div class="btn-group">
                    <a href="backend/storage/sheets/proposta_1_rio_canoa_verde.pdf" target="_blank" class="btn btn-p">📄 Abrir PDF de Impressão</a>
                    <a href="backend/storage/sheets/proposta_1_rio.html" target="_blank" class="btn btn-s">🌐 Abrir HTML Individual</a>
                </div>
            </div>
            <div class="p-body">
                <img src="backend/storage/sheets/proposta_1_rio_canoa_verde.png" class="preview-img" alt="Opção 1 - Rio & Canoa">
            </div>
        </div>

        <!-- Opção 2 -->
        <div class="proposal-card">
            <div class="p-header">
                <span class="badge b-orange">Modelo 1 de prova-canoa2.html</span>
                <h2>Opção 2: Pôr do Sol no Rio (Solar / Laranja)</h2>
                <p>Rumo ao horizonte. Gradiente aquecido com sol radiante, rio ondulado e detalhes vibrantes em laranja e âmbar.</p>
                <div class="btn-group">
                    <a href="backend/storage/sheets/proposta_2_por_do_sol_laranja.pdf" target="_blank" class="btn btn-p">📄 Abrir PDF de Impressão</a>
                    <a href="backend/storage/sheets/proposta_2_pordosol.html" target="_blank" class="btn btn-s">🌐 Abrir HTML Individual</a>
                </div>
            </div>
            <div class="p-body">
                <img src="backend/storage/sheets/proposta_2_por_do_sol_laranja.png" class="preview-img" alt="Opção 2 - Pôr do Sol">
            </div>
        </div>

        <!-- Opção 3 -->
        <div class="proposal-card">
            <div class="p-header">
                <span class="badge b-blue">Modelo 2 de prova-canoa2.html</span>
                <h2>Opção 3: Canoa & Montanhas (Azul Marinho)</h2>
                <p>Explorando caminhos. Ilustração de montanhas em camadas geométricas com a canoa dourada sobre o rio e azul marinho institucional.</p>
                <div class="btn-group">
                    <a href="backend/storage/sheets/proposta_3_canoa_montanhas_azul.pdf" target="_blank" class="btn btn-p">📄 Abrir PDF de Impressão</a>
                    <a href="backend/storage/sheets/proposta_3_montanhas.html" target="_blank" class="btn btn-s">🌐 Abrir HTML Individual</a>
                </div>
            </div>
            <div class="p-body">
                <img src="backend/storage/sheets/proposta_3_canoa_montanhas_azul.png" class="preview-img" alt="Opção 3 - Canoa e Montanhas">
            </div>
        </div>
    </main>
</body>
</html>
"""

master_html_p = os.path.join(project_root, "propostas_capas_canoa.html")
with open(master_html_p, "w", encoding="utf-8") as f:
    f.write(catalog_html)

print("Catálogo de propostas gerado com sucesso!")
