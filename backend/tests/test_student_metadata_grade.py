import unittest
import os
import sys
import uuid
import numpy as np
import cv2
import fitz  # PyMuPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.database import (
    init_db,
    get_or_create_school,
    get_or_create_classroom,
    get_or_create_student,
    save_exam,
    get_student_by_id
)
from app.services.pdf_generator import generate_batch_classroom_pdf
from app.services.omr_engine import grade_submission

class TestStudentMetadataGrade(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_end_to_end_student_qr_reading(self):
        # 1. Create School, Classroom, Student
        school = get_or_create_school("Escola Municipal Professor Darcy")
        cl = get_or_create_classroom(school["id"], "9º Ano Matutino", "Manhã")
        student = get_or_create_student(cl["id"], "Douglas Cavalcante Silva", "REG-8821")

        # 2. Create Exam
        exam_id = str(uuid.uuid4())
        exam = save_exam({
            "id": exam_id,
            "title": "Simulado Prova Brasil 2026",
            "subtitle": "Avaliação de Rendimento",
            "num_questions": 10,
            "num_alternatives": 4,
            "points_per_question": 1.0,
            "answer_key": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "A", "6": "B", "7": "C", "8": "D", "9": "A", "10": "B"},
            "weights": {},
            "school_name": "Escola Municipal Professor Darcy",
            "classroom": "9º Ano Matutino"
        })

        # 3. Generate Answer Sheet PDF for this student
        pdf_bytes = generate_batch_classroom_pdf(
            exam=exam,
            classroom={"id": cl["id"], "name": cl["name"], "school_name": school["name"]},
            students=[student],
            sheets_per_page=1
        )

        # 4. Convert 1st page of PDF to image with PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[1] if len(doc) > 1 else doc[0]
        pix = page.get_pixmap(dpi=150)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
        if pix.n == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        else:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # 5. Process sheet through grade_submission
        _, jpg_buf = cv2.imencode(".jpg", img_bgr)
        result = grade_submission(jpg_buf.tobytes(), exam)

        print("\n--- OMR RESULT METADATA ---")
        print("Student Name:", result.get("student_name"))
        print("Exam Title:", result.get("exam_title"))
        print("School Name:", result.get("school_name"))
        print("Classroom Name:", result.get("classroom_name"))
        print("Registration:", result.get("registration"))
        print("Score:", result.get("score"), "/", result.get("max_score"))

        # 6. Verifications
        self.assertEqual(result.get("student_name"), "Douglas Cavalcante Silva")
        self.assertEqual(result.get("exam_title"), "Simulado Prova Brasil 2026")
        self.assertEqual(result.get("school_name"), "Escola Municipal Professor Darcy")
        self.assertEqual(result.get("classroom_name"), "9º Ano Matutino")
        self.assertEqual(result.get("registration"), "REG-8821")

    def test_exam_fallback_metadata_without_student_qr(self):
        from app.services.pdf_generator import generate_answer_sheet_pdf
        exam_id = str(uuid.uuid4())
        pdf_bytes, template = generate_answer_sheet_pdf(
            exam_id=exam_id,
            title="Simulado Geral Escola Base",
            school_name="Colégio Estadual Modelo",
            classroom="3º Ano Ensino Médio",
            num_questions=10,
            num_alternatives=4
        )
        exam = save_exam({
            "id": exam_id,
            "title": "Simulado Geral Escola Base",
            "school_name": "Colégio Estadual Modelo",
            "classroom": "3º Ano Ensino Médio",
            "student_name": "Aluno Padrão",
            "num_questions": 10,
            "num_alternatives": 4,
            "points_per_question": 1.0,
            "answer_key": {"1": "A"},
            "weights": {},
            "sheet_template": template
        })

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[1] if len(doc) > 1 else doc[0]
        pix = page.get_pixmap(dpi=150)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR)

        _, jpg_buf = cv2.imencode(".jpg", img_bgr)
        result = grade_submission(jpg_buf.tobytes(), exam)

        self.assertEqual(result.get("exam_title"), "Simulado Geral Escola Base")
        self.assertEqual(result.get("school_name"), "Colégio Estadual Modelo")
        self.assertEqual(result.get("classroom_name"), "3º Ano Ensino Médio")
        self.assertEqual(result.get("student_name"), "Aluno Padrão")

if __name__ == "__main__":
    unittest.main()
