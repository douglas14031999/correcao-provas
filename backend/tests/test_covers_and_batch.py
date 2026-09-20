import os
import sys
import unittest
import fitz

# Setup path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.services.database import init_db, save_exam, get_exam, update_exam, delete_exam
from app.services.cover_batch_generator import (
    render_single_cover_html,
    generate_classroom_covers_pdf,
    build_table_html,
    get_chrome_executable
)
from app.services.pdf_generator import get_cover_template

class TestCoverModelsAndBatch(unittest.TestCase):
    def setUp(self):
        init_db()
        self.mock_exam_id = "test-cov-exam-12345"
        self.mock_exam = {
            "id": self.mock_exam_id,
            "title": "SIMULADO MATEMÁTICA 2026",
            "subtitle": "4º ANO DO ENSINO FUNDAMENTAL",
            "school_name": "ESCOLA MUNICIPAL GOV LUIZ CAVALCANTE",
            "classroom": "4º ANO A",
            "shift": "MATUTINO",
            "num_questions": 22,
            "num_alternatives": 4,
            "answer_key": {str(i): "A" for i in range(1, 23)},
            "cover_model": "opcao_4_azul_nautico_lagoa",
            "cover_title": "PROVA CANOA 2026",
            "cover_subtitle": "CADERNO M0402 • MATEMÁTICA",
            "cover_instructions": "Preencha totalmente a bolha com caneta preta."
        }

    def tearDown(self):
        try:
            delete_exam(self.mock_exam_id)
        except Exception:
            pass

    def test_database_persistence(self):
        save_exam(self.mock_exam)
        loaded = get_exam(self.mock_exam_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.get("cover_model"), "opcao_4_azul_nautico_lagoa")
        self.assertEqual(loaded.get("cover_title"), "PROVA CANOA 2026")
        self.assertEqual(loaded.get("cover_subtitle"), "CADERNO M0402 • MATEMÁTICA")

        # Test update
        self.mock_exam["cover_title"] = "PROVA CANOA ATUALIZADA"
        self.mock_exam["cover_model"] = "opcao_1_montanhas_canoa"
        updated = update_exam(self.mock_exam_id, self.mock_exam)
        self.assertEqual(updated.get("cover_title"), "PROVA CANOA ATUALIZADA")
        self.assertEqual(updated.get("cover_model"), "opcao_1_montanhas_canoa")

    def test_render_cover_html(self):
        student = {"id": "st-101", "name": "MARIA CLARA DOS SANTOS"}
        classroom = {
            "name": "4º ANO A",
            "school_name": "ESCOLA GOV LUIZ CAVALCANTE",
            "shift": "MATUTINO"
        }
        
        for model in ["opcao_1_montanhas_canoa", "opcao_2_rio_verde_petroleo", "opcao_3_por_do_sol_solar", "opcao_4_azul_nautico_lagoa"]:
            self.mock_exam["cover_model"] = model
            html = render_single_cover_html(self.mock_exam, student, classroom)
            self.assertIn("MARIA CLARA DOS SANTOS", html)
            self.assertIn("4º ANO A", html)
            self.assertIn("data:image/png;base64", html) # QR Code
            self.assertIn("omr-tables-container", html)

    def test_batch_covers_pdf_generation(self):
        chrome = get_chrome_executable()
        if not chrome:
            self.skipTest("Chrome / Edge not available on this host.")

        classroom = {
            "name": "4º ANO A",
            "school_name": "ESCOLA GOV LUIZ CAVALCANTE",
            "shift": "MATUTINO"
        }
        students = [
            {"id": "st-01", "name": "ALUNO UM"},
            {"id": "st-02", "name": "ALUNO DOIS"}
        ]
        exams = [
            {
                "id": "ex-01",
                "title": "PORTUGUÊS 2026",
                "cover_title": "PROVA CANOA",
                "cover_subtitle": "PORTUGUÊS",
                "cover_model": "opcao_4_azul_nautico_lagoa",
                "num_questions": 20,
                "num_alternatives": 4
            },
            {
                "id": "ex-02",
                "title": "MATEMÁTICA 2026",
                "cover_title": "PROVA CANOA",
                "cover_subtitle": "MATEMÁTICA",
                "cover_model": "opcao_1_montanhas_canoa",
                "num_questions": 22,
                "num_alternatives": 4
            }
        ]

        # 1. Test order by student: 1 roster page + (2 students x 2 exams = 4 covers) = 5 pages
        pdf_bytes_student = generate_classroom_covers_pdf(classroom, students, exams, order_by="student")
        self.assertGreater(len(pdf_bytes_student), 1000)
        doc1 = fitz.open(stream=pdf_bytes_student, filetype="pdf")
        self.assertEqual(len(doc1), 5)
        # Verify page 1 is the official Attendance Roster
        page1_text = doc1[0].get_text()
        self.assertIn("ATA DE FREQUÊNCIA", page1_text)
        doc1.close()

        # 2. Test order by exam: 1 roster page + (2 exams x 2 students = 4 covers) = 5 pages
        pdf_bytes_exam = generate_classroom_covers_pdf(classroom, students, exams, order_by="exam")
        self.assertGreater(len(pdf_bytes_exam), 1000)
        doc2 = fitz.open(stream=pdf_bytes_exam, filetype="pdf")
        self.assertEqual(len(doc2), 5)
        doc2.close()

        # 3. Test explicit model_id override
        pdf_bytes_model = generate_classroom_covers_pdf(
            classroom, students, exams, order_by="student", model_id="opcao_3_por_do_sol_solar"
        )
        self.assertGreater(len(pdf_bytes_model), 1000)
        doc3 = fitz.open(stream=pdf_bytes_model, filetype="pdf")
        self.assertEqual(len(doc3), 5)
        doc3.close()

if __name__ == "__main__":
    unittest.main()
