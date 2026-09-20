import os
import base64

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sheets_dir = os.path.join(project_root, "backend", "storage", "sheets")
output_html = os.path.join(project_root, "visualizador_capas.html")

models = [
    {
        "id": "modelo_1",
        "name": "Modelo 1: Matemática 4º Ano (22 Questões, A-D)",
        "file_png": "modelo_1_matematica_4ano_22q.png",
        "file_pdf": "modelo_1_matematica_4ano_22q.pdf",
        "desc": "Fiel ao modelo da imagem original (Caderno M0402, 22 questões, 4 alternativas A-D, marca d'água superior, QR Code e marcadores fiduciais OMR)."
    },
    {
        "id": "modelo_2",
        "name": "Modelo 2: Língua Portuguesa 5º Ano (22 Questões, A-D)",
        "file_png": "modelo_2_portugues_5ano_22q.png",
        "file_pdf": "modelo_2_portugues_5ano_22q.pdf",
        "desc": "Variação oficial para Língua Portuguesa do Ciclo II (Caderno P0501, 22 questões, 4 alternativas A-D)."
    },
    {
        "id": "modelo_3",
        "name": "Modelo 3: Simulado / 9º Ano (26 Questões, A-E)",
        "file_png": "modelo_3_simulado_9ano_26q_5alt.png",
        "file_pdf": "modelo_3_simulado_9ano_26q_5alt.pdf",
        "desc": "Modelo expandido para Ensino Fundamental II / Prova Brasil (Caderno CN0901, 26 questões, 5 alternativas A-E)."
    },
    {
        "id": "modelo_4",
        "name": "Modelo 4: Alfabetização 2º Ano (20 Questões, A-D)",
        "file_png": "modelo_4_ciclo1_alfabetizacao_20q.png",
        "file_pdf": "modelo_4_ciclo1_alfabetizacao_20q.pdf",
        "desc": "Modelo adaptado para Ciclo I / Alfabetização (Caderno P0201, 20 questões, 4 alternativas A-D)."
    }
]

cards_html = ""
for m in models:
    png_path = os.path.join(sheets_dir, m["file_png"])
    pdf_rel = "backend/storage/sheets/" + m["file_pdf"]
    png_rel = "backend/storage/sheets/" + m["file_png"]
    
    b64_img = ""
    if os.path.exists(png_path):
        with open(png_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")

    cards_html += f"""
    <div class="model-card" id="{m['id']}">
        <div class="card-header">
            <h2>{m['name']}</h2>
            <p>{m['desc']}</p>
            <div class="actions">
                <a href="{pdf_rel}" target="_blank" class="btn btn-primary">📄 Abrir PDF para Imprimir</a>
                <a href="{png_rel}" target="_blank" class="btn btn-secondary">🔍 Abrir Imagem em Alta Resolução</a>
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
    <title>Visualizador de Modelos de Capa - Avaliação Contínua da Aprendizagem</title>
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
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        header p {{
            color: var(--text-muted);
            font-size: 1.05rem;
        }}
        .notice {{
            margin-top: 18px;
            display: inline-block;
            background: rgba(37, 99, 235, 0.12);
            border: 1px solid rgba(59, 130, 246, 0.35);
            border-radius: 8px;
            padding: 10px 20px;
            color: #93c5fd;
            font-size: 0.95rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 35px;
            max-width: 1400px;
            margin: 0 auto;
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
        .card-header h2 {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 8px;
        }}
        .card-header p {{
            font-size: 0.9rem;
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
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 0.88rem;
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
        <h1>Modelos de Capa & Cartão-Resposta Oficial</h1>
        <p>Desenvolvidos com base no padrão da Avaliação Contínua da Aprendizagem / CAEd / SAEB</p>
        <div class="notice">
            🖨️ Os arquivos em PDF estão em tamanho <strong>A4 (alta definição vetorial)</strong>, prontos para impressão ou aplicação no leitor OMR.
        </div>
    </header>
    <main class="grid">
        {cards_html}
    </main>
</body>
</html>
"""

with open(output_html, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Visualizador criado em:", output_html)
