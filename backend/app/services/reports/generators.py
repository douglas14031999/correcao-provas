from typing import Optional, Dict, Any, List
from .base_report import ReportData, ReportMetadata, ReportTableColumn
from ..database import (
    get_classroom_report,
    compare_classroom_exams,
    get_students_report_by_year,
    get_schools_overview_report,
    get_system_settings,
    get_school
)

import os
from datetime import datetime

def get_base_metadata(school_name: str = "", inep: str = "", classroom_name: str = "", grade_year: str = "", shift: str = "", exam_title: str = "") -> ReportMetadata:
    settings = get_system_settings()
    
    # Resolve official municipal logo path with multi-path automatic fallback
    logo = settings.get("logo_path", "")
    if not logo or not os.path.exists(logo):
        curr_dir = os.path.abspath(os.path.dirname(__file__))
        # Walk up to find root and check candidate locations
        p_root_5 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(curr_dir)))))
        p_root_4 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(curr_dir))))
        candidates = [
            os.path.join(p_root_4, "frontend", "assets", "logo_lagoa_da_canoa.png"),
            os.path.join(p_root_4, "backend", "storage", "assets", "logo_lagoa_da_canoa.png"),
            os.path.join(p_root_4, "backend", "storage", "logo_municipal.jpg"),
            os.path.join(p_root_5, "frontend", "assets", "logo_lagoa_da_canoa.png"),
            os.path.join(p_root_4, "storage", "assets", "logo_lagoa_da_canoa.png"),
            os.path.join(p_root_4, "storage", "logo_municipal.jpg"),
        ]
        for c in candidates:
            if os.path.exists(c):
                logo = os.path.abspath(c)
                break

    # Format shift
    shift_str = shift.strip() if shift else ""
    if not shift_str:
        shift_str = "( ) MANHÃ       ( ) TARDE"
    elif shift_str.upper() == "MANHÃ":
        shift_str = "( X ) MANHÃ     (   ) TARDE"
    elif shift_str.upper() == "TARDE":
        shift_str = "(   ) MANHÃ     ( X ) TARDE"

    return ReportMetadata(
        prefeitura=settings.get("prefeitura_name", "PREFEITURA MUNICIPAL DE LAGOA DA CANOA"),
        secretaria=settings.get("secretaria_name", "SECRETARIA MUNICIPAL DE EDUCAÇÃO"),
        state=settings.get("state_name", "Estado de Alagoas"),
        school_name=school_name,
        inep_code=inep,
        classroom_name=classroom_name,
        grade_year=grade_year,
        shift=shift_str,
        exam_title=exam_title,
        school_year=str(datetime.now().year),
        logo_path=logo
    )

