import os
import sys
import numpy as np
import cv2

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TEST_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.pdf_generator import (
    generate_answer_sheet_pdf,
    generate_aruco_marker_image,
    CANONICAL_WIDTH,
    CANONICAL_HEIGHT,
    CANONICAL_HEIGHT_HALF
)
from app.services.omr_engine import grade_submission

def test_both_layouts():
    print("=================================================================")
    print("TESTE DE DETECÇÃO AUTOMÁTICA DE FORMATO: 2 POR FOLHA vs PÁGINA INTEIRA")
    print("=================================================================")

    num_questions = 20
    answer_key = {str(i): ("A" if i % 2 == 1 else "B") for i in range(1, num_questions + 1)}

    exam = {
        "id": "exam-test-dual-layout",
        "title": "Simulado Canoa - Teste de Layouts",
        "school_name": "Escola Municipal Teste",
        "num_questions": num_questions,
        "num_alternatives": 4,
        "points_per_question": 1.0,
        "answer_key": answer_key,
        "weights": {}
    }

    # -------------------------------------------------------------
    # PARTE 1: MODELO 2 POR FOLHA (MEIA PÁGINA A4)
    # -------------------------------------------------------------
    print("\n[1/2] Testando Modelo 2 POR FOLHA (Compacto / Meia Página)...")
    _, compact_tmpl = generate_answer_sheet_pdf(
        exam_id=exam["id"],
        title=exam["title"],
        school_name=exam["school_name"],
        num_questions=num_questions,
        num_alternatives=4,
        sheets_per_page=2
    )

    assert compact_tmpl["canonical_width"] == CANONICAL_WIDTH
    assert compact_tmpl["canonical_height"] == CANONICAL_HEIGHT_HALF, f"Esperado {CANONICAL_HEIGHT_HALF}, obtido {compact_tmpl['canonical_height']}"
    assert compact_tmpl["is_compact"] == True

    # Criar folha canônica compacta (1654x1169)
    sheet_half = np.ones((CANONICAL_HEIGHT_HALF, CANONICAL_WIDTH, 3), dtype=np.uint8) * 255
    m_centers = compact_tmpl["marker_centers"]
    marker_size = 110
    half_m = marker_size // 2

    for mid in [0, 1, 2, 3]:
        cx, cy = m_centers.get(mid) or m_centers.get(str(mid))
        pil_marker = generate_aruco_marker_image(mid, size=marker_size)
        m_arr = cv2.cvtColor(np.array(pil_marker), cv2.COLOR_GRAY2BGR)
        sheet_half[cy - half_m:cy + half_m, cx - half_m:cx + half_m] = m_arr

    # Preencher respostas
    for q_str, options in compact_tmpl["bubbles"].items():
        correct_opt = answer_key[q_str]
        coords = options[correct_opt]
        bx, by, br = coords["x"], coords["y"], coords["radius"]
        cv2.circle(sheet_half, (bx, by), br, (160, 160, 160), 2)
        cv2.circle(sheet_half, (bx, by), br - 1, (10, 10, 10), -1)

    # Simular foto de smartphone de meia folha
    h, w = sheet_half.shape[:2]
    pts1 = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    skew = 100
    pts2 = np.float32([
        [skew + 40, skew + 20],
        [w - skew - 20, skew + 50],
        [w - skew + 15, h - skew - 30],
        [skew - 30, h - skew + 10]
    ])
    warp_mat = cv2.getPerspectiveTransform(pts1, pts2)
    photo_half = np.ones((h, w, 3), dtype=np.uint8) * 90
    cv2.warpPerspective(sheet_half, warp_mat, (w, h), dst=photo_half, borderMode=cv2.BORDER_TRANSPARENT)

    _, jpg_data = cv2.imencode(".jpg", photo_half, [cv2.IMWRITE_JPEG_QUALITY, 90])

    storage_dir = os.path.join(BACKEND_DIR, "storage")
    result_compact = grade_submission(
        image_bytes=jpg_data.tobytes(),
        exam=exam,
        student_name="Aluno Meia Folha",
        storage_dir=storage_dir
    )

    print(f"  Layout Detectado: {result_compact['layout_detected']}")
    print(f"  Nota: {result_compact['score']}/{result_compact['max_score']} (Acertos: {result_compact['correct_count']}/20)")
    assert result_compact["is_compact"] == True, "Deveria ter detectado como modelo 2 por folha!"
    assert result_compact["layout_detected"] == "2_por_folha"
    assert result_compact["correct_count"] == 20, f"Esperado 20 acertos, obtido {result_compact['correct_count']}"

    # -------------------------------------------------------------
    # PARTE 2: MODELO PÁGINA INTEIRA (FOLHA A4 COMPLETA)
    # -------------------------------------------------------------
    print("\n[2/2] Testando Modelo PÁGINA INTEIRA (A4 Completa)...")
    _, single_tmpl = generate_answer_sheet_pdf(
        exam_id=exam["id"],
        title=exam["title"],
        school_name=exam["school_name"],
        num_questions=num_questions,
        num_alternatives=4,
        sheets_per_page=1
    )

    assert single_tmpl["canonical_width"] == CANONICAL_WIDTH
    assert single_tmpl["canonical_height"] == CANONICAL_HEIGHT
    assert single_tmpl["is_compact"] == False

    sheet_full = np.ones((CANONICAL_HEIGHT, CANONICAL_WIDTH, 3), dtype=np.uint8) * 255
    m_centers_full = single_tmpl["marker_centers"]

    for mid in [0, 1, 2, 3]:
        cx, cy = m_centers_full.get(mid) or m_centers_full.get(str(mid))
        pil_marker = generate_aruco_marker_image(mid, size=marker_size)
        m_arr = cv2.cvtColor(np.array(pil_marker), cv2.COLOR_GRAY2BGR)
        sheet_full[cy - half_m:cy + half_m, cx - half_m:cx + half_m] = m_arr

    for q_str, options in single_tmpl["bubbles"].items():
        correct_opt = answer_key[q_str]
        coords = options[correct_opt]
        bx, by, br = coords["x"], coords["y"], coords["radius"]
        cv2.circle(sheet_full, (bx, by), br, (160, 160, 160), 2)
        cv2.circle(sheet_full, (bx, by), br - 1, (10, 10, 10), -1)

    h_f, w_f = sheet_full.shape[:2]
    pts1_f = np.float32([[0, 0], [w_f, 0], [w_f, h_f], [0, h_f]])
    pts2_f = np.float32([
        [skew + 50, skew + 30],
        [w_f - skew - 30, skew + 60],
        [w_f - skew + 20, h_f - skew - 40],
        [skew - 40, h_f - skew + 15]
    ])
    warp_mat_f = cv2.getPerspectiveTransform(pts1_f, pts2_f)
    photo_full = np.ones((h_f, w_f, 3), dtype=np.uint8) * 90
    cv2.warpPerspective(sheet_full, warp_mat_f, (w_f, h_f), dst=photo_full, borderMode=cv2.BORDER_TRANSPARENT)

    _, jpg_data_f = cv2.imencode(".jpg", photo_full, [cv2.IMWRITE_JPEG_QUALITY, 90])

    result_full = grade_submission(
        image_bytes=jpg_data_f.tobytes(),
        exam=exam,
        student_name="Aluno Folha Inteira",
        storage_dir=storage_dir
    )

    print(f"  Layout Detectado: {result_full['layout_detected']}")
    print(f"  Nota: {result_full['score']}/{result_full['max_score']} (Acertos: {result_full['correct_count']}/20)")
    assert result_full["is_compact"] == False, "Deveria ter detectado como modelo página inteira!"
    assert result_full["layout_detected"] == "pagina_inteira"
    assert result_full["correct_count"] == 20, f"Esperado 20 acertos, obtido {result_full['correct_count']}"

    print("\n>>> SUCESSO TOTAL! AMBOS OS MODELOS (2 POR FOLHA E PÁGINA INTEIRA) FORAM IDENTIFICADOS COM 100% DE EXATIDÃO E SEM QUALQUER DEFORMAÇÃO! <<<")

if __name__ == "__main__":
    test_both_layouts()
