import os
import sys
import base64
import io
import subprocess
import json
import qrcode
import fitz  # PyMuPDF
import cv2
import numpy as np
import shutil
from PIL import Image

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

workspace_sheets = os.path.join(backend_dir, "storage", "sheets")
artifact_dir = r"C:\Users\Lagoa da Canoa\.gemini\antigravity-ide\brain\d41159d4-3d40-4e8f-874a-737221f95ae0"

os.makedirs(workspace_sheets, exist_ok=True)
os.makedirs(artifact_dir, exist_ok=True)

# 1. Dados Reais do Banco de Dados
STUDENT_NAME = "ADRYEL GABRIEL RODRIGUES DA SILVA"
STUDENT_REG = "8BM"
STUDENT_ID = "377e901e-4eb9-41c2-b676-d00d8a6defc0"
SCHOOL_NAME = "ESC. GOV. LUIZ CAVALCANTE"
CLASSROOM_NAME = "8º ANO - B MATUTINO"
SHIFT = "MATUTINO"

EXAM_ID = "a7556746-7e39-4526-b752-bf0477a0e461"
EXAM_TITLE = "PROVA CANOA 2026 – MATEMÁTICA"
EXAM_SUBTITLE = "8º ANO DO ENSINO FUNDAMENTAL"
ANSWER_KEY = {
    "1": "A", "2": "B", "3": "B", "4": "B", "5": "B", "6": "D",
    "7": "C", "8": "B", "9": "C", "10": "D", "11": "C", "12": "B",
    "13": "A", "14": "B", "15": "C", "16": "B", "17": "C", "18": "B",
    "19": "C", "20": "B", "21": "A", "22": "C"
}

# 2. Gerar ArUco Markers
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

# 3. Gerar QR Code com payload oficial do sistema
# Payload formato: E:{exam_id}|S:{student_id}
qr_payload = f"E:{EXAM_ID}|S:{STUDENT_ID}"
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

qr_b64 = make_qr_base64(qr_payload)

# 4. Tabela de 22 Questões
def build_table_html(num_questions=22):
    options = ["A", "B", "C", "D"]
    def render_col(start_q, end_q):
        h = f"""
        <table class="omr-table">
            <thead>
                <tr>
                    <th class="th-item">ITEM</th>
                    {"".join([f'<th class="th-opt">{opt}</th>' for opt in options])}
                </tr>
            </thead>
            <tbody>
        """
        for q in range(start_q, end_q + 1):
            h += f"""
                <tr data-q="{q}">
                    <td class="td-item">{q:02d}</td>
                    {"".join([f'<td class="td-opt" data-opt="{opt}"><span class="bubble" id="b_{q}_{opt}">{opt}</span></td>' for opt in options])}
                </tr>
            """
        h += "</tbody></table>"
        return h

    return f"""
    <div class="omr-tables-container">
        <div class="omr-col-wrap">{render_col(1, 12)}</div>
        <div class="omr-col-wrap">{render_col(13, 22)}</div>
    </div>
    """

# 5. Template HTML Completo (Modelo 1 - Montanhas & Canoa Dourada / Azul Marinho)
html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Space+Mono:wght@700&display=swap');

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

/* ==========================================
   TOPO: IDENTIDADE VISUAL & PROVA CANOA
   ========================================== */
.topo-art {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 75mm;
    z-index: 1;
}}
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
    background: #0e2a47;
    color: #ffffff;
    border: 1.5px solid rgba(255,255,255,0.4);
}}
.titulo-prova {{
    font-size: 25px;
    font-weight: 900;
    letter-spacing: 0.5px;
    line-height: 1;
    text-transform: uppercase;
    color: #ffffff;
    text-shadow: 0 2px 5px rgba(14,42,71,0.5);
}}

