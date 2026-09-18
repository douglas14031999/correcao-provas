import requests
import io
import pypdf

BASE_URL = "http://127.0.0.1:8080"

def test_dual_exam_batch():
    # 1. Create a test school
    s_res = requests.post(f"{BASE_URL}/api/schools", json={"name": "Escola Dual PDF Teste"})
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
    imp_res = requests.post(f"{BASE_URL}/api/students/import-csv", files=files, data={"school_id": school_id})
    assert imp_res.status_code == 200

    # Retrieve classroom ID
    tree_res = requests.get(f"{BASE_URL}/api/schools")
    target_school = next(s for s in tree_res.json() if s["id"] == school_id)
    target_class = target_school["classrooms"][0]
    class_id = target_class["id"]

    # 3. Create 2 distinct exams (Portuguese and Math)
    e1_res = requests.post(f"{BASE_URL}/api/exams", json={
        "title": "SIMULADO LINGUA PORTUGUESA", "num_questions": 10, "num_alternatives": 4
    })
    e2_res = requests.post(f"{BASE_URL}/api/exams", json={
        "title": "SIMULADO MATEMATICA", "num_questions": 10, "num_alternatives": 4
    })
    assert e1_res.status_code == 201 and e2_res.status_code == 201
    exam1_id = e1_res.json()["id"]
    exam2_id = e2_res.json()["id"]

    # 4. Link both exams to the classroom
    link_res = requests.post(f"{BASE_URL}/api/classrooms/{class_id}/exams", json={
        "exam_ids": [exam1_id, exam2_id]
    })
    assert link_res.status_code == 200

    # 5. Request batch PDF with exam_id='both' and layout='double' (2 por folha)
    pdf_res = requests.get(f"{BASE_URL}/api/classrooms/{class_id}/exams/both/batch-pdf?layout=double")
    assert pdf_res.status_code == 200, f"Batch PDF failed: {pdf_res.status_code} - {pdf_res.text}"
    assert pdf_res.headers.get("content-type") == "application/pdf"

    pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_res.content))
    # Exactly 3 students -> exactly 3 pages (one sheet per student, containing BOTH exams!)
    print(f"Total pages generated: {len(pdf_reader.pages)}")
    assert len(pdf_reader.pages) == 3, f"Expected 3 pages (1 per student with 2 exams), got {len(pdf_reader.pages)}"

    # Verify each page has both exam titles and the student name
    # Students are ordered alphabetically by name: BEATRIZ SANTOS, CARLOS EDUARDO, DANIEL OLIVEIRA
    students_expected = ["BEATRIZ SANTOS", "CARLOS EDUARDO", "DANIEL OLIVEIRA"]
    for idx, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        print(f"\n--- Page {idx + 1} Content Sample ---")
        assert "SIMULADO LINGUA PORTUGUESA" in text, f"Exam 1 title missing on page {idx + 1}"
        assert "SIMULADO MATEMATICA" in text, f"Exam 2 title missing on page {idx + 1}"
        assert students_expected[idx] in text, f"Student {students_expected[idx]} missing on page {idx + 1}"
        print(f"Page {idx + 1} successfully verified: Contains {students_expected[idx]} with BOTH exams (Top + Bottom)!")

    print("\nSUCCESS: Dual-exam per sheet for each student verified perfectly!")

if __name__ == "__main__":
    test_dual_exam_batch()
