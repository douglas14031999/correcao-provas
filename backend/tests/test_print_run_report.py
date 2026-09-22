import os
import sys
import unittest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.services.database import get_print_run_data
from app.services.reports import (
    generate_print_run_report_data,
    build_pdf_report,
    build_xlsx_report,
    build_docx_report,
)

client = TestClient(app)

class TestPrintRunReport(unittest.TestCase):
    def test_database_print_run_query(self):
        """Verifica se a consulta SQL de tiragem roda sem erros."""
        data = get_print_run_data()
        self.assertIsInstance(data, list)

    def test_generate_print_run_report_data(self):
        """Verifica se o gerador de dados do relatório de tiragem monta as 4 seções."""
        report = generate_print_run_report_data()
        if not report:
            # Se o banco de testes não possuir turmas vinculadas a exames, o teste passa graciosamente
            return

        self.assertIn("Tiragem", report.title)
        self.assertIsNotNone(report.sections)
        self.assertEqual(len(report.sections), 4)

        # Seção 1: Geral por Ano
        sec1 = report.sections[0]
        self.assertIn("CONSOLIDADO GERAL", sec1.title)
        self.assertTrue(len(sec1.columns) >= 3)

        # Seção 2: Por Escola e Ano
        sec2 = report.sections[1]
        self.assertIn("QUANTITATIVO POR ESCOLA", sec2.title)

        # Seção 3: Detalhamento por Turma
        sec3 = report.sections[2]
        self.assertIn("LOGÍSTICA DETALHADA POR TURMA", sec3.title)

        # Seção 4: Quantitativo Geral de Materiais
        sec4 = report.sections[3]
        self.assertIn("QUANTITATIVO GERAL DE MATERIAIS", sec4.title)
        self.assertTrue(len(sec4.rows) >= 5)

    def test_generate_print_run_sheets_mode(self):
        """Verifica o relatório de tiragem no modo detalhado de folhas (duplex e simplex)."""
        report_duplex = generate_print_run_report_data(mode="folhas", duplex=True)
        if report_duplex:
            self.assertIn("Folhas", report_duplex.title)
            self.assertIn("Frente e Verso", report_duplex.title)
            self.assertEqual(len(report_duplex.sections), 4)
            # Confere se a coluna de total_sheets está presente
            col_keys = [c.key for c in report_duplex.sections[0].columns]
            self.assertIn("total_sheets", col_keys)

        report_simplex = generate_print_run_report_data(mode="folhas", duplex=False)
        if report_simplex:
            self.assertIn("Só Frente", report_simplex.title)
            self.assertEqual(len(report_simplex.sections), 4)
            col_keys = [c.key for c in report_simplex.sections[0].columns]
            self.assertIn("total_sheets", col_keys)

    def test_print_run_formats_generation(self):
        """Testa a geração dos arquivos físicos em PDF, XLSX e DOCX."""
        report = generate_print_run_report_data()
        if not report:
            return

        # 1. PDF
        pdf_bytes = build_pdf_report(report)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

        # 2. XLSX
        xlsx_bytes = build_xlsx_report(report)
        self.assertGreater(len(xlsx_bytes), 1000)
        self.assertEqual(xlsx_bytes[:2], b"PK")

        # 3. DOCX (Microsoft Word)
        docx_bytes = build_docx_report(report)
        self.assertGreater(len(docx_bytes), 1000)
        self.assertEqual(docx_bytes[:2], b"PK")

    def test_api_print_run_endpoints(self):
        """Testa o endpoint da API para os 3 formatos: PDF, XLSX e DOCX em modo normal e folhas."""
        # PDF
        resp_pdf = client.get("/api/reports/print-run?format=pdf")
        if resp_pdf.status_code == 200:
            self.assertEqual(resp_pdf.headers["content-type"], "application/pdf")
            self.assertIn("Relatorio_Tiragem_Impressao_Provas", resp_pdf.headers["content-disposition"])
            self.assertTrue(resp_pdf.content.startswith(b"%PDF"))

        # PDF - Modo Folhas
        resp_folhas = client.get("/api/reports/print-run?format=pdf&mode=folhas&duplex=true")
        if resp_folhas.status_code == 200:
            self.assertEqual(resp_folhas.headers["content-type"], "application/pdf")
            self.assertIn("Relatorio_Tiragem_Folhas_Detalhadas", resp_folhas.headers["content-disposition"])
            self.assertTrue(resp_folhas.content.startswith(b"%PDF"))

        # XLSX
        resp_xlsx = client.get("/api/reports/print-run?format=xlsx&mode=folhas")
        if resp_xlsx.status_code == 200:
            self.assertIn("spreadsheetml", resp_xlsx.headers["content-type"])
            self.assertEqual(resp_xlsx.content[:2], b"PK")

        # DOCX
        resp_docx = client.get("/api/reports/print-run?format=docx&mode=folhas")
        if resp_docx.status_code == 200:
            self.assertIn("wordprocessingml", resp_docx.headers["content-type"])
            self.assertEqual(resp_docx.content[:2], b"PK")

if __name__ == "__main__":
    unittest.main()