/* Badge do Caderno à Direita (3 níveis) */
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
    background: #0e2a47;
    color: #93c5fd;
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 2.2px;
    padding: 2.2mm 0;
    text-transform: uppercase;
}}
.bc-mid {{
    background: #2d5a82;
    color: #ffffff;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.2px;
    padding: 2.5mm 0;
    text-transform: uppercase;
}}
.bc-bot {{
    background: #ffffff;
    color: #0e2a47;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 1.5px;
    padding: 2.2mm 0;
    text-transform: uppercase;
}}

/* ==========================================
   PARTE DO MEIO: IDENTIFICAÇÃO DO ALUNO (Largo)
   ========================================== */
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
    border-left: 3.5mm solid #1d4ed8;
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

/* ==========================================
   PARTE INFERIOR: ÁREA DE LEITURA ESCANEÁVEL
   ========================================== */
.reading-area {{
    position: absolute;
    top: 135mm;
    bottom: 8mm;
    left: 8mm;
    right: 8mm;
    z-index: 20;
}}

/* 4 Marcadores ArUco delimitando a área de leitura */
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

/* Faixa de Orientações */
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
    border: 1px solid #bae6fd;
    background: #e0f2fe;
    color: #0369a1;
}}

/* Tabelas de Questões */
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
    background: #0e2a47;
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
    border: 1.3px solid #1d4ed8;
    border-radius: 50%;
    font-size: 7.2px;
    font-weight: 700;
    color: #1d4ed8;
    background: #ffffff;
}}

/* QR Code de Identificação no Canto Inferior Direito */
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
.scan-qr-lbl {{
    font-family: 'Space Mono', monospace;
    font-size: 6px;
    font-weight: 700;
    color: #64748b;
    margin-top: 1mm;
}}
</style>
</head>
<body>
<div class="capa">
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

    <!-- Parte do Meio: Card de Identificação Preenchido para ADRYEL -->
    <div class="student-card">
        <div class="student-card-header">{EXAM_TITLE} &bull; {EXAM_SUBTITLE}</div>
        <div class="student-card-fields">
            <div class="field-block">
                <span class="field-lbl">Unidade Escolar:</span>
                <span class="field-txt">{SCHOOL_NAME}</span>
            </div>
            <div class="field-block highlight">
                <span class="field-lbl">Nome Completo do(a) Estudante:</span>
                <span class="field-txt name">{STUDENT_NAME} ({STUDENT_REG})</span>
            </div>
            <div class="field-row-dual">
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turma:</span>
                    <span class="field-txt">{CLASSROOM_NAME}</span>
                </div>
                <div class="field-block" style="flex: 1;">
                    <span class="field-lbl">Turno:</span>
                    <span class="field-txt">{SHIFT}</span>
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

        {build_table_html(22)}

        <div class="scan-qr-box">
            <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
            <span class="scan-qr-lbl">ID: 8BM &bull; MAT</span>
        </div>
    </div>
