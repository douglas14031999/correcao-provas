import os
import sys
import base64
import fitz

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from app.services.reports.exam_cover_builder import generate_exam_cover
from app.services.reports.exam_cover_builder_v2 import (
    render_design_modern_tech,
    render_design_editorial_instructions,
    render_design_formal_gov,
    render_design_dynamic_wave
)

artifact_dir = r"C:\Users\Lagoa da Canoa\.gemini\antigravity-ide\brain\d41159d4-3d40-4e8f-874a-737221f95ae0"
workspace_sheets = os.path.join(backend_dir, "storage", "sheets")
project_root = os.path.dirname(backend_dir)
os.makedirs(artifact_dir, exist_ok=True)
os.makedirs(workspace_sheets, exist_ok=True)

def convert_pdf_to_png(pdf_path, png_path, dpi=180):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(png_path)
    doc.close()

# 1. Generate Models 5 to 8
new_models = [
    {
        "id": "modelo_5_modern_tech",
        "name": "Design 5: Minimalista Tech (Padrão INEP / ENEM)",
        "tag": "Estilo Modern Tech",
        "file_pdf": "modelo_5_modern_tech.pdf",
        "file_png": "modelo_5_modern_tech.png",
        "desc": "Header escuro geométrico (#0f172a / azul elétrico), visual executivo, tipografia de alto impacto, linhas limpas e zebra suave nas alternativas.",
        "func": lambda p: render_design_modern_tech(p, year="2026", caderno_code="MAT-0402", discipline="MATEMÁTICA", grade_stage="4º ano do Ensino Fundamental", num_questions=22, num_alternatives=4)
    },
    {
        "id": "modelo_6_editorial_instrucoes",
        "name": "Design 6: Educativo com Guia Ilustrado (Estilo Lemann / Nova Escola)",
        "tag": "Estilo Educativo",
        "file_pdf": "modelo_6_editorial_instrucoes.pdf",
        "file_png": "modelo_6_editorial_instrucoes.png",
        "desc": "Paleta verde-esmeralda e âmbar, banner visual didático ensinando o aluno a preencher a bolha (● Correto, ✕ Errado), amigável e acessível.",
        "func": lambda p: render_design_editorial_instructions(p, year="2026", caderno_code="LP-0501", discipline="LÍNGUA PORTUGUESA", grade_stage="5º ano do Ensino Fundamental", num_questions=22, num_alternatives=4)
    },
    {
        "id": "modelo_7_formal_governo",
        "name": "Design 7: Institucional Oficial de Governo (Estilo Prova Brasil / Clássico)",
        "tag": "Estilo Governo Oficial",
        "file_pdf": "modelo_7_formal_governo.pdf",
        "file_png": "modelo_7_formal_governo.png",
        "desc": "Borda dupla clássica, cabeçalho governamental centralizado em caixa alta, tabela institucional rigorosa (Escola, Turma, Turno, Estudante).",
        "func": lambda p: render_design_formal_gov(p, year="2026", caderno_code="M0402", discipline="MATEMÁTICA", grade_stage="4º ANO DO ENSINO FUNDAMENTAL", num_questions=22, num_alternatives=4)
    },
    {
        "id": "modelo_8_curvas_dinamicas",
        "name": "Design 8: Ondas Contemporâneas (Estilo CAEd Waves & Gradients)",
        "tag": "Estilo Ondas Dinâmicas",
        "file_pdf": "modelo_8_curvas_dinamicas.pdf",
        "file_png": "modelo_8_curvas_dinamicas.png",
        "desc": "Faixas onduladas fluidas em azul marinho e azul royal, badge flutuante, 26 questões com 5 alternativas (A, B, C, D, E) e linhas zebra de alto contraste.",
        "func": lambda p: render_design_dynamic_wave(p, year="2026", caderno_code="SIM-0901", discipline="CIÊNCIAS DA NATUREZA", grade_stage="9º ano do Ensino Fundamental", num_questions=26, num_alternatives=5)
    }
]

for m in new_models:
    pdf_ws = os.path.join(workspace_sheets, m["file_pdf"])
    png_ws = os.path.join(workspace_sheets, m["file_png"])
    pdf_art = os.path.join(artifact_dir, m["file_pdf"])
    png_art = os.path.join(artifact_dir, m["file_png"])
    
    m["func"](pdf_ws)
    m["func"](pdf_art)
    convert_pdf_to_png(pdf_ws, png_ws, dpi=180)
    convert_pdf_to_png(pdf_art, png_art, dpi=180)
    print(f"Generated: {m['id']}")

