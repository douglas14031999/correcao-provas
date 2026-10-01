import unittest
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.exam_builder_db import (
    init_builder_db,
    insert_question_into_bank,
    export_question_bank_data,
    import_question_bank_data,
    normalize_statement
)

class TestQuestionBankBackup(unittest.TestCase):
    def setUp(self):
        init_builder_db()

    def test_normalize_statement(self):
        s1 = "  Qual   é a   capital  de   Alagoas?  "
        s2 = "qual é a capital de alagoas?"
        self.assertEqual(normalize_statement(s1), normalize_statement(s2))

    def test_export_and_import_with_deduplication(self):
        # 1. Insere uma questão base no banco
        unique_stmt = "Questão Teste Export/Import " + os.urandom(4).hex() + ": Calcule a raiz de 144."
        q_data = {
            "statement": unique_stmt,
            "discipline": "Matemática",
            "grade_year": "9º Ano",
            "bncc_code": "EF09MA03",
            "explanation": "A raiz quadrada de 144 é 12.",
            "alternatives": [
                {"letter": "A", "text": "10", "is_correct": False},
                {"letter": "B", "text": "12", "is_correct": True},
                {"letter": "C", "text": "14", "is_correct": False},
                {"letter": "D", "text": "16", "is_correct": False}
            ]
        }
        insert_question_into_bank(q_data)

        # 2. Exporta o banco
        export_res = export_question_bank_data()
        self.assertTrue(export_res["total_questions"] >= 1)
        found = any(q["statement"] == unique_stmt for q in export_res["questions"])
        self.assertTrue(found, "Questão inserida deve estar presente na exportação")

        # 3. Tenta importar um arquivo contendo a questão já existente + uma questão nova
        new_unique_stmt = "Questão Nova Importada " + os.urandom(4).hex() + ": Qual é o maior planeta?"
        import_payload = {
            "questions": [
                # Questão duplicada (deve ser pulada)
                {
                    "statement": "   " + unique_stmt.upper() + "   ",  # Mesma questão com variação de caixa/espaço
                    "discipline": "Matemática",
                    "grade_year": "9º Ano",
                    "alternatives": [
                        {"letter": "A", "text": "10", "is_correct": False},
                        {"letter": "B", "text": "12", "is_correct": True}
                    ]
                },
                # Questão inédita (deve ser importada)
                {
                    "statement": new_unique_stmt,
                    "discipline": "Ciências",
                    "grade_year": "6º Ano",
                    "bncc_code": "EF06CI11",
                    "alternatives": [
                        {"letter": "A", "text": "Terra", "is_correct": False},
                        {"letter": "B", "text": "Júpiter", "is_correct": True}
                    ]
                }
            ]
        }

        import_res = import_question_bank_data(import_payload)
        self.assertTrue(import_res["success"])
        self.assertEqual(import_res["total_in_file"], 2)
        self.assertEqual(import_res["imported_count"], 1, "Apenas a questão inédita deve ser importada")
        self.assertEqual(import_res["skipped_duplicates"], 1, "A questão duplicada deve ser ignorada")

        # 4. Tenta reimportar o mesmo lote: agora ambas devem ser puladas como duplicadas!
        second_import_res = import_question_bank_data(import_payload)
        self.assertEqual(second_import_res["imported_count"], 0)
        self.assertEqual(second_import_res["skipped_duplicates"], 2)

if __name__ == "__main__":
    unittest.main()