# REL-01: Registro de Avaliação da Turma
def generate_classroom_report_data(classroom_id: str, exam_id: str) -> Optional[ReportData]:
    rep = get_classroom_report(classroom_id, exam_id)
    if not rep:
        return None

    cl = rep["classroom"]
    ex = rep["exam"]
    meta = get_base_metadata(
        school_name=cl.get("school_name", ""),
        classroom_name=cl.get("name", ""),
        grade_year=cl.get("grade_year", ""),
        shift=cl.get("shift", ""),
        exam_title=ex.get("title", "")
    )

    columns = [
        ReportTableColumn(key="pos", header="Nº", width_ratio=0.9, align="center"),
        ReportTableColumn(key="name", header="Nome do Estudante", width_ratio=5.5, align="left"),
        ReportTableColumn(key="score_str", header="Nota", width_ratio=1.3, align="center", is_numeric=True),
        ReportTableColumn(key="hits_str", header="Acertos", width_ratio=1.3, align="center"),
        ReportTableColumn(key="pct_str", header="Aproveitamento", width_ratio=1.7, align="center"),
        ReportTableColumn(key="status", header="Situação", width_ratio=1.5, align="center")
    ]

    rows = []
    ranked_num = 1
    for st in rep["students"]:
        is_graded = st.get("status") == "CORRIGIDO" and st.get("score") is not None
        score_val = st.get("score")
        correct = st.get("correct_count", 0)
        pct = st.get("percentage")

        rows.append({
            "pos": f"{ranked_num}º" if is_graded else "-",
            "registration": st.get("registration") or "-",
            "name": st.get("name", ""),
            "score_str": f"{score_val:.1f}" if is_graded else "-",
            "hits_str": f"{correct} / {ex.get('num_questions', 20)}" if is_graded else "-",
            "pct_str": f"{pct}%" if pct is not None else "-",
            "status": "CORRIGIDO" if is_graded else "PENDENTE"
        })
        if is_graded:
            ranked_num += 1

    summary_cards = [
        {"label": "Total de Estudantes", "value": rep["total_students"], "subtext": "Matriculados"},
        {"label": "Provas Corrigidas", "value": rep["graded_students"], "subtext": f"{round((rep['graded_students']/max(1, rep['total_students']))*100)}% pres."},
        {"label": "Média da Turma", "value": f"{rep['average_score']:.1f}", "subtext": f"de {ex.get('max_score', 10.0)} pts"},
        {"label": "Aproveitamento", "value": f"{rep['average_percentage']}%", "subtext": "Global"}
    ]

    return ReportData(
        title="Registro Oficial de Avaliação e Desempenho Escolar",
        metadata=meta,
        columns=columns,
        rows=rows,
        summary_cards=summary_cards,
        signatures=["Professor(a) / Aplicador(a)", "Coordenação Pedagógica / Direção"]
    )

# REL-02: Rendimento por Ano Escolar (2º Ano, 5º Ano, etc.)
def generate_year_performance_report_data(grade_year: str, school_id: Optional[str] = None, exam_id: Optional[str] = None) -> ReportData:
    rep = get_students_report_by_year(grade_year, school_id, exam_id)
    exam_info = rep.get("exam")
    exam_title = exam_info["title"] if exam_info else "Média Geral de Todos os Simulados"

    school_display = "REDE MUNICIPAL DE ENSINO (TODAS AS ESCOLAS)"
    inep_code = ""
    if school_id:
        sch = get_school(school_id)
        if sch:
            school_display = sch["name"].upper()
            inep_code = sch.get("inep_code", "")

    grade_display = grade_year if grade_year else "Todos os Anos"
    meta = get_base_metadata(
        school_name=school_display,
        inep=inep_code,
        grade_year=grade_display,
        exam_title=exam_title,
        classroom_name=f"Todas as Turmas ({grade_display})" if not school_id else f"Turmas ({grade_display})"
    )

    columns = [
        ReportTableColumn(key="rank", header="Classif.", width_ratio=1.0, align="center"),
        ReportTableColumn(key="name", header="Nome do Estudante", width_ratio=4.5, align="left"),
        ReportTableColumn(key="classroom", header="Turma", width_ratio=2.0, align="center"),
        ReportTableColumn(key="school", header="Unidade Escolar", width_ratio=3.5, align="left"),
        ReportTableColumn(key="score_str", header="Nota Final", width_ratio=1.4, align="center", is_numeric=True),
        ReportTableColumn(key="pct_str", header="Aproveitamento", width_ratio=1.6, align="center"),
        ReportTableColumn(key="status", header="Situação", width_ratio=1.4, align="center")
    ]

    rows = []
    for s in rep["students"]:
        is_graded = s.get("status") == "CORRIGIDO" and s.get("score") is not None
        score = s.get("score")
        pct = s.get("percentage")

        rows.append({
            "rank": f"{s.get('rank')}º" if s.get("rank") != "-" else "-",
            "name": s.get("name", ""),
            "classroom": s.get("classroom_name", ""),
            "school": s.get("school_name", ""),
            "score_str": f"{score:.1f}" if is_graded else "-",
            "pct_str": f"{pct}%" if pct is not None else "-",
            "status": "CORRIGIDO" if is_graded else "PENDENTE"
        })

    title_prefix = "Rendimento Escolar por Gabarito" if exam_info else "Rendimento Escolar Geral"
    doc_title = f"{title_prefix} — {grade_display.upper()} (Classificação da Maior para a Menor)"

    summary_cards = [
        {"label": f"Estudantes ({grade_display})", "value": rep["total_students"], "subtext": "Total"},
        {"label": "Avaliados", "value": rep["graded_students"], "subtext": "Com nota"},
        {"label": "Média Geral", "value": f"{rep['average_score']:.1f}", "subtext": "pts"},
        {"label": "Maior Nota", "value": f"{rep.get('highest_score', 0.0):.1f}", "subtext": "Pontuação máx."}
    ]

    return ReportData(
        title=doc_title,
        metadata=meta,
        columns=columns,
        rows=rows,
        summary_cards=summary_cards,
        signatures=["Coordenador(a) de Etapa / Ano", "Secretaria Municipal de Educação"]
    )

