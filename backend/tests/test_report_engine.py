import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.reports.base_report import ReportData, ReportMetadata, ReportTableColumn
from app.services.reports.pdf_builder import build_pdf_report
from app.services.reports.xlsx_builder import build_xlsx_report
from app.services.reports.docx_builder import build_docx_report
from app.services.reports.generators import (
    generate_schools_overview_report_data,
    generate_year_performance_report_data,
)
from app.services.database import get_system_settings, update_system_settings

def test_builders_generate_valid_files():
    data = ReportData(
        title="REGISTRO DE AVALIAÇÃO DA TURMA",
        subtitle="1º BIMESTRE - AVALIAÇÃO DIAGNÓSTICA",
        metadata=ReportMetadata(
            prefeitura="PREFEITURA MUNICIPAL DE LAGOA DA CANOA",
            secretaria="SECRETARIA MUNICIPAL DE EDUCAÇÃO",
            state="Estado de Alagoas",
            school_name="ESCOLA MUNICIPAL MANOEL ALVES",
            classroom_name="5º ANO A",
            grade_year="5º Ano",
            exam_title="SIMULADO REGIONAL LP/MAT",
            school_year="2026",
            issue_date="16/09/2026 14:00"
        ),
        columns=[
            ReportTableColumn(key="pos", header="Pos.", width_ratio=0.8, align="center"),
            ReportTableColumn(key="name", header="Nome do Estudante", width_ratio=4.0, align="left"),
            ReportTableColumn(key="score", header="Nota", width_ratio=1.2, align="center", is_numeric=True),
            ReportTableColumn(key="status", header="Situação", width_ratio=1.5, align="center")
        ],
        rows=[
            {"pos": 1, "name": "ANA JULIA SILVA", "score": "9.5", "status": "CONSOLIDADO"},
            {"pos": 2, "name": "BRUNO HENRIQUE SANTOS", "score": "8.0", "status": "EM DESENVOLVIMENTO"},
            {"pos": 3, "name": "CARLA LIMA DE OLIVEIRA", "score": "6.5", "status": "ATENÇÃO"}
        ],
        summary_cards=[
            {"label": "Total Alunos", "value": "3"},
            {"label": "Presença", "value": "100%"},
            {"label": "Média da Turma", "value": "8.0"},
            {"label": "Aproveitamento", "value": "80%"}
        ],
        signatures=[
            "Professor(a) Regente",
            "Coordenação Pedagógica",
            "Direção Escolar"
        ]
    )

    # 1. PDF
    pdf_bytes = build_pdf_report(data)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
    print("  -> PDF generated successfully (", len(pdf_bytes), "bytes )")

    # 2. XLSX
    xlsx_bytes = build_xlsx_report(data)
    assert len(xlsx_bytes) > 1000
    assert xlsx_bytes[:2] == b"PK"  # Zip format for xlsx
    print("  -> XLSX generated successfully (", len(xlsx_bytes), "bytes )")

    # 3. DOCX
    docx_bytes = build_docx_report(data)
    assert len(docx_bytes) > 1000
    assert docx_bytes[:2] == b"PK"  # Zip format for docx
    print("  -> DOCX generated successfully (", len(docx_bytes), "bytes )")

def test_system_settings_db():
    orig = get_system_settings()
    try:
        update_system_settings(
            prefeitura_name="PREFEITURA MUNICIPAL DE TESTE",
            secretaria_name="SECRETARIA DE EDUCAÇÃO DE TESTE",
            state_name="AL"
        )
        s = get_system_settings()
        assert s["prefeitura_name"] == "PREFEITURA MUNICIPAL DE TESTE"
        assert s["secretaria_name"] == "SECRETARIA DE EDUCAÇÃO DE TESTE"
        assert s["state_name"] == "AL"
        print("  -> System settings DB functions passed")
    finally:
        update_system_settings(
            prefeitura_name=orig.get("prefeitura_name", "PREFEITURA MUNICIPAL DE LAGOA DA CANOA"),
            secretaria_name=orig.get("secretaria_name", "SECRETARIA MUNICIPAL DE EDUCAÇÃO"),
            state_name=orig.get("state_name", "Estado de Alagoas"),
            logo_path=orig.get("logo_path", "")
        )

def test_network_overview_generator():
    data = generate_schools_overview_report_data()
    assert data is not None
    pdf = build_pdf_report(data)
    assert len(pdf) > 500
    xlsx = build_xlsx_report(data)
    assert len(xlsx) > 500
    docx = build_docx_report(data)
    assert len(docx) > 500
    print("  -> Schools overview data & builders passed")

def test_year_performance_generator():
    data = generate_year_performance_report_data("5º Ano", None, None)
    assert data is not None
    pdf = build_pdf_report(data)
    assert len(pdf) > 500
    xlsx = build_xlsx_report(data)
    assert len(xlsx) > 500
    docx = build_docx_report(data)
    assert len(docx) > 500
    print("  -> Year performance data & builders passed")

if __name__ == "__main__":
    print("Running test_builders_generate_valid_files...")
    test_builders_generate_valid_files()
    print("Running test_system_settings_db...")
    test_system_settings_db()
    print("Running test_network_overview_generator...")
    test_network_overview_generator()
    print("Running test_year_performance_generator...")
    test_year_performance_generator()
    print("\n>>> ALL REPORT ENGINE TESTS PASSED SUCCESSFULLY! <<<")

