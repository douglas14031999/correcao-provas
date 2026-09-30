import uuid
import json
from datetime import datetime
from app.services.database import (
    get_connection,
    get_or_create_school,
    get_or_create_classroom,
    get_or_create_student,
    save_exam,
    link_exams_to_classroom,
    save_submission
)

def populate_test_environment():
    print("=== INICIANDO CRIAÇÃO DO AMBIENTE DE TESTE ===")
    
    # 1. Escola de Teste
    school_name = "ESCOLA MUNICIPAL PROFESSOR TESTE - CANOA"
    inep_code = "12345678"
    school = get_or_create_school(school_name, inep_code)
    school_id = school["id"]
    print(f"1. Escola: {school['name']} (ID: {school_id})")

    # 2. Turma de Teste
    class_name = "5º ANO A - TURMA TESTE"
    grade_year = "5º ANO"
    shift = "MANHÃ"
    classroom = get_or_create_classroom(school_id, class_name, grade_year, shift)
    classroom_id = classroom["id"]
    print(f"2. Turma: {classroom['name']} (ID: {classroom_id})")

    # 3. 12 Alunos de Teste
    students_data = [
        ("ANA BEATRIZ SILVA SANTOS", "2026-001"),
        ("BRUNO HENRIQUE OLIVEIRA", "2026-002"),
        ("CAMILA FERREIRA COSTA", "2026-003"),
        ("DANIEL SOUZA RODRIGUES", "2026-004"),
        ("EDUARDO LIMA MARTINS", "2026-005"),
        ("FERNANDA ALVES BARBOSA", "2026-006"),
        ("GABRIEL MONTEIRO DIAS", "2026-007"),
        ("HELENA CARDOSO PEREIRA", "2026-008"),
        ("IGOR CAVALCANTE NUNES", "2026-009"),
        ("JULIA TEIXEIRA MEDEIROS", "2026-010"),
        ("LUCAS FARIAS RIBEIRO", "2026-011"),
        ("MARIANA NASCIMENTO SILVA", "2026-012")
    ]

    created_students = []
    for name, reg in students_data:
        st = get_or_create_student(classroom_id, name, reg)
        created_students.append(st)
    print(f"3. {len(created_students)} alunos cadastrados na turma.")

    # 4. Prova 1: PROVA CANOA - LÍNGUA PORTUGUESA - TESTE (20 Questões)
    title_lp = "PROVA CANOA - LÍNGUA PORTUGUESA - TESTE"
    key_lp = {}
    skills_lp = {}
    options = ["A", "B", "C", "D"]
    for q in range(1, 21):
        q_str = str(q)
        key_lp[q_str] = options[(q - 1) % 4]
        skills_lp[q_str] = f"EF05LP{q:02d}"

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM exams WHERE title = ?", (title_lp,))
    row_lp = c.fetchone()
    if row_lp:
        exam_lp_id = row_lp["id"]
        c.execute("""
            UPDATE exams 
            SET num_questions = 20, points_per_question = 0.5, skills_matrix = ?, answer_key = ? 
            WHERE id = ?
        """, (json.dumps(skills_lp), json.dumps(key_lp), exam_lp_id))
        conn.commit()
    else:
        created_lp = save_exam({
            "title": title_lp,
            "subtitle": "5º ANO DO ENSINO FUNDAMENTAL",
            "school_name": school_name,
            "classroom": class_name,
            "num_questions": 20,
            "num_alternatives": 4,
            "points_per_question": 0.5,
            "answer_key": key_lp,
            "weights": {str(q): 1.0 for q in range(1, 21)},
            "header_color": "#2563eb",
            "cover_model": "opcao_4_azul_nautico_lagoa",
            "cover_title": "PROVA CANOA",
            "cover_subtitle": "AVALIAÇÃO DIAGNÓSTICA DE LÍNGUA PORTUGUESA"
        })
        exam_lp_id = created_lp["id"]
        c.execute("UPDATE exams SET skills_matrix = ? WHERE id = ?", (json.dumps(skills_lp), exam_lp_id))
        conn.commit()

    print(f"4. Prova Língua Portuguesa: {title_lp} (20Q, ID: {exam_lp_id})")

    # 5. Prova 2: PROVA CANOA - MATEMÁTICA - TESTE (20 Questões)
    title_mat = "PROVA CANOA - MATEMÁTICA - TESTE"
    key_mat = {}
    skills_mat = {}
    for q in range(1, 21):
        q_str = str(q)
        key_mat[q_str] = options[(q + 1) % 4]
        skills_mat[q_str] = f"EF05MA{q:02d}"

    c.execute("SELECT id FROM exams WHERE title = ?", (title_mat,))
    row_mat = c.fetchone()
    if row_mat:
        exam_mat_id = row_mat["id"]
        c.execute("""
            UPDATE exams 
            SET num_questions = 20, points_per_question = 0.5, skills_matrix = ?, answer_key = ? 
            WHERE id = ?
        """, (json.dumps(skills_mat), json.dumps(key_mat), exam_mat_id))
        conn.commit()
    else:
        created_mat = save_exam({
            "title": title_mat,
            "subtitle": "5º ANO DO ENSINO FUNDAMENTAL",
            "school_name": school_name,
            "classroom": class_name,
            "num_questions": 20,
            "num_alternatives": 4,
            "points_per_question": 0.5,
            "answer_key": key_mat,
            "weights": {str(q): 1.0 for q in range(1, 21)},
            "header_color": "#10b981",
            "cover_model": "opcao_2_verde_esmeralda_lagoa",
            "cover_title": "PROVA CANOA",
            "cover_subtitle": "AVALIAÇÃO DIAGNÓSTICA DE MATEMÁTICA"
        })
        exam_mat_id = created_mat["id"]
        c.execute("UPDATE exams SET skills_matrix = ? WHERE id = ?", (json.dumps(skills_mat), exam_mat_id))
        conn.commit()

    conn.close()
    print(f"5. Prova Matemática: {title_mat} (20Q, ID: {exam_mat_id})")

    # 6. Vincular ambos os gabaritos à turma
    link_exams_to_classroom(classroom_id, [exam_lp_id, exam_mat_id])
    print("6. Ambos os simulados vinculados à turma com sucesso.")

    # 7. Limpar submissions antigas
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM submissions WHERE exam_id IN (?, ?) AND classroom_id = ?", (exam_lp_id, exam_mat_id, classroom_id))
    conn.commit()
    conn.close()

    # 8. Definir perfil pedagógico das questões para abranger TODAS as 4 faixas de cores do SALVEAL:
    # Faixa 1 (Acima de 80% - Teal): 10 ou 11 alunos acertam
    # Faixa 2 (De 61 a 80% - Ciano): 8 ou 9 alunos acertam
    # Faixa 3 (De 41 a 60% - Laranja): 5 a 7 alunos acertam
    # Faixa 4 (Até 40% - Vermelho): 2 a 4 alunos acertam

    # Para Língua Portuguesa:
    # Q1..Q6: Acima de 80% (10 ou 11 alunos)
    # Q7..Q11: 61% a 80% (8 ou 9 alunos)
    # Q12..Q16: 41% a 60% (6 alunos)
    # Q17..Q20: Até 40% (3 ou 4 alunos)
    question_correct_students_lp = {
        1: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],     # 11/12 (91.7%) -> Teal
        2: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], # 12/12 (100%) -> Teal
        3: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11],     # 11/12 (91.7%) -> Teal
        4: [0, 1, 2, 3, 4, 5, 6, 7, 8, 10],         # 10/12 (83.3%) -> Teal
        5: [0, 1, 2, 3, 4, 5, 6, 7, 9, 10],         # 10/12 (83.3%) -> Teal
        6: [0, 1, 2, 3, 4, 5, 6, 7, 8, 10],         # 10/12 (83.3%) -> Teal
        7: [0, 1, 2, 3, 4, 5, 6, 7, 8],             # 9/12  (75.0%) -> Ciano
        8: [0, 1, 2, 3, 4, 5, 6, 7, 9],             # 9/12  (75.0%) -> Ciano
        9: [0, 1, 2, 3, 4, 5, 6, 7],                # 8/12  (66.7%) -> Ciano
        10: [0, 1, 2, 3, 4, 5, 6, 8],               # 8/12  (66.7%) -> Ciano
        11: [0, 1, 2, 3, 4, 5, 7, 8],               # 8/12  (66.7%) -> Ciano
        12: [0, 1, 2, 3, 4, 5, 6],                  # 7/12  (58.3%) -> Laranja
        13: [0, 1, 2, 3, 4, 5],                     # 6/12  (50.0%) -> Laranja
        14: [0, 1, 2, 3, 4, 6],                     # 6/12  (50.0%) -> Laranja
        15: [0, 1, 2, 3, 5, 7],                     # 6/12  (50.0%) -> Laranja
        16: [0, 1, 2, 4, 6, 8],                     # 6/12  (50.0%) -> Laranja
        17: [0, 1, 2, 3],                           # 4/12  (33.3%) -> Vermelho
        18: [0, 1, 2, 4],                           # 4/12  (33.3%) -> Vermelho
        19: [0, 1, 3],                              # 3/12  (25.0%) -> Vermelho
        20: [0, 2, 4]                               # 3/12  (25.0%) -> Vermelho
    }

    # Para Matemática: Perfil variado para permitir comparações ricas
    # Q1..Q5: Acima de 80% (10 a 12 alunos)
    # Q6..Q10: 61% a 80% (8 ou 9 alunos)
    # Q11..Q15: 41% a 60% (5 a 7 alunos)
    # Q16..Q20: Até 40% (2 a 4 alunos)
    question_correct_students_mat = {
        1: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], # 12/12 (100%) -> Teal
        2: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],     # 11/12 (91.7%) -> Teal
        3: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],         # 10/12 (83.3%) -> Teal
        4: [0, 1, 2, 3, 4, 5, 6, 7, 8, 11],        # 10/12 (83.3%) -> Teal
        5: [0, 1, 2, 3, 4, 5, 6, 7, 10],            # 9/12  (75.0%) -> Ciano
        6: [0, 1, 2, 3, 4, 5, 6, 8, 9],             # 9/12  (75.0%) -> Ciano
        7: [0, 1, 2, 3, 4, 5, 6, 7],                # 8/12  (66.7%) -> Ciano
        8: [0, 1, 2, 3, 4, 5, 7, 8],                # 8/12  (66.7%) -> Ciano
        9: [0, 1, 2, 3, 4, 5, 6, 8],                # 8/12  (66.7%) -> Ciano
        10: [0, 1, 2, 3, 4, 5, 7],                  # 7/12  (58.3%) -> Laranja
        11: [0, 1, 2, 3, 4, 6],                     # 6/12  (50.0%) -> Laranja
        12: [0, 1, 2, 3, 5, 7],                     # 6/12  (50.0%) -> Laranja
        13: [0, 1, 2, 4, 6, 8],                     # 6/12  (50.0%) -> Laranja
        14: [0, 1, 2, 3, 5],                        # 5/12  (41.7%) -> Laranja
        15: [0, 1, 2, 4, 6],                        # 5/12  (41.7%) -> Laranja
        16: [0, 1, 2, 3],                           # 4/12  (33.3%) -> Vermelho
        17: [0, 1, 2],                              # 3/12  (25.0%) -> Vermelho
        18: [0, 1, 3],                              # 3/12  (25.0%) -> Vermelho
        19: [0, 2],                                 # 2/12  (16.7%) -> Vermelho
        20: [0, 1]                                  # 2/12  (16.7%) -> Vermelho
    }

    def generate_exam_submissions(exam_id, exam_key, question_map):
        points_per_q = 0.5
        max_score = 10.0

        for st_idx, student in enumerate(created_students):
            detected_answers = {}
            results_detail = []
            correct_count = 0

            for q in range(1, 21):
                q_str = str(q)
                corr_ans = exam_key[q_str]
                st_list = question_map.get(q, [])

                if st_idx in st_list:
                    chosen = corr_ans
                    is_corr = True
                    score_q = points_per_q
                    correct_count += 1
                else:
                    wrong_choices = [opt for opt in options if opt != corr_ans]
                    chosen = wrong_choices[(q + st_idx) % len(wrong_choices)]
                    is_corr = False
                    score_q = 0.0

                detected_answers[q_str] = chosen
                results_detail.append({
                    "question": q,
                    "chosen": chosen,
                    "correct": corr_ans,
                    "is_correct": is_corr,
                    "is_blank": False,
                    "is_double": False,
                    "score": score_q
                })

            total_score = round(correct_count * points_per_q, 1)
            pct = round((total_score / max_score) * 100, 1)

            sub_data = {
                "id": str(uuid.uuid4()),
                "exam_id": exam_id,
                "student_name": student["name"],
                "student_id": student["id"],
                "classroom_id": classroom_id,
                "school_id": school_id,
                "score": total_score,
                "max_score": max_score,
                "detected_answers": detected_answers,
                "results_detail": results_detail,
                "scanned_image_url": "",
                "overlay_image_url": ""
            }
            save_submission(sub_data)
            print(f" - Aluno {student['name']:<28} | Acertos: {correct_count:>2}/20 | Nota: {total_score:>4.1f} ({pct:>5.1f}%)")

    print("\n--- Gerando Respostas para Língua Portuguesa ---")
    generate_exam_submissions(exam_lp_id, key_lp, question_correct_students_lp)

    print("\n--- Gerando Respostas para Matemática ---")
    generate_exam_submissions(exam_mat_id, key_mat, question_correct_students_mat)

    print("\n=== POPULAÇÃO DE DADOS DE TESTE CONCLUÍDA COM SUCESSO! ===")
    print(f"Escola: {school_name} (ID: {school_id})")
    print(f"Turma:  {class_name} (ID: {classroom_id})")
    print(f"Prova 1: {title_lp} (ID: {exam_lp_id})")
    print(f"Prova 2: {title_mat} (ID: {exam_mat_id})")

if __name__ == "__main__":
    populate_test_environment()
