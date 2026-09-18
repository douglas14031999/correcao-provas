import requests
import json
import io

BASE_URL = "http://127.0.0.1:8080"

def run_tests():
    # 1. Health check
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    print("1. Health check OK")

    # 2. Create school manually
    school_payload = {"name": "Escola Teste Multiano", "inep_code": "999888"}
    s_res = requests.post(f"{BASE_URL}/api/schools", json=school_payload)
    assert s_res.status_code == 200, f"Create school failed: {s_res.status_code}"
    school = s_res.json()
    school_id = school["id"]
    print(f"2. School created: {school['name']} ({school_id})")

    # 3. Import CSV with same turma name 'turma 1 Aline' but DIFFERENT 'Ano Escolar' (1º ANO and 2º ANO)
    csv_text = (
        "Código da Turma;Turma;Ano Escolar;Estudante\n"
        "cod123;turma 1 Aline;1º ANO;ALUNO PRIMEIRO ANO A\n"
        "cod123;turma 1 Aline;1º ANO;ALUNO PRIMEIRO ANO B\n"
        "cod456;turma 1 Aline;2º ANO;ALUNO SEGUNDO ANO A\n"
        "cod456;turma 1 Aline;2º ANO;ALUNO SEGUNDO ANO B\n"
    )
    files = {"file": ("turmas_multiano.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
    data = {"school_id": school_id}
    imp_res = requests.post(f"{BASE_URL}/api/students/import-csv", files=files, data=data)
    assert imp_res.status_code == 200, f"Import CSV failed: {imp_res.status_code} - {imp_res.text}"
    imp_data = imp_res.json()
    print(f"3. CSV Imported: {imp_data['imported_students']} students across {imp_data['classrooms_count']} classrooms")
    assert imp_data["classrooms_count"] == 2, f"Expected 2 separate classrooms for multiano, got {imp_data['classrooms_count']}"

    # Verify both classrooms exist under this school
    tree_res = requests.get(f"{BASE_URL}/api/schools")
    assert tree_res.status_code == 200
    schools_tree = tree_res.json()
    target_school = next((s for s in schools_tree if s["id"] == school_id), None)
    assert target_school is not None
    classrooms = target_school["classrooms"]
    assert len(classrooms) == 2, f"Expected 2 classrooms in school tree, got {len(classrooms)}"
    grades = [c.get("grade_year") for c in classrooms]
    print(f"Classroom grades found: {grades}")
    assert "1º ANO" in grades
    assert "2º ANO" in grades
    print("4. Verification SUCCESS: Multiano classrooms separated properly by 'Ano Escolar'!")

    # 5. Test linking multiple exams to a classroom
    # Create two exams
    ex1_res = requests.post(f"{BASE_URL}/api/exams", json={
        "title": "PROVA 1 - PORTUGUES", "num_questions": 5, "num_alternatives": 4, "points_per_question": 2.0
    })
    ex2_res = requests.post(f"{BASE_URL}/api/exams", json={
        "title": "PROVA 2 - MATEMATICA", "num_questions": 5, "num_alternatives": 4, "points_per_question": 2.0
    })
    assert ex1_res.status_code == 201 and ex2_res.status_code == 201
    exam1_id = ex1_res.json()["id"]
    exam2_id = ex2_res.json()["id"]

    c1_id = classrooms[0]["id"]
    # Link both exams to classroom 1
    link_res = requests.post(f"{BASE_URL}/api/classrooms/{c1_id}/exams", json={
        "exam_ids": [exam1_id, exam2_id]
    })
    assert link_res.status_code == 200, f"Link exams failed: {link_res.status_code}"
    print("5. Linked 2 exams to classroom successfully")

    # Get linked exams
    get_links_res = requests.get(f"{BASE_URL}/api/classrooms/{c1_id}/exams")
    assert get_links_res.status_code == 200
    linked_exams = get_links_res.json()
    assert len(linked_exams) == 2, f"Expected 2 linked exams, got {len(linked_exams)}"
    linked_titles = [e["title"] for e in linked_exams]
    print(f"6. Retrieved linked exams: {linked_titles}")
    assert "PROVA 1 - PORTUGUES" in linked_titles
    assert "PROVA 2 - MATEMATICA" in linked_titles

    # 7. Test deleting one classroom
    c2_id = classrooms[1]["id"]
    del_c_res = requests.delete(f"{BASE_URL}/api/classrooms/{c2_id}")
    assert del_c_res.status_code == 200, f"Delete classroom failed: {del_c_res.status_code}"
    print(f"7. Deleted classroom {c2_id} successfully")

    # Verify classroom 1 still exists and classroom 2 is deleted
    c1_check = requests.get(f"{BASE_URL}/api/classrooms/{c1_id}")
    assert c1_check.status_code == 200, "Classroom 1 should still exist"
    c2_check = requests.get(f"{BASE_URL}/api/classrooms/{c2_id}")
    assert c2_check.status_code == 404, "Classroom 2 should be 404 deleted"
    print("8. Deletion verification SUCCESS: Classroom deleted with cascade properly!")

    # 8. Clean up test school
    requests.delete(f"{BASE_URL}/api/schools/{school_id}")
    requests.delete(f"{BASE_URL}/api/exams/{exam1_id}")
    requests.delete(f"{BASE_URL}/api/exams/{exam2_id}")
    print("9. Cleanup completed")

    print("ALL TESTS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    run_tests()
