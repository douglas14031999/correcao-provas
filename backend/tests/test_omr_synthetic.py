import os
import sys
import numpy as np
import cv2

# Add backend dir to sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TEST_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.pdf_generator import generate_answer_sheet_pdf, generate_aruco_marker_image, CANONICAL_WIDTH, CANONICAL_HEIGHT
from app.services.omr_engine import grade_submission

def test_omr_end_to_end_synthetic():
    print("=== INICIANDO TESTE END-TO-END DE VISÃO COMPUTACIONAL OMR ===")
    
    # 1. Definir Gabarito Oficial de 10 Questões
    num_questions = 10
    answer_key = {
        "1": "A", "2": "B", "3": "C", "4": "D", "5": "E",
        "6": "A", "7": "B", "8": "C", "9": "D", "10": "E"
    }
    
    # 2. Gerar PDF e Template com as posições matemáticas das bolhas
    _, template = generate_answer_sheet_pdf(
        exam_id="test-sim-001",
        title="Simulado de Verificação Automatizada",
        school_name="Colégio Teste OMR",
        num_questions=num_questions,
        num_alternatives=5
    )
    
    exam = {
        "id": "test-sim-001",
        "title": "Simulado Teste",
        "num_questions": num_questions,
        "num_alternatives": 5,
        "points_per_question": 1.0,
        "answer_key": answer_key,
        "weights": {},
        "sheet_template": template
    }
    
    # 3. Criar imagem canônica em branco (papel branco 255)
    canonical_sheet = np.ones((CANONICAL_HEIGHT, CANONICAL_WIDTH, 3), dtype=np.uint8) * 255
    
    # Desenhar os 4 marcadores ArUco exatamente nas posições dos cantos
    marker_centers = template["marker_centers"]
    marker_size = 120
    half_m = marker_size // 2
    
    for marker_id in [0, 1, 2, 3]:
        cx, cy = marker_centers.get(marker_id) or marker_centers.get(str(marker_id))
        pil_marker = generate_aruco_marker_image(marker_id, size=marker_size)
        marker_arr = np.array(pil_marker)
        marker_bgr = cv2.cvtColor(marker_arr, cv2.COLOR_GRAY2BGR)
        
        y1, y2 = cy - half_m, cy + half_m
        x1, x2 = cx - half_m, cx + half_m
        canonical_sheet[y1:y2, x1:x2] = marker_bgr

    # 4. Simular marcações do aluno:
    # Questões 1 a 8: ACERTOS (A, B, C, D, E, A, B, C)
    # Questão 9: ERRO (aluno marcou A ao invés de D)
    # Questão 10: EM BRANCO (nenhuma bolha preenchida)
    student_simulated_answers = {
        "1": "A", "2": "B", "3": "C", "4": "D", "5": "E",
        "6": "A", "7": "B", "8": "C", "9": "A"
        # "10" é deixada em branco
    }
    
    # Desenha os círculos das bolhas e preenche a resposta do aluno
    bubbles = template["bubbles"]
    for q_str, options in bubbles.items():
        marked_opt = student_simulated_answers.get(q_str, None)
        for opt_letter, coords in options.items():
            bx, by, br = coords["x"], coords["y"], coords["radius"]
            
            # Desenha borda da bolha
            cv2.circle(canonical_sheet, (bx, by), br, (160, 160, 160), 2)
            
            # Se for a opção marcada pelo aluno, preenche com caneta preta sólida
            if marked_opt == opt_letter:
                cv2.circle(canonical_sheet, (bx, by), br - 1, (20, 20, 20), -1)

    # 5. Aplicar distorção realista de câmera de smartphone:
    # - Redimensionar
    # - Rotação e inclinação de perspectiva (homografia simulada)
    # - Adicionar ruído de fundo
    h, w = canonical_sheet.shape[:2]
    
    # 4 pontos originais da folha
    pts1 = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    
    # 4 pontos distorcidos simulando foto tirada com o celular inclinado
    margin_rot = 150
    pts2 = np.float32([
        [margin_rot + 60, margin_rot + 40],        # TL
        [w - margin_rot - 40, margin_rot + 80],    # TR
        [w - margin_rot + 30, h - margin_rot - 50],# BR
        [margin_rot - 50, h - margin_rot + 20]     # BL
    ])
    
    warp_mat = cv2.getPerspectiveTransform(pts1, pts2)
    # Imagem simulada com fundo escuro de mesa (madeira/mesa cinza)
    simulated_photo = np.ones((h, w, 3), dtype=np.uint8) * 80 # Fundo escuro da mesa
    cv2.warpPerspective(canonical_sheet, warp_mat, (w, h), dst=simulated_photo, borderMode=cv2.BORDER_TRANSPARENT)
    
    # Codificar para JPEG como se viesse da câmera HTTP
    _, encoded_jpg = cv2.imencode(".jpg", simulated_photo, [cv2.IMWRITE_JPEG_QUALITY, 90])
    image_bytes = encoded_jpg.tobytes()
    
    # 6. Executar o Motor OMR na foto distorcida
    storage_temp = os.path.join(BACKEND_DIR, "storage")
    result = grade_submission(
        image_bytes=image_bytes,
        exam=exam,
        student_name="Aluno de Teste Automatizado",
        storage_dir=storage_temp
    )
    
    print(f"Resultado Obtido: Nota {result['score']} de {result['max_score']} ({result['percentage']}%)")
    print(f"Acertos: {result['correct_count']} | Erros: {result['wrong_count']} | Em Branco: {result['blank_count']}")
    
    # 7. Asserções
    assert result["score"] == 8.0, f"Esperado nota 8.0, obtido {result['score']}"
    assert result["correct_count"] == 8, f"Esperado 8 acertos, obtido {result['correct_count']}"
    assert result["wrong_count"] == 1, f"Esperado 1 erro na questão 9, obtido {result['wrong_count']}"
    assert result["blank_count"] == 1, f"Esperado 1 em branco na questão 10, obtido {result['blank_count']}"
    assert result["detected_answers"]["9"] == "A", f"Questão 9 deveria ter sido detectada como 'A', foi {result['detected_answers']['9']}"
    assert result["detected_answers"]["10"] == "BLANK", f"Questão 10 deveria ter sido detectada como 'BLANK', foi {result['detected_answers']['10']}"
    
    print("\n[SUCESSO] TESTE SINTETICO OMR 10 QUESTÕES PASSOU COM 100% DE EXATIDAO!")
    print(f"Overlay gerado em: {result['overlay_image_url']}")