# 2. Build Updated visualizador_capas.html with ALL 8 MODELS
all_models = [
    # Initial 4 (Floral CAEd)
    {
        "id": "modelo_1",
        "name": "Modelo 1: Matemática 4º Ano (22 Questões, A-D)",
        "tag": "Padrão CAEd / SAEB Fiel",
        "file_png": "modelo_1_matematica_4ano_22q.png",
        "file_pdf": "modelo_1_matematica_4ano_22q.pdf",
        "desc": "Fiel ao modelo da imagem original enviada (Caderno M0402, 22 questões, 4 alternativas A-D, marca d'água superior de pétalas)."
    },
    {
        "id": "modelo_2",
        "name": "Modelo 2: Língua Portuguesa 5º Ano (22 Questões, A-D)",
        "tag": "Padrão CAEd / SAEB Fiel",
        "file_png": "modelo_2_portugues_5ano_22q.png",
        "file_pdf": "modelo_2_portugues_5ano_22q.pdf",
        "desc": "Variação da capa oficial para Língua Portuguesa Ciclo II (Caderno P0501, 22 questões, 4 alternativas A-D)."
    },
    {
        "id": "modelo_3",
        "name": "Modelo 3: Simulado 9º Ano (26 Questões, A-E)",
        "tag": "Padrão CAEd / 5 Alternativas",
        "file_png": "modelo_3_simulado_9ano_26q_5alt.png",
        "file_pdf": "modelo_3_simulado_9ano_26q_5alt.pdf",
        "desc": "Modelo estendido para Ensino Fundamental II (Caderno CN0901, 26 questões, 5 alternativas A-E)."
    },
    {
        "id": "modelo_4",
        "name": "Modelo 4: Alfabetização 2º Ano (20 Questões, A-D)",
        "tag": "Padrão CAEd / Ciclo I",
        "file_png": "modelo_4_ciclo1_alfabetizacao_20q.png",
        "file_pdf": "modelo_4_ciclo1_alfabetizacao_20q.pdf",
        "desc": "Modelo adaptado para Ciclo I / Alfabetização (Caderno P0201, 20 questões, 4 alternativas A-D)."
    },
    # New 4 Different Designs
    new_models[0],
    new_models[1],
    new_models[2],
    new_models[3]
]

cards_html = ""
for m in all_models:
    png_path = os.path.join(workspace_sheets, m["file_png"])
    pdf_rel = "backend/storage/sheets/" + m["file_pdf"]
    png_rel = "backend/storage/sheets/" + m["file_png"]
    
    b64_img = ""
    if os.path.exists(png_path):
        with open(png_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")

    cards_html += f"""
    <div class="model-card" id="{m['id']}">
        <div class="card-header">
            <span class="card-badge">{m['tag']}</span>
            <h2>{m['name']}</h2>
            <p>{m['desc']}</p>
            <div class="actions">
                <a href="{pdf_rel}" target="_blank" class="btn btn-primary">📄 Abrir PDF (Imprimir)</a>
                <a href="{png_rel}" target="_blank" class="btn btn-secondary">🔍 Imagem em Alta Resolução</a>
            </div>
        </div>
        <div class="card-body">
            <img src="data:image/png;base64,{b64_img}" alt="{m['name']}" class="cover-img" />
        </div>
    </div>
    """

html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo Completo: 8 Modelos de Capa & Cartão-Resposta</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0b0f19;
            --surface: #151d2c;
            --border: #233044;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 40px 20px;
            line-height: 1.5;
        }}
        header {{
            max-width: 1200px;
            margin: 0 auto 35px auto;
            text-align: center;
        }}
        header h1 {{
            font-size: 2.3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa, #38bdf8, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        header p {{
            color: var(--text-muted);
            font-size: 1.05rem;
        }}
        .filter-bar {{
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .filter-btn {{
            background: #1e293b;
            color: #94a3b8;
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: #2563eb;
            color: #fff;
            border-color: #3b82f6;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 35px;
            max-width: 1400px;
            margin: 30px auto 0 auto;
        }}
        .model-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .model-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 18px 35px -5px rgba(0, 0, 0, 0.7);
            border-color: #3b82f6;
        }}
        .card-header {{
            padding: 22px 26px;
            border-bottom: 1px solid var(--border);
            background: #192233;
        }}
        .card-badge {{
            display: inline-block;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.4);
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 12px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .card-header h2 {{
            font-size: 1.22rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 8px;
        }}
        .card-header p {{
            font-size: 0.88rem;
            color: var(--text-muted);
            margin-bottom: 18px;
        }}
        .actions {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            padding: 9px 16px;
            border-radius: 8px;
            font-size: 0.86rem;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-primary {{
            background: var(--accent);
            color: #fff;
        }}
        .btn-primary:hover {{
            background: var(--accent-hover);
        }}
        .btn-secondary {{
            background: #233044;
            color: #e2e8f0;
            border: 1px solid #334155;
        }}
        .btn-secondary:hover {{
            background: #2d3d57;
            color: #fff;
        }}
        .card-body {{
            padding: 24px;
            background: #090c15;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .cover-img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.6);
            background: #fff;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Catálogo de Capas & Cartões-Resposta</h1>
        <p>Explore 8 opções e estilos de design para avaliações educacionais municipais e simulados</p>
        <div class="filter-bar">
            <a href="#modelo_1" class="filter-btn">1 a 4: Estilo CAEd Floral</a>
            <a href="#modelo_5_modern_tech" class="filter-btn">5: Minimalista Tech</a>
            <a href="#modelo_6_editorial_instrucoes" class="filter-btn">6: Educativo Ilustrado</a>
            <a href="#modelo_7_formal_governo" class="filter-btn">7: Institucional Governo</a>
            <a href="#modelo_8_curvas_dinamicas" class="filter-btn">8: Ondas Contemporâneas</a>
        </div>
    </header>
    <main class="grid">
        {cards_html}
    </main>
</body>
</html>
"""

# Write to root and backend
with open(os.path.join(project_root, "visualizador_capas.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

with open(os.path.join(backend_dir, "visualizador_capas.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print("Visualizador atualizado com sucesso com todos os 8 modelos!")
