import os
import sys
import unittest
import io
import asyncio
from fastapi import UploadFile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.database import (
    init_db,
    get_or_create_school,
    get_classroom_with_details,
    list_schools_tree
)
from app.api.schools import import_students_csv

class TestUserCsvImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_manual_school_and_user_csv(self):
        # 1. Create school manually
        school = get_or_create_school("Escola Municipal Manoel Pereira Filho")
        self.assertIsNotNone(school["id"])

        user_csv_text = (
            "Rede;Ano Escolar;Componente Curricular;Estado;Município;Código da Turma;Turma;Estudante;Avaliado;Nível de aprendizagem;H 01;H 02;H 03;H 04;H 05;H 06;H 07;H 08\n"
            "MUNICIPAL;ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO;LÍNGUA PORTUGUESA;ALAGOAS;LAGOA DA CANOA; e2iv8e17d526 ;turma 1 Aline;ENZO GABRIEL IZIDORO DANTAS;Sim;Defasagem; 1 / 3; 2 / 3; 1 / 3; 0 / 3; 0 / 3; 2 / 3; 0 / 2; 1 / 2\n"
            "MUNICIPAL;ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO;LÍNGUA PORTUGUESA;ALAGOAS;LAGOA DA CANOA; e2iv8e17d526 ;turma 1 Aline;LARIELY HENRIQUE DE MELO;Sim;Defasagem; 3 / 3; 2 / 3; 2 / 3; 1 / 3; 0 / 3; 1 / 3; 0 / 2; 2 / 2\n"
            "MUNICIPAL;ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO;LÍNGUA PORTUGUESA;ALAGOAS;LAGOA DA CANOA; e2iv8e17d526 ;turma 1 Aline;LAÍSE GABRIELLY BEZERRA DE OLIVEIRA;Sim;Adequado; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 1 / 2; 1 / 2\n"
            "MUNICIPAL;ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO;LÍNGUA PORTUGUESA;ALAGOAS;LAGOA DA CANOA; e2iv8e17d526 ;turma 1 Aline;LUIZ LORENZO PADILHA MENDES;Sim;Adequado; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 2 / 3; 3 / 3; 1 / 2; 2 / 2\n"
            "MUNICIPAL;ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO;LÍNGUA PORTUGUESA;ALAGOAS;LAGOA DA CANOA; e2iv8e17d526 ;turma 1 Aline;MARIA CECÍLIA ALVES DA SILVA;Sim;Adequado; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 2 / 2; 1 / 2\n"
            "MUNICIPAL;ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO;LÍNGUA PORTUGUESA;ALAGOAS;LAGOA DA CANOA; e2iv8e17d526 ;turma 1 Aline;THAYLOR PEREIRA DE FREITAS;Sim;Intermediário; 3 / 3; 2 / 3; 3 / 3; 3 / 3; 0 / 3; 1 / 3; 0 / 2; 1 / 2\n"
            "MUNICIPAL;ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO;LÍNGUA PORTUGUESA;ALAGOAS;LAGOA DA CANOA; e2iv8e17d526 ;turma 1 Aline;ÍCARO IAN ADELINO DA SILVA;Sim;Adequado; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 3 / 3; 2 / 2; 1 / 2\n"
        )

        upload_file = UploadFile(
            filename="dados_alunos.csv",
            file=io.BytesIO(user_csv_text.encode("utf-8-sig"))
        )

        # 2. Import into the manually created school
        res = asyncio.run(import_students_csv(upload_file, school_id=school["id"]))
        self.assertTrue(res["success"])
        self.assertEqual(res["imported_students"], 7)
        self.assertEqual(res["school_name"], "Escola Municipal Manoel Pereira Filho")

        # 3. Check classroom details
        tree = list_schools_tree()
        matched_school = next((s for s in tree if s["id"] == school["id"]), None)
        self.assertIsNotNone(matched_school)
        self.assertEqual(len(matched_school["classrooms"]), 1)
        
        classroom_meta = matched_school["classrooms"][0]
        self.assertEqual(classroom_meta["name"], "turma 1 Aline")
        self.assertEqual(classroom_meta["student_count"], 7)

        # 4. Check students list
        full_class = get_classroom_with_details(classroom_meta["id"])
        self.assertEqual(len(full_class["students"]), 7)
        first_student = full_class["students"][0]
        self.assertEqual(first_student["registration"], "e2iv8e17d526")

if __name__ == "__main__":
    unittest.main()
