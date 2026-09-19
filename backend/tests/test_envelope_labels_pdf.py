import os
import sys
import unittest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app
from app.services.database import (
    init_db,
    get_or_create_school,
    get_or_create_classroom,
    get_or_create_student
)
from app.services.pdf_generator import (
    generate_envelope_labels_pdf,
    DEFAULT_LOGO_PATH
)

class TestEnvelopeLabelsPdf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_pdf_generation_single_classroom(self):
        """Test PDF generation for 1 classroom (1 page, 1 slot used)."""
        school = {"id": "sch-t1", "name": "Escola Teste 1 Turma", "inep_code": "11223344"}
        classrooms = [{
            "id": "c1",
            "name": "5º Ano A",
            "shift": "Matutino",
            "student_count": 25,
            "linked_exams": [
                {"id": "ex1", "title": "Simulado Língua Portuguesa", "num_questions": 15}
            ]
        }]
        pdf_bytes = generate_envelope_labels_pdf(school, classrooms, logo_path=DEFAULT_LOGO_PATH)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_02_pdf_generation_four_classrooms(self):
        """Test PDF generation for exactly 4 classrooms (1 full page of 4 labels)."""
        school = {"id": "sch-t4", "name": "Escola Teste 4 Turmas", "inep_code": "22334455"}
        classrooms = [
            {
                "id": f"c{i}",
                "name": f"{i}º Ano A",
                "shift": "Matutino" if i % 2 == 0 else "Vespertino",
                "student_count": 20 + i,
                "linked_exams": [
                    {"id": f"ex{i}_1", "title": "Português", "num_questions": 15},
                    {"id": f"ex{i}_2", "title": "Matemática", "num_questions": 15}
                ]
            }
            for i in range(1, 5)
        ]
        pdf_bytes = generate_envelope_labels_pdf(school, classrooms, logo_path=DEFAULT_LOGO_PATH)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_03_pdf_generation_five_classrooms(self):
        """Test PDF generation for 5 classrooms (2 pages: 4 on first, 1 on second)."""
        school = {"id": "sch-t5", "name": "Escola Teste 5 Turmas", "inep_code": "33445566"}
        classrooms = [
            {
                "id": f"c{i}",
                "name": f"{i}º Ano B",
                "shift": "Integral",
                "student_count": 18 + i,
                "linked_exams": []
            }
            for i in range(1, 6)
        ]
        pdf_bytes = generate_envelope_labels_pdf(school, classrooms, logo_path=DEFAULT_LOGO_PATH)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_04_pdf_generation_eight_classrooms(self):
        """Test PDF generation for 8 classrooms (2 full pages of 4 labels)."""
        school = {"id": "sch-t8", "name": "Escola Teste 8 Turmas", "inep_code": "44556677"}
        classrooms = [
            {
                "id": f"c{i}",
                "name": f"{i}º Ano C",
                "shift": "Matutino",
                "student_count": 30,
                "linked_exams": [
                    {"id": f"ex{i}", "title": "Avaliação Diagnóstica", "num_questions": 20}
                ]
            }
            for i in range(1, 9)
        ]
        pdf_bytes = generate_envelope_labels_pdf(school, classrooms, logo_path=DEFAULT_LOGO_PATH)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_05_api_endpoint_success_and_errors(self):
        """Test the GET /api/schools/{school_id}/envelope-labels-pdf endpoint."""
        # 1. Escola inexistente -> 404
        res_404 = self.client.get("/api/schools/escola-inexistente-xyz/envelope-labels-pdf")
        self.assertEqual(res_404.status_code, 404)

        # 2. Escola criada sem turmas -> 400
        empty_sch = get_or_create_school("Escola Sem Turmas Teste", inep_code="00001111")
        res_400 = self.client.get(f"/api/schools/{empty_sch['id']}/envelope-labels-pdf")
        self.assertEqual(res_400.status_code, 400)
        self.assertIn("não possui turmas", res_400.json().get("detail", ""))

        # 3. Escola com turma e alunos -> 200 com PDF e nome [turma] - Etiquetas - [Escola]
        school_ok = get_or_create_school("Escola Com Turmas Completa", inep_code="99887766")
        cl = get_or_create_classroom(school_ok["id"], "4º Ano Manhã", "Matutino")
        get_or_create_student(cl["id"], "Estudante Teste 1", "REG-001")

        res_200 = self.client.get(f"/api/schools/{school_ok['id']}/envelope-labels-pdf?classroom_id={cl['id']}")
        self.assertEqual(res_200.status_code, 200)
        self.assertEqual(res_200.headers.get("content-type"), "application/pdf")
        self.assertIn("attachment", res_200.headers.get("content-disposition", ""))
        self.assertIn("4o_Ano_Manha_-_Etiquetas_-_Escola_Com_Turmas_Completa.pdf", res_200.headers.get("content-disposition", ""))
        self.assertTrue(res_200.content.startswith(b"%PDF-1.4"))

    def test_06_expected_sheets_multiplication(self):
        """Test that expected sheets = students count * number of linked exams (e.g. 40 * 2 = 80)."""
        import fitz
        school = {"id": "sch-calc", "name": "Escola Multiplicação", "inep_code": "55667788"}
        classrooms = [{
            "id": "c_calc",
            "name": "8º ANO - A MATUTINO",
            "shift": "Matutino",
            "student_count": 40,
            "linked_exams": [
                {"id": "ex1", "title": "PROVA CANOA 2026 – LÍNGUA PORTUGUESA", "num_questions": 22},
                {"id": "ex2", "title": "PROVA CANOA 2026 – MATEMÁTICA", "num_questions": 22}
            ]
        }]
        pdf_bytes = generate_envelope_labels_pdf(school, classrooms, logo_path=DEFAULT_LOGO_PATH)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = doc[0].get_text()
        doc.close()
        self.assertIn("80 FOLHAS DE RESPOSTAS", text)
        self.assertIn("40 alunos × 2 cadernos", text)

if __name__ == "__main__":
    unittest.main()
