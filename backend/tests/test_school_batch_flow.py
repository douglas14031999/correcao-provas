import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.database import (
    init_db,
    get_or_create_school,
    get_or_create_classroom,
    get_or_create_student,
    list_schools_tree,
    get_classroom_with_details,
    get_classroom_report,
    save_exam,
    save_submission
)
import uuid
from app.services.pdf_generator import generate_batch_classroom_pdf
from app.services.omr_engine import read_qr_metadata

class TestSchoolBatchFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_hierarchy_creation(self):
        school = get_or_create_school("Escola Teste OMR")
        self.assertIsNotNone(school["id"])
        
        classroom = get_or_create_classroom(school["id"], "9º Ano B", "Manhã")
        self.assertIsNotNone(classroom["id"])
        
        s1 = get_or_create_student(classroom["id"], "Lucas Gabriel", "MAT-001")
        s2 = get_or_create_student(classroom["id"], "Mariana Lima", "MAT-002")
        self.assertIsNotNone(s1["id"])
        self.assertIsNotNone(s2["id"])
        
        details = get_classroom_with_details(classroom["id"])
        self.assertEqual(len(details["students"]), 2)
        self.assertEqual(details["school_name"], "Escola Teste OMR")

    def test_02_batch_pdf_generation(self):
        # Create an exam
        exam_data = {
            "id": str(uuid.uuid4()),
            "title": "Simulado Geral 2026",
            "subtitle": "Avaliação Diagnóstica",
            "school_name": "Escola Modelo",
            "classroom": "9º Ano B",
            "student_name": "",
            "shift": "Manhã",
            "num_questions": 10,
            "num_alternatives": 4,
            "points_per_question": 1.0,
            "answer_key": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "A", "6": "B", "7": "C", "8": "D", "9": "A", "10": "B"},
            "weights": {},
            "sheet_template": {}
        }
        exam = save_exam(exam_data)
        
        school = get_or_create_school("Escola Teste OMR")
        classroom = get_or_create_classroom(school["id"], "9º Ano B", "Manhã")
        details = get_classroom_with_details(classroom["id"])
        
        # Test batch PDF generation with 2 per page
        pdf_bytes_double = generate_batch_classroom_pdf(
            exam=exam,
            classroom=details,
            students=details["students"],
            sheets_per_page=2
        )
        self.assertTrue(len(pdf_bytes_double) > 5000)
        self.assertTrue(pdf_bytes_double.startswith(b"%PDF"))

        # Test batch PDF generation with 1 per page
        pdf_bytes_single = generate_batch_classroom_pdf(
            exam=exam,
            classroom=details,
            students=details["students"],
            sheets_per_page=1
        )
        self.assertTrue(len(pdf_bytes_single) > 5000)
        self.assertTrue(pdf_bytes_single.startswith(b"%PDF"))

    def test_03_classroom_report(self):
        school = get_or_create_school("Escola Teste OMR")
        classroom = get_or_create_classroom(school["id"], "9º Ano B", "Manhã")
        details = get_classroom_with_details(classroom["id"])
        students = details["students"]
        
        # Simulate submissions
        exam_data = {
            "id": str(uuid.uuid4()),
            "title": "Simulado Bimestral",
            "subtitle": "Matemática",
            "num_questions": 5,
            "num_alternatives": 4,
            "points_per_question": 2.0,
            "answer_key": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "A"},
            "weights": {}
        }
        exam = save_exam(exam_data)
        
        save_submission({
            "id": str(uuid.uuid4()),
            "exam_id": exam["id"],
            "student_id": students[0]["id"],
            "student_name": students[0]["name"],
            "classroom_id": classroom["id"],
            "school_id": school["id"],
            "score": 8.0,
            "max_score": 10.0,
            "correct_count": 4,
            "wrong_count": 1,
            "blank_count": 0,
            "double_count": 0,
            "detected_answers": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "B"},
            "results_detail": []
        })
        
        report = get_classroom_report(classroom["id"], exam["id"])
        self.assertIsNotNone(report)
        self.assertEqual(report["total_students"], len(students))
        self.assertEqual(report["corrected_count"], 1)
        self.assertAlmostEqual(report["class_average"], 8.0)

    def test_04_csv_import_simulation(self):
        import io
        import csv
        from app.api.schools import import_students_csv
        from fastapi import UploadFile

        csv_bytes = (
            "Escola;Turma;Turno;Matrícula;Aluno\n"
            "Escola Teste CSV;3º Ano C;Manhã;9981;Pedro Henrique\n"
            "Escola Teste CSV;3º Ano C;Manhã;9982;Camila Barbosa\n"
        ).encode("utf-8-sig")

        upload_file = UploadFile(
            filename="alunos.csv",
            file=io.BytesIO(csv_bytes)
        )
        import asyncio
        from datetime import datetime, timedelta
        from app.services.database import update_system_settings
        update_system_settings({
            "admin_session_token": "test-token-batch",
            "admin_session_expires": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        })
        res = asyncio.run(import_students_csv(upload_file, authorization="Bearer test-token-batch"))
        self.assertTrue(res["success"])
        self.assertEqual(res["imported_students"], 2)

if __name__ == "__main__":
    unittest.main()