# REL-03: Diagnóstico por Questão / Descritores
def generate_questions_diagnostic_report_data(classroom_id: str, exam_id: str) -> Optional[ReportData]:
    rep = get_classroom_report(classroom_id, exam_id)
    if not rep:
        return None

    cl = rep["classroom"]
    ex = rep["exam"]
    meta = get_base_metadata(
        school_name=cl.get("school_name", ""),
        classroom_name=cl.get("name", ""),
        grade_year=cl.get("grade_year", ""),
        shift=cl.get("shift", ""),
        exam_title=ex.get("title", "")
    )

    columns = [
        ReportTableColumn(key="item", header="Item / Questão", width_ratio=1.5, align="center"),
        ReportTableColumn(key="correct_key", header="Gabarito", width_ratio=1.2, align="center"),
        ReportTableColumn(key="hits", header="Total de Acertos", width_ratio=1.8, align="center"),
        ReportTableColumn(key="accuracy", header="Taxa de Acerto (%)", width_ratio=2.0, align="center", is_numeric=True),
        ReportTableColumn(key="diagnosis", header="Diagnóstico Pedagógico", width_ratio=3.5, align="left")
    ]

    rows = []
    q_stats = rep.get("questions_stats", {})
    sorted_q = sorted(q_stats.keys(), key=lambda k: int(k) if k.isdigit() else k)

    for qk in sorted_q:
        q_info = q_stats[qk]
        acc = q_info.get("accuracy_percentage", 0.0)
        
        if acc >= 70.0:
            diag = "Dominado (Consolidado)"
        elif acc >= 40.0:
            diag = "Regular (Em Desenvolvimento)"
        else:
            diag = "CRÍTICO (Necessita Intervenção)"

        rows.append({
            "item": f"Questão {qk}",
            "correct_key": q_info.get("correct_answer", "-"),
            "hits": f"{q_info.get('correct_count', 0)} alunos",
            "accuracy": f"{acc:.1f}%",
            "diagnosis": diag
        })

    summary_cards = [
        {"label": "Total de Questões", "value": ex.get("num_questions", 0)},
        {"label": "Provas Corrigidas", "value": rep["graded_students"]},
        {"label": "Média da Turma", "value": f"{rep['average_score']:.1f}"},
        {"label": "Aproveitamento", "value": f"{rep['average_percentage']}%"}
    ]

    return ReportData(
        title="Diagnóstico Pedagógico Item a Item / Questão por Questão",
        metadata=meta,
        columns=columns,
        rows=rows,
        summary_cards=summary_cards,
        signatures=["Professor(a) Regente", "Coordenação Pedagógica"]
    )

