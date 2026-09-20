import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from app.services.reports.exam_cover_builder import generate_exam_cover, render_pdf_to_image

artifact_dir = r"C:\Users\Lagoa da Canoa\.gemini\antigravity-ide\brain\d41159d4-3d40-4e8f-874a-737221f95ae0"
workspace_dir = os.path.join(backend_dir, "storage", "sheets")
os.makedirs(artifact_dir, exist_ok=True)
os.makedirs(workspace_dir, exist_ok=True)

models = [
    {
        "id": "modelo_1_matematica_4ano_22q",
        "title": "Modelo 1 - Matemática 4º Ano (22 Questões, A-D)",
        "params": {
            "year": "2026",
            "main_title_lines": ["AVALIAÇÃO", "CONTÍNUA DA", "APRENDIZAGEM", "CICLO II"],
            "header_subtitle": "AVALIAÇÃO CONTÍNUA DA APRENDIZAGEM - CICLO II",
            "caderno_code": "M0402",
            "discipline": "MATEMÁTICA",
            "grade_stage": "4º ano do Ensino Fundamental",
            "qr_code_text": "2268M0402",
            "num_questions": 22,
            "num_alternatives": 4,
            "tracking_code": "4454197329",
            "caderno_accent_color": "#475569"
        }
    },
    {
        "id": "modelo_2_portugues_5ano_22q",
        "title": "Modelo 2 - Língua Portuguesa 5º Ano (22 Questões, A-D)",
        "params": {
            "year": "2026",
            "main_title_lines": ["AVALIAÇÃO", "CONTÍNUA DA", "APRENDIZAGEM", "CICLO II"],
            "header_subtitle": "AVALIAÇÃO CONTÍNUA DA APRENDIZAGEM - CICLO II",
            "caderno_code": "P0501",
            "discipline": "LÍNGUA PORTUGUESA",
            "grade_stage": "5º ano do Ensino Fundamental",
            "qr_code_text": "2268P0501",
            "num_questions": 22,
            "num_alternatives": 4,
            "tracking_code": "4454198812",
            "caderno_accent_color": "#334155"
        }
    },
    {
        "id": "modelo_3_simulado_9ano_26q_5alt",
        "title": "Modelo 3 - Prova Brasil / Simulado 9º Ano (26 Questões, A-E)",
        "params": {
            "year": "2026",
            "main_title_lines": ["SIMULADO SAEB", "DIAGNÓSTICO", "REDE MUNICIPAL", "ANOS FINAIS"],
            "header_subtitle": "AVALIAÇÃO DIAGNÓSTICA - ENSINO FUNDAMENTAL II",
            "caderno_code": "CN0901",
            "discipline": "CIÊNCIAS DA NATUREZA",
            "grade_stage": "9º ano do Ensino Fundamental",
            "qr_code_text": "3399CN0901",
            "num_questions": 26,
            "num_alternatives": 5,
            "tracking_code": "5519283741",
            "caderno_accent_color": "#1e3a8a"
        }
    },
    {
        "id": "modelo_4_ciclo1_alfabetizacao_20q",
        "title": "Modelo 4 - Ciclo de Alfabetização 2º Ano (20 Questões, A-D)",
        "params": {
            "year": "2026",
            "main_title_lines": ["AVALIAÇÃO", "CONTÍNUA DA", "APRENDIZAGEM", "CICLO I"],
            "header_subtitle": "AVALIAÇÃO DA ALFABETIZAÇÃO - CICLO I",
            "caderno_code": "P0201",
            "discipline": "LÍNGUA PORTUGUESA",
            "grade_stage": "2º ano do Ensino Fundamental",
            "qr_code_text": "1122P0201",
            "num_questions": 20,
            "num_alternatives": 4,
            "tracking_code": "3321456789",
            "caderno_accent_color": "#0f766e"
        }
    }
]

if __name__ == "__main__":
    for m in models:
        pdf_path_art = os.path.join(artifact_dir, f"{m['id']}.pdf")
        png_path_art = os.path.join(artifact_dir, f"{m['id']}.png")
        pdf_path_ws = os.path.join(workspace_dir, f"{m['id']}.pdf")
        
        generate_exam_cover(pdf_path_art, **m["params"])
        generate_exam_cover(pdf_path_ws, **m["params"])
        render_pdf_to_image(pdf_path_art, png_path_art, dpi=180)
        print(f"Generated: {m['id']} -> {png_path_art}")
