import unittest
import asyncio
import json
import os
import sys
from unittest.mock import patch, MagicMock

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.groq_service import (
    mask_api_key,
    get_configured_groq_api_key,
    generate_ai_question_groq,
    test_groq_api_key
)
from app.services.database import get_system_settings, update_system_settings
from app.services.exam_builder_db import (
    init_builder_db,
    insert_question_into_bank,
    get_question_bank
)

class TestGroqAIGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_builder_db()

    def test_mask_api_key(self):
        self.assertEqual(mask_api_key(""), "")
        self.assertEqual(mask_api_key("short"), "********")
        self.assertEqual(mask_api_key("gsk_1234567890abcdef"), "gsk_...cdef")

    def test_settings_groq_key_persistence(self):
        orig_settings = get_system_settings()
        orig_key = orig_settings.get("groq_api_key", "")

        try:
            update_system_settings({"groq_api_key": "gsk_test_mock_123456789"})
            settings = get_system_settings()
            self.assertEqual(settings.get("groq_api_key"), "gsk_test_mock_123456789")

            key = get_configured_groq_api_key()
            self.assertEqual(key, "gsk_test_mock_123456789")
        finally:
            update_system_settings({"groq_api_key": orig_key})

    @patch("httpx.AsyncClient.post")
    def test_generate_ai_question_groq_mock(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "statement": "Em uma fazenda em Lagoa da Canoa, um agricultor colheu 240 espigas de milho.",
                        "bncc_code": "EF05MA08",
                        "correct_answer": "C",
                        "alternatives": [
                            {"letter": "A", "text": "100 espigas"},
                            {"letter": "B", "text": "180 espigas"},
                            {"letter": "C", "text": "240 espigas"},
                            {"letter": "D", "text": "300 espigas"}
                        ],
                        "explanation": "O agricultor colheu exatamente 240 espigas conforme descrito no texto-base."
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        # Executa chamada assíncrona com chave simulada
        with patch("app.services.groq_service.get_configured_groq_api_key", return_value="gsk_valid_key"):
            result = asyncio.run(generate_ai_question_groq(
                discipline="Matemática",
                grade_year="5º Ano",
                bncc_code="EF05MA08",
                difficulty="Médio",
                num_alternatives=4,
                local_theme="Lagoa da Canoa"
            ))

        self.assertIn("Lagoa da Canoa", result["statement"])
        self.assertEqual(result["correct_answer"], "C")
        self.assertEqual(result["bncc_code"], "EF05MA08")
        self.assertEqual(len(result["alternatives"]), 4)
        self.assertTrue(result["alternatives"][2]["is_correct"])

    def test_insert_question_into_bank(self):
        question_data = {
            "statement": "Questão de Teste Automatizado BNCC com IA",
            "discipline": "Matemática",
            "grade_year": "9º Ano",
            "bncc_code": "EF09MA06",
            "difficulty": "Médio",
            "points": 1.0,
            "explanation": "Justificativa da resolução",
            "alternatives": [
                {"letter": "A", "text": "Alternativa A", "is_correct": False},
                {"letter": "B", "text": "Alternativa B", "is_correct": True},
                {"letter": "C", "text": "Alternativa C", "is_correct": False},
                {"letter": "D", "text": "Alternativa D", "is_correct": False}
            ]
        }

        res = insert_question_into_bank(question_data)
        self.assertTrue(res.get("success"))
        qid = res.get("id")
        self.assertTrue(bool(qid))

        # Verifica se a questão foi encontrada pelo get_question_bank
        bank_res = get_question_bank(query="Questão de Teste Automatizado BNCC com IA")
        items = bank_res.get("items", [])
        self.assertTrue(any(it["id"] == qid for it in items))

        saved_item = next(it for it in items if it["id"] == qid)
        self.assertEqual(saved_item["bncc_code"], "EF09MA06")
        self.assertEqual(len(saved_item["alternatives"]), 4)
        self.assertTrue(saved_item["alternatives"][1]["is_correct"])

if __name__ == "__main__":
    unittest.main()