# REL-04: Comparativo entre Gabaritos / Disciplinas
def generate_comparison_report_data(classroom_id: str, exam1_id: str, exam2_id: str) -> Optional[ReportData]:
    data = compare_classroom_exams(classroom_id, exam1_id, exam2_id)
    if not data:
        return None

    cl = data["classroom"]
    ex1 = data["exam1"]
    ex2 = data["exam2"]

    meta = get_base_metadata(
        school_name=cl.get("school_name", ""),
        classroom_name=cl.get("name", ""),
        grade_year=cl.get("grade_year", ""),
        shift=cl.get("shift", ""),
        exam_title=f"{ex1['title']} VS {ex2['title']}"
    )

    columns = [
        ReportTableColumn(key="name", header="Nome do Estudante", width_ratio=5.0, align="left"),
        ReportTableColumn(key="score1", header=f"Nota ({ex1['title']})", width_ratio=2.0, align="center", is_numeric=True),
        ReportTableColumn(key="score2", header=f"Nota ({ex2['title']})", width_ratio=2.0, align="center", is_numeric=True),
        ReportTableColumn(key="avg", header="Média Final", width_ratio=1.8, align="center", is_numeric=True),
        ReportTableColumn(key="best", header="Melhor Desempenho", width_ratio=2.8, align="center")
    ]

    rows = []
    for s in data["students"]:
        sc1_str = f"{s['score1']:.1f}" if s["score1"] is not None else "-"
        sc2_str = f"{s['score2']:.1f}" if s["score2"] is not None else "-"
        avg_str = f"{s['combined_avg']:.1f}" if s["combined_avg"] is not None else "-"

        rows.append({
            "name": s["name"],
            "score1": sc1_str,
            "score2": sc2_str,
            "avg": avg_str,
            "best": s.get("best_exam", "-")
        })

    sum_info = data["summary"]
    summary_cards = [
        {"label": f"Média ({ex1['title']})", "value": f"{sum_info['avg_score1']:.1f}"},
        {"label": f"Média ({ex2['title']})", "value": f"{sum_info['avg_score2']:.1f}"},
        {"label": "Diferença", "value": f"{sum_info['avg_diff']:+.1f} pts"},
        {"label": "Total Alunos", "value": sum_info["total_students"]}
    ]

    return ReportData(
        title="Relatório Comparativo de Desempenho entre Gabaritos",
        metadata=meta,
        columns=columns,
        rows=rows,
        summary_cards=summary_cards,
        signatures=["Professor(a) / Aplicador(a)", "Coordenação Pedagógica"]
    )

# REL-05: Panorâmico de Escolas e Turmas da Rede
def generate_schools_overview_report_data() -> ReportData:
    rep = get_schools_overview_report()
    meta = get_base_metadata(exam_title="Panorama Geral da Rede Municipal")

    columns = [
        ReportTableColumn(key="name", header="Unidade Escolar", width_ratio=4.5, align="left"),
        ReportTableColumn(key="inep", header="Código INEP", width_ratio=1.8, align="center"),
        ReportTableColumn(key="classrooms", header="Turmas", width_ratio=1.4, align="center"),
        ReportTableColumn(key="students", header="Matriculados", width_ratio=1.6, align="center"),
        ReportTableColumn(key="graded", header="Corrigidos", width_ratio=1.6, align="center"),
        ReportTableColumn(key="average", header="Média Geral", width_ratio=1.6, align="center", is_numeric=True)
    ]

    rows = []
    for s in rep["schools"]:
        rows.append({
            "name": s["school_name"],
            "inep": s["inep_code"] or "-",
            "classrooms": s["classrooms_count"],
            "students": s["students_count"],
            "graded": s["graded_count"],
            "average": f"{s['average_score']:.1f}"
        })

    summary_cards = [
        {"label": "Total de Escolas", "value": rep["total_schools"]},
        {"label": "Total de Estudantes", "value": rep["total_students"]},
        {"label": "Total de Avaliados", "value": rep["total_graded"]},
        {"label": "Média Municipal", "value": f"{rep['network_average']:.1f}"}
    ]

    return ReportData(
        title="Relatório Panorâmico de Escolas e Turmas da Rede Municipal",
        metadata=meta,
        columns=columns,
        rows=rows,
        summary_cards=summary_cards,
        signatures=["Secretário(a) Municipal de Educação", "Supervisão Pedagógica"]
    )