def test_omr_20_questions_with_double_and_offset():
    print("\n=== INICIANDO TESTE END-TO-END DE 20 QUESTÕES (2 COLUNAS, DUPLA MARCAÇÃO E OFFSET) ===")
    
    num_questions = 20
    answer_key = {str(i): ("A" if i % 2 == 1 else "B") for i in range(1, num_questions + 1)}
    
    _, template = generate_answer_sheet_pdf(
        exam_id="test-sim-020",
        title="Simulado Prova Canoa 20 Questões",
        school_name="Escola Municipal Modelo",
        num_questions=num_questions,
        num_alternatives=4
    )
    
    # Check that bubble radius is enlarged
    sample_bubble = template["bubbles"]["1"]["A"]
    print(f"Raio canônico da bolha gerada: {sample_bubble['radius']}px (anteriormente era ~13px)")
    assert sample_bubble["radius"] >= 18, f"Esperado raio >= 18px, obtido {sample_bubble['radius']}"
    
    exam = {
        "id": "test-sim-020",
        "title": "Simulado 20 Questões",
        "num_questions": num_questions,
        "num_alternatives": 4,
        "points_per_question": 1.0,
        "answer_key": answer_key,
        "weights": {},
        "sheet_template": template
    }
    
    canonical_sheet = np.ones((CANONICAL_HEIGHT, CANONICAL_WIDTH, 3), dtype=np.uint8) * 255
    marker_centers = template["marker_centers"]
    marker_size = 120
    half_m = marker_size // 2
    
    for marker_id in [0, 1, 2, 3]:
        cx, cy = marker_centers.get(marker_id) or marker_centers.get(str(marker_id))
        pil_marker = generate_aruco_marker_image(marker_id, size=marker_size)
        marker_arr = np.array(pil_marker)
        marker_bgr = cv2.cvtColor(marker_arr, cv2.COLOR_GRAY2BGR)
        canonical_sheet[cy - half_m:cy + half_m, cx - half_m:cx + half_m] = marker_bgr

    bubbles = template["bubbles"]
    for q_str, options in bubbles.items():
        q_num = int(q_str)
        # Questões 1 a 17: Respostas Corretas
        if q_num <= 17:
            target_opt = answer_key[q_str]
            coords = options[target_opt]
            bx, by, br = coords["x"], coords["y"], coords["radius"]
            cv2.circle(canonical_sheet, (bx, by), br, (160, 160, 160), 2)
            cv2.circle(canonical_sheet, (bx, by), br - 2, (15, 15, 15), -1)
        # Questão 18: Dupla Marcação ('A' e 'C')
        elif q_num == 18:
            for opt_letter in ["A", "C"]:
                coords = options[opt_letter]
                bx, by, br = coords["x"], coords["y"], coords["radius"]
                cv2.circle(canonical_sheet, (bx, by), br, (160, 160, 160), 2)
                cv2.circle(canonical_sheet, (bx, by), br - 2, (20, 20, 20), -1)
        # Questão 19: Marcação Correta com Deslocamento/Offset de +3px
        elif q_num == 19:
            target_opt = answer_key[q_str]
            coords = options[target_opt]
            bx, by, br = coords["x"], coords["y"], coords["radius"]
            cv2.circle(canonical_sheet, (bx, by), br, (160, 160, 160), 2)
            # Offset de +3 pixels em x e -3 em y
            cv2.circle(canonical_sheet, (bx + 3, by - 3), br - 2, (25, 25, 25), -1)
        # Questão 20: Em branco (não desenha preenchimento)

    # Simular distorção de foto inclinada de smartphone
    h, w = canonical_sheet.shape[:2]
    pts1 = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    margin_rot = 140
    pts2 = np.float32([
        [margin_rot + 50, margin_rot + 30],
        [w - margin_rot - 30, margin_rot + 70],
        [w - margin_rot + 20, h - margin_rot - 40],
        [margin_rot - 40, h - margin_rot + 15]
    ])
    warp_mat = cv2.getPerspectiveTransform(pts1, pts2)
    simulated_photo = np.ones((h, w, 3), dtype=np.uint8) * 85
    cv2.warpPerspective(canonical_sheet, warp_mat, (w, h), dst=simulated_photo, borderMode=cv2.BORDER_TRANSPARENT)
    
    _, encoded_jpg = cv2.imencode(".jpg", simulated_photo, [cv2.IMWRITE_JPEG_QUALITY, 90])
    image_bytes = encoded_jpg.tobytes()
    
    storage_temp = os.path.join(BACKEND_DIR, "storage")
    result = grade_submission(
        image_bytes=image_bytes,
        exam=exam,
        student_name="Estudante Prova 20Q",
        storage_dir=storage_temp
    )
    
    print(f"Resultado 20Q: Nota {result['score']}/{result['max_score']} ({result['percentage']}%)")
    print(f"Acertos: {result['correct_count']} | Duplas: {result['double_count']} | Em Branco: {result['blank_count']}")
    
    assert result["correct_count"] == 18, f"Esperado 18 acertos (incluindo offset da Q19), obtido {result['correct_count']}"
    assert result["double_count"] == 1, f"Esperado 1 dupla na questão 18, obtido {result['double_count']}"
    assert result["blank_count"] == 1, f"Esperado 1 em branco na questão 20, obtido {result['blank_count']}"
    assert result["detected_answers"]["18"] == "DOUBLE", f"Q18 esperada como DOUBLE, obtido {result['detected_answers']['18']}"
    assert result["detected_answers"]["19"] == answer_key["19"], f"Q19 com offset esperada como {answer_key['19']}, obtido {result['detected_answers']['19']}"
    assert result["detected_answers"]["20"] == "BLANK", f"Q20 esperada como BLANK, obtido {result['detected_answers']['20']}"
    
    print("\n[SUCESSO] TESTE SINTETICO 20 QUESTÕES PASSOU COM 100% DE EXATIDÃO!")

if __name__ == "__main__":
    test_omr_end_to_end_synthetic()
    test_omr_20_questions_with_double_and_offset()
