import os
import sys
import io
import zipfile
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
    get_or_create_student,
    save_exam,
    link_exams_to_classroom
)
from app.services.pdf_generator import generate_classroom_attendance_roster_pdf

class TestSchoolPackageZip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

        # Setup test school, classroom, student and exam
        cls.school = get_or_create_school("Escola Municipal Pacote Teste", inep_code="99887766")
        cls.classroom = get_or_create_classroom(cls.school["id"], "5º Ano Alpha", shift="Manhã", grade_year="5º Ano")
        cls.student = get_or_create_student(cls.classroom["id"], "Aluno Teste Pacote", registration="20269999")

        import uuid
        cls.exam_id = str(uuid.uuid4())[:8]
        cls.exam = save_exam({
            "id": cls.exam_id,
            "title": "Simulado Avaliativo de Teste",
            "school_id": cls.school["id"],
            "grade_year": "5º Ano",
            "num_questions": 10,
            "num_alternatives": 4,
            "page_count": 2,
            "answer_key": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "A", "6": "B", "7": "C", "8": "D", "9": "A", "10": "B"}
        })
        link_exams_to_classroom(cls.classroom["id"], [cls.exam_id])

    def test_01_attendance_roster_pdf_generation(self):
        """Verifica a geração do PDF isolado da Ata de Frequência da turma."""
        pdf_bytes = generate_classroom_attendance_roster_pdf(
            classroom=self.classroom,
            students=[self.student],
            exams=[self.exam]
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_02_school_package_zip_endpoint(self):
        """Verifica o endpoint de download do pacote completo em .ZIP da escola."""
        resp = self.client.get(f"/api/schools/{self.school['id']}/package-zip")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "application/zip")
        self.assertIn("Pacote_Completo", resp.headers["content-disposition"])

        zip_content = resp.content
        self.assertTrue(zip_content.startswith(b"PK\x03\x04"))

        # Inspeciona os arquivos contidos dentro do ZIP
        zf = zipfile.ZipFile(io.BytesIO(zip_content))
        file_list = zf.namelist()

        # 1. Deve conter as Etiquetas da escola em arquivo único
        etiquetas_files = [f for f in file_list if "Etiquetas" in f and f.endswith(".pdf")]
        self.assertTrue(len(etiquetas_files) >= 1)

        # 2. Deve conter a Ata de Frequência da turma
        ata_files = [f for f in file_list if "Ata" in f and f.endswith(".pdf")]
        self.assertTrue(len(ata_files) >= 1)

        # 3. Deve conter as Capas de Prova da turma
        capas_files = [f for f in file_list if "Capas" in f and f.endswith(".pdf")]
        self.assertTrue(len(capas_files) >= 1)

    def test_03_classroom_attendance_roster_endpoint(self):
        """Verifica o endpoint avulso de ata da turma."""
        resp = self.client.get(f"/api/classrooms/{self.classroom['id']}/attendance-roster-pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