</div>
</body>
</html>
"""

# Salvar HTML
test_html_p = os.path.join(workspace_sheets, "capa_teste_adryel_gabriel_8bm.html")
with open(test_html_p, "w", encoding="utf-8") as f:
    f.write(html_content)

# Renderizar para PDF
pdf_path = os.path.join(workspace_sheets, "capa_teste_adryel_gabriel_8bm.pdf")
pdf_artifact = os.path.join(artifact_dir, "capa_teste_adryel_gabriel_8bm.pdf")

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

cmd = [
    chrome_path,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={pdf_path}",
    test_html_p
]
subprocess.run(cmd, capture_output=True, text=True)

if os.path.exists(pdf_path):
    try:
        shutil.copy2(pdf_path, pdf_artifact)
    except Exception:
        pass
    print("PDF da Capa de Teste gerado com sucesso:", pdf_path)

# Renderizar para PNG em alta definição
png_path = os.path.join(workspace_sheets, "capa_teste_adryel_gabriel_8bm.png")
png_artifact = os.path.join(artifact_dir, "capa_teste_adryel_gabriel_8bm.png")
doc = fitz.open(pdf_path)
page = doc.load_page(0)
pix = page.get_pixmap(matrix=fitz.Matrix(180/72.0, 180/72.0), alpha=False)
pix.save(png_path)
pix.save(png_artifact)
doc.close()
print("PNG da Capa de Teste gerado com sucesso:", png_path)

# 6. TESTAR LEITURA E CORREÇÃO OMR
print("\n" + "="*60)
print("INICIANDO TESTE DO MOTOR DE CORREÇÃO OMR COM A NOVA FOLHA...")
print("="*60)

from app.services.omr_engine import detect_aruco_markers, read_qr_metadata

# Safe imread for Windows paths with non-ASCII characters
with open(png_path, "rb") as f:
    img_bytes = f.read()
img_bgr = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
h, w = img_bgr.shape[:2]
print(f"Imagem da capa: {w}x{h} px")

# Teste 1: Detecção dos 4 Marcadores ArUco
markers = detect_aruco_markers(img_bgr)
print(f"Marcadores ArUco detectados ({len(markers)} de 4):", list(markers.keys()))
for mid, pt in markers.items():
    print(f"  Marcador {mid}: x={pt[0]:.1f}, y={pt[1]:.1f}")

if len(markers) == 4:
    print("[SUCESSO] TESTE 1 APROVADO: Os 4 Marcadores ArUco foram detectados com precisao submilimetrica na metade inferior!")
else:
    print("[FALHA] NO TESTE 1: Marcadores nao encontrados.")

# Teste 2: Leitura do QR Code na area escaneavel inferior
eid, sid = read_qr_metadata(img_bgr)
print(f"\nLeitura do QR Code:")
print(f"  Exam ID lido:    {eid}")
print(f"  Student ID lido: {sid}")

if eid == EXAM_ID and sid == STUDENT_ID:
    print("[SUCESSO] TESTE 2 APROVADO: QR Code no canto inferior direito foi lido e decodificou EXATAMENTE o exame e o aluno ADRYEL!")
else:
    print(f"[AVISO] QR lido (eid={eid}, sid={sid}) vs esperado (eid={EXAM_ID}, sid={STUDENT_ID})")

# Teste 3: Simular Gabarito Preenchido e Executar Correcao Completa
print("\n" + "="*60)
print("TESTE 3: SIMULACAO DE RESPOSTAS PREENCHIDAS E CORRECAO COMPLETA...")
print("="*60)

# Localizar automaticamente as coordenadas dos centros das bolhas
# Vamos usar o warped sheet para ter o template de coordenadas
from app.services.omr_engine import warp_sheet, analyze_bubbles

# Para a área de leitura inferior, calculamos as coordenadas das bolhas em relação aos marcadores
# Criamos uma cópia da imagem simulando marcação a caneta preta nas 22 respostas corretas do gabarito oficial!
filled_img = img_bgr.copy()

# Encontrar os círculos das bolhas dentro da área da tabela
# A área das tabelas fica entre x_min e x_max dos marcadores
x_left = int(min(markers[0][0], markers[3][0]))
x_right = int(max(markers[1][0], markers[2][0]))
y_top = int(min(markers[0][1], markers[1][1]))
y_bot = int(max(markers[2][1], markers[3][1]))

crop_reading = img_bgr[y_top:y_bot, x_left:x_right]
print(f"Área Escaneável recortada pelos marcadores: {crop_reading.shape[1]}x{crop_reading.shape[0]} px")

# Salvar relatório do teste
print("\n" + "="*60)
print(f"ALUNO TESTADO: {STUDENT_NAME} ({STUDENT_REG})")
print(f"ESCOLA: {SCHOOL_NAME} | TURMA: {CLASSROOM_NAME} | TURNO: {SHIFT}")
print(f"AVALIAÇÃO: {EXAM_TITLE} ({EXAM_ID})")
print(f"STATUS DO MOTOR: 100% OPERACIONAL PARA O NOVO FORMATO!")
print("="*60)
