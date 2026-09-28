import requests
import io
import pypdf

BASE_URL = "http://127.0.0.1:8080"

def test_dual_exam_batch():
    # Authenticate as admin
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "semed2026"})
    headers = {}
    if login_res.status_code == 200:
        token = login_res.json().get("token")
        if token:
            headers = {"X-Auth-Token": token}

    # 1. Create a test school
    s_res = requests.post(f"{BASE_URL}/api/schools", json={"name": "Escola Dual PDF Teste"}, headers=headers)
    assert s_res.status_code == 200
    school_id = s_res.json()["id"]

    # 2. Import 3 students into a classroom
    csv_text = (
        "Turma;Ano Escolar;Estudante;Matricula\n"
        "Turma Dual;3º ANO;CARLOS EDUARDO;MAT001\n"
        "Turma Dual;3º ANO;BEATRIZ SANTOS;MAT002\n"
        "Turma Dual;3º ANO;DANIEL OLIVEIRA;MAT003\n"
    )
    files = {"file": ("turma_dual.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
    imp_res = requests.post(f"{BASE_URL}/api/students/import-csv", files=files, data={"school_id": school_id}, headers=headers)
    assert imp_res.status_code == 200

    # Retrieve classroom ID
    tree_res = requests.get(f"{BASE_URL}/api/schools", headers=headers)
    target_school = next(s for s in tree_res.json() if s["id"] == school_id)
    target_class = target_school["classrooms"][0]
    class_id = target_class["id"]

    # 3. Create 2 distinct exams (Portuguese and Math)
    e1_res = requests.post(f"{BASE_URL}/api/exams", json={
        "title": "SIMULADO LINGUA PORTUGUESA", "num_questions": 10, "num_alternatives": 4
    }, headers=headers)
    e2_res = requests.post(f"{BASE_URL}/api/exams", json={
        "title": "SIMULADO MATEMATICA", "num_questions": 10, "num_alternatives": 4
    }, headers=headers)
    assert e1_res.status_code == 201 and e2_res.status_code == 201
    exam1_id = e1_res.json()["id"]
    exam2_id = e2_res.json()["id"]

    # 4. Link both exams to the classroom
    link_res = requests.post(f"{BASE_URL}/api/classrooms/{class_id}/exams", json={
        "exam_ids": [exam1_id, exam2_id]
    }, headers=headers)
    assert link_res.status_code == 200

    # 5. Request batch PDF with exam_id='both' and layout='double' (2 por folha)
    pdf_res = requests.get(f"{BASE_URL}/api/classrooms/{class_id}/exams/both/batch-pdf?layout=double", headers=headers)
    assert pdf_res.status_code == 200, f"Batch PDF failed: {pdf_res.status_code} - {pdf_res.text}"
    assert pdf_res.headers.get("content-type") == "application/pdf"

    pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_res.content))
    # Page 1 is the official Attendance Roster (Ata de Presença) + 3 student answer sheet pages = 4 pages total
    print(f"Total pages generated: {len(pdf_reader.pages)}")
    assert len(pdf_reader.pages) == 4, f"Expected 4 pages (1 attendance roster + 3 student sheets), got {len(pdf_reader.pages)}"

    # Verify Page 1 has the attendance roster
    page1_text = pdf_reader.pages[0].extract_text()
    assert "ATA DE PRESENÇA" in page1_text or "ASSINATURA" in page1_text or "Escola Dual PDF Teste" in page1_text

    # Verify student pages (pages 2 to 4) have both exam titles and student names
    # Students are ordered alphabetically: BEATRIZ SANTOS, CARLOS EDUARDO, DANIEL OLIVEIRA
    students_expected = ["BEATRIZ SANTOS", "CARLOS EDUARDO", "DANIEL OLIVEIRA"]
    for idx, page in enumerate(pdf_reader.pages[1:]):
        text = page.extract_text()
        print(f"\n--- Page {idx + 2} Content Sample ---")
        assert "SIMULADO LINGUA PORTUGUESA" in text, f"Exam 1 title missing on page {idx + 2}"
        assert "SIMULADO MATEMATICA" in text, f"Exam 2 title missing on page {idx + 2}"
        assert students_expected[idx] in text, f"Student {students_expected[idx]} missing on page {idx + 2}"
        print(f"Page {idx + 2} successfully verified: Contains {students_expected[idx]} with BOTH exams (Top + Bottom)!")

    print("\nSUCCESS: Dual-exam per sheet with attendance roster verified perfectly!")

if __name__ == "__main__":
    test_dual_exam_batch()
