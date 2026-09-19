import unicodedata
import re
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response

from app.services.reports import (
    build_pdf_report,
    build_xlsx_report,
    build_docx_report,
    generate_classroom_report_data,
    generate_year_performance_report_data,
    generate_questions_diagnostic_report_data,
    generate_comparison_report_data,
    generate_schools_overview_report_data,
    generate_school_report_data,
    generate_print_run_report_data,
)
from app.services.database import (
    get_classroom_linked_exams,
    list_exams,
    get_students_report_by_year,
    get_exams_by_grade_year,
    get_macro_dashboard_data
)

router = APIRouter(prefix="/reports", tags=["Módulo de Relatórios Oficiais"])

@router.get("/dashboard")
def get_dashboard_metrics(exam_id: Optional[str] = Query(None)):
    """Retorna métricas macros e consolidadas para o Dashboard Inicial."""
    try:
        return get_macro_dashboard_data(exam_id=exam_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular métricas do dashboard: {str(e)}")

def sanitize_filename(name: str) -> str:
    nfkd = unicodedata.normalize('NFKD', str(name))
    ascii_name = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', ascii_name)
    return re.sub(r'_+', '_', clean).strip('_')

def export_report_response(report_data, format: str, base_filename: str) -> Response:
    fmt = (format or "pdf").lower().strip()
    safe_name = sanitize_filename(base_filename)

    if fmt == "xlsx":
        content = build_xlsx_report(report_data)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{safe_name}.xlsx"
    elif fmt == "docx":
        content = build_docx_report(report_data)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{safe_name}.docx"
    elif fmt == "pdf":
        content = build_pdf_report(report_data, orientation="portrait")
        media_type = "application/pdf"
        filename = f"{safe_name}.pdf"
    else:
        raise HTTPException(status_code=400, detail="Formato inválido. Escolha entre 'pdf', 'xlsx' ou 'docx'.")

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.get("/classroom/{classroom_id}")
def export_classroom_report(
    classroom_id: str,
    exam_id: Optional[str] = Query(None, description="ID do simulado/gabarito"),
    format: str = Query("pdf", description="Formato de exportação: pdf, xlsx, docx")
):
    """R1: Registro de Avaliação da Turma"""
    target_exam_id = exam_id
    if not target_exam_id:
        linked = get_classroom_linked_exams(classroom_id)
        if linked:
            target_exam_id = linked[0]["id"]
        else:
            all_exams = list_exams()
            if all_exams:
                target_exam_id = all_exams[0]["id"]
            else:
                raise HTTPException(status_code=404, detail="Nenhum simulado cadastrado no sistema.")

    data = generate_classroom_report_data(classroom_id, target_exam_id)
    if not data:
        raise HTTPException(status_code=404, detail="Turma ou simulado não encontrado.")
    
    cl_name = data.metadata.classroom_name or "turma"
    return export_report_response(data, format, f"Relatorio_Turma_{cl_name}")

@router.get("/year-performance")
def export_year_performance_report(
    grade_year: str = Query("", description="Série ou Ano escolar (ex: 2º Ano, 5º Ano)"),
    school_id: Optional[str] = Query(None, description="ID da escola opcional para filtrar"),
    exam_id: Optional[str] = Query(None, description="ID do simulado opcional"),
    format: str = Query("pdf", description="Formato: pdf, xlsx, docx, json")
):
    """R2: Rendimento Geral por Ano Escolar (1º ao 9º Ano) ordenado do melhor ao pior desempenho"""
    fmt = (format or "pdf").lower().strip()
    if fmt == "json":
        return get_students_report_by_year(grade_year, school_id, exam_id)

    data = generate_year_performance_report_data(grade_year, school_id, exam_id)
    scope = "Rede" if not school_id else "Escola"
    gy_slug = grade_year.replace(" ", "_") if grade_year else "Todos_Anos"
    return export_report_response(data, format, f"Rendimento_{gy_slug}_{scope}")

@router.get("/year-exams")
def list_year_exams(
    grade_year: str = Query("", description="Série ou Ano escolar"),
    school_id: Optional[str] = Query(None, description="ID da escola opcional")
):
    """Retorna apenas os simulados/gabaritos vinculados às turmas daquele ano escolar / série."""
    return get_exams_by_grade_year(grade_year, school_id)

@router.get("/diagnostic/{classroom_id}")
def export_questions_diagnostic_report(
    classroom_id: str,
    exam_id: Optional[str] = Query(None, description="ID do simulado"),
    format: str = Query("pdf", description="Formato: pdf, xlsx, docx")
):
    """R3: Diagnóstico Item a Item / Questão por Questão"""
    target_exam_id = exam_id
    if not target_exam_id:
        linked = get_classroom_linked_exams(classroom_id)
        if linked:
            target_exam_id = linked[0]["id"]
        else:
            all_exams = list_exams()
            if all_exams:
                target_exam_id = all_exams[0]["id"]
            else:
                raise HTTPException(status_code=404, detail="Nenhum simulado cadastrado no sistema.")

    data = generate_questions_diagnostic_report_data(classroom_id, target_exam_id)
    if not data:
        raise HTTPException(status_code=404, detail="Turma ou simulado não encontrado.")
    
    cl_name = data.metadata.classroom_name or "turma"
    return export_report_response(data, format, f"Diagnostico_Questoes_{cl_name}")

@router.get("/compare/{classroom_id}")
def export_comparison_report(
    classroom_id: str,
    exam1: str = Query(..., description="ID do primeiro gabarito"),
    exam2: str = Query(..., description="ID do segundo gabarito"),
    format: str = Query("pdf", description="Formato: pdf, xlsx, docx")
):
    """R4: Relatório Comparativo entre Gabaritos"""
    data = generate_comparison_report_data(classroom_id, exam1, exam2)
    if not data:
        raise HTTPException(status_code=404, detail="Dados insuficientes para comparativo.")
    
    cl_name = data.metadata.classroom_name or "turma"
    return export_report_response(data, format, f"Comparativo_Gabaritos_{cl_name}")

@router.get("/schools-overview")
def export_schools_overview_report(
    format: str = Query("pdf", description="Formato: pdf, xlsx, docx")
):
    """R5: Panorâmico de Escolas e Turmas da Rede Municipal"""
    data = generate_schools_overview_report_data()
    return export_report_response(data, format, "Panoramico_Escolas_Rede_Municipal")

@router.get("/school/{school_id}")
def export_school_report(
    school_id: str,
    format: str = Query("pdf", description="Formato: pdf, xlsx, docx")
):
    """R6: Relatório Consolidado da Escola (Turmas, Top 3 Geral e Top 3 por Série)"""
    data = generate_school_report_data(school_id)
    if not data:
        raise HTTPException(status_code=404, detail="Escola não encontrada.")

    sch_name = data.metadata.school_name or "escola"
    return export_report_response(data, format, f"Relatorio_Escola_{sch_name}")

@router.get("/print-run")
def export_print_run_report(
    format: str = Query("pdf", description="Formato: pdf, xlsx, docx"),
    school_id: Optional[str] = Query(None, description="Filtrar por ID da Escola"),
    exam_id: Optional[str] = Query(None, description="Filtrar por ID do Simulado/Avaliação")
):
    """R7: Relatório Oficial de Tiragem e Impressão de Provas (Geral por Série, Escola/Série/Gabarito e Turmas). Formatos: PDF, XLSX, DOCX."""
    data = generate_print_run_report_data(school_id=school_id, exam_id=exam_id)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma turma com simulado vinculado encontrada para os filtros selecionados."
        )

    base_name = "Relatorio_Tiragem_Impressao_Provas"
    if school_id and data.metadata.school_name and data.metadata.school_name != "REDE MUNICIPAL DE ENSINO":
        base_name += f"_{data.metadata.school_name}"

    return export_report_response(data, format, base_name)

