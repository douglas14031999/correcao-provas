from typing import Optional, Dict, Any, List
import os
import re
from collections import defaultdict
from datetime import datetime

from .base_report import ReportData, ReportMetadata, ReportTableColumn, ReportTableSection
from ..database import (
    get_classroom_report,
    compare_classroom_exams,
    get_students_report_by_year,
    get_schools_overview_report,
    get_school_report_details,
    get_system_settings,
    get_school,
    get_print_run_data
)

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
    if shift_str:
        if shift_str.upper() == "MANHÃ":
            shift_str = "( X ) MANHÃ     (   ) TARDE"
        elif shift_str.upper() == "TARDE":
            shift_str = "(   ) MANHÃ     ( X ) TARDE"
    elif classroom_name and classroom_name.strip() not in ("", "-"):
        shift_str = "( ) MANHÃ       ( ) TARDE"
    else:
        shift_str = ""

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


# REL-06: Relatório Consolidado da Escola (Turmas, Top 3 Geral e Top 3 por Série)
def generate_school_report_data(school_id: str) -> Optional[ReportData]:
    rep = get_school_report_details(school_id)
    if not rep:
        return None

    sch = rep["school"]
    meta = get_base_metadata(
        school_name=sch["name"],
        inep=sch.get("inep_code", "")
    )

    # Section 1: Desempenho das Turmas por Prova / Simulado
    sec1_columns = [
        ReportTableColumn(key="classroom_name", header="Turma", width_ratio=2.2, align="left"),
        ReportTableColumn(key="grade_year", header="Ano/Série", width_ratio=1.6, align="center"),
        ReportTableColumn(key="shift", header="Turno", width_ratio=1.4, align="center"),
        ReportTableColumn(key="exam_title", header="Prova / Simulado", width_ratio=3.2, align="left"),
        ReportTableColumn(key="enrolled_count", header="Matrículas", width_ratio=1.4, align="center", is_numeric=True),
        ReportTableColumn(key="evaluated_count", header="Presentes", width_ratio=1.4, align="center", is_numeric=True),
        ReportTableColumn(key="attendance_rate", header="Freq. (%)", width_ratio=1.4, align="center"),
        ReportTableColumn(key="average_score", header="Média", width_ratio=1.3, align="center", is_numeric=True),
        ReportTableColumn(key="average_percentage", header="% Acerto", width_ratio=1.4, align="center")
    ]
    sec1_rows = rep["classrooms"] if rep["classrooms"] else [{
        "classroom_name": "Nenhuma turma cadastrada",
        "grade_year": "-",
        "shift": "-",
        "exam_title": "-",
        "enrolled_count": 0,
        "evaluated_count": 0,
        "attendance_rate": "-",
        "average_score": "-",
        "average_percentage": "-"
    }]
    sec1 = ReportTableSection(
        title="1. DESEMPENHO DAS TURMAS POR PROVA / SIMULADO",
        columns=sec1_columns,
        rows=sec1_rows,
        subtitle="Métricas de participação, frequência e aproveitamento médio por turma e avaliação"
    )

    # Section 2: Quadro de Honra — 3 Melhores Alunos da Escola
    sec2_columns = [
        ReportTableColumn(key="rank", header="Pos.", width_ratio=1.0, align="center"),
        ReportTableColumn(key="student_name", header="Nome do Estudante", width_ratio=4.0, align="left"),
        ReportTableColumn(key="classroom_name", header="Turma", width_ratio=2.0, align="center"),
        ReportTableColumn(key="grade_year", header="Ano/Série", width_ratio=1.8, align="center"),
        ReportTableColumn(key="exam_title", header="Avaliação de Destaque", width_ratio=3.2, align="left"),
        ReportTableColumn(key="score", header="Nota", width_ratio=1.3, align="center", is_numeric=True),
        ReportTableColumn(key="correct_count", header="Acertos", width_ratio=1.2, align="center", is_numeric=True),
        ReportTableColumn(key="percentage", header="% Acerto", width_ratio=1.4, align="center")
    ]
    sec2_rows = rep["top_overall"] if rep["top_overall"] else [{
        "rank": "-",
        "student_name": "Nenhum estudante avaliado até o momento",
        "classroom_name": "-",
        "grade_year": "-",
        "exam_title": "-",
        "score": "-",
        "correct_count": "-",
        "percentage": "-"
    }]
    sec2 = ReportTableSection(
        title="2. QUADRO DE HONRA — 3 MELHORES ALUNOS DA ESCOLA GERAL",
        columns=sec2_columns,
        rows=sec2_rows,
        subtitle="Estudantes com maiores notas consolidadas em avaliações aplicadas na escola"
    )

    # Section 3: 3 Melhores Alunos por Ano/Série Escolar
    sec3_columns = [
        ReportTableColumn(key="rank", header="Colocação", width_ratio=1.2, align="center"),
        ReportTableColumn(key="grade_year", header="Ano / Série Escolar", width_ratio=2.4, align="center"),
        ReportTableColumn(key="student_name", header="Nome do Estudante", width_ratio=4.0, align="left"),
        ReportTableColumn(key="classroom_name", header="Turma", width_ratio=2.0, align="center"),
        ReportTableColumn(key="exam_title", header="Avaliação", width_ratio=3.0, align="left"),
        ReportTableColumn(key="score", header="Nota", width_ratio=1.3, align="center", is_numeric=True),
        ReportTableColumn(key="percentage", header="% Acerto", width_ratio=1.4, align="center")
    ]
    sec3_rows = rep["top_by_grade"] if rep["top_by_grade"] else [{
        "rank": "-",
        "grade_year": "-",
        "student_name": "Nenhum estudante avaliado por série até o momento",
        "classroom_name": "-",
        "exam_title": "-",
        "score": "-",
        "percentage": "-"
    }]
    sec3 = ReportTableSection(
        title="3. 3 MELHORES ALUNOS POR ANO / SÉRIE ESCOLAR",
        columns=sec3_columns,
        rows=sec3_rows,
        subtitle="Destaques acadêmicos individuais agrupados por série/ano de ensino"
    )

    # Summary KPI cards
    summary_cards = [
        {"label": "Total de Turmas", "value": rep["total_classrooms"]},
        {"label": "Alunos Matriculados", "value": rep["total_enrolled"]},
        {"label": "Provas Corrigidas", "value": rep["total_evaluated"]},
        {"label": "Média Geral Escola", "value": f"{rep['average_score']:.1f}" if rep['total_evaluated'] > 0 else "-"}
    ]

    return ReportData(
        title=f"Relatório de Desempenho Escolar — {sch['name']}",
        metadata=meta,
        columns=sec1_columns,
        rows=sec1_rows,
        summary_cards=summary_cards,
        sections=[sec1, sec2, sec3],
        signatures=["Direção Escolar", "Coordenação Pedagógica"]
    )

# =========================================================================
# REL-07: RELATÓRIO DE TIRAGEM E IMPRESSÃO DE PROVAS (LOGÍSTICA / GRÁFICA)
# =========================================================================

def extract_clean_grade(grade_year: str, classroom_name: str) -> str:
    """Standardizes grade/year string into clean label like '2º ANO' or '9º ANO'."""
    src = (grade_year or "").strip()
    if src.upper() in ["MANHÃ", "TARDE", "NOITE", "INTEGRAL", "MATUTINO", "VESPERTINO"]:
        src = ""
    m = re.search(r'\b([1-9])\s*[º°ªo\.]?\s*ANO\b', src, re.IGNORECASE) or re.search(r'\b([1-9])\s*[º°ªo\.]?\s*ANO\b', classroom_name or "", re.IGNORECASE)
    if m:
        return f"{m.group(1)}º ANO"
    if src:
        return src
    m_spec = re.search(r'\b(EJA|INFANTIL|PRÉ|BERÇÁRIO|CRECHE)\b', classroom_name or "", re.IGNORECASE)
    if m_spec:
        return m_spec.group(1).upper()
    return "GERAL"

def generate_print_run_report_data(school_id: Optional[str] = None, exam_id: Optional[str] = None) -> Optional[ReportData]:
    """Generates the Print Run / Copies Logistics Report for municipal exam printing."""
    raw_data = get_print_run_data(school_id=school_id, exam_id=exam_id)
    if not raw_data:
        return None

    # Resolve School info if single school
    selected_school_name = ""
    if school_id:
        sch = get_school(school_id)
        if sch:
            selected_school_name = sch["name"]

    meta = get_base_metadata(
        school_name=selected_school_name or "REDE MUNICIPAL DE ENSINO",
        exam_title="Planejamento de Tiragem e Impressão de Provas"
    )

    # 1. Process data structures
    distinct_schools = set()
    distinct_classrooms = set()
    classroom_students = {}
    total_copies_all = 0

    by_grade = defaultdict(lambda: defaultdict(int))
    by_school_grade = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    classroom_rows = []

    for r in raw_data:
        s_name = r["school_name"]
        c_id = r["classroom_id"]
        c_name = r["classroom_name"]
        c_shift = r["shift"] or "MANHÃ"
        st_count = int(r["student_count"] or 0)
        e_title = r["exam_title"]
        clean_g = extract_clean_grade(r["grade_year"], c_name)

        distinct_schools.add(s_name)
        distinct_classrooms.add(c_id)
        classroom_students[c_id] = st_count

        by_grade[clean_g][e_title] += st_count
        by_school_grade[s_name][clean_g][e_title] += st_count
        total_copies_all += st_count

        classroom_rows.append({
            "school_name": s_name,
            "classroom_name": c_name,
            "shift": c_shift,
            "grade_year": clean_g,
            "student_count": st_count,
            "exam_title": e_title,
            "copies_needed": st_count
        })

    total_enrolled = sum(classroom_students.values())

    def grade_sort_key(g):
        digits = re.findall(r'\d+', g)
        if digits:
            return (0, int(digits[0]), g)
        return (1, 99, g)

    sorted_grades = sorted(by_grade.keys(), key=grade_sort_key)

    # Section 1: CONSOLIDADO GERAL DA REDE POR ANO / SÉRIE ESCOLAR
    sec1_columns = [
        ReportTableColumn(key="grade_year", header="Ano / Série Escolar", width_ratio=2.5, align="center"),
        ReportTableColumn(key="exam_title", header="Simulado / Avaliação", width_ratio=5.0, align="left"),
        ReportTableColumn(key="copies_needed", header="Qtd. Provas a Imprimir", width_ratio=2.5, align="center", is_numeric=True)
    ]
    sec1_rows = []
    for g in sorted_grades:
        exams_dict = by_grade[g]
        grade_total = 0
        for ex_title, count in sorted(exams_dict.items()):
            sec1_rows.append({
                "grade_year": g,
                "exam_title": ex_title,
                "copies_needed": count
            })
            grade_total += count
        sec1_rows.append({
            "grade_year": f"TOTAL {g}",
            "exam_title": f"Subtotal do {g} (Todas as Provas)",
            "copies_needed": grade_total
        })

    sec1_rows.append({
        "grade_year": "TOTAL GERAL",
        "exam_title": "Consolidado Geral da Rede Municipal",
        "copies_needed": total_copies_all
    })

    sec1 = ReportTableSection(
        title="1. CONSOLIDADO GERAL DA REDE POR ANO / SÉRIE ESCOLAR",
        columns=sec1_columns,
        rows=sec1_rows,
        subtitle="Quantitativo total de cadernos de avaliação a serem impressos por série/ano"
    )

    # Section 2: QUANTITATIVO POR ESCOLA E POR ANO ESCOLAR
    sec2_columns = [
        ReportTableColumn(key="school_name", header="Unidade Escolar", width_ratio=3.5, align="left"),
        ReportTableColumn(key="grade_year", header="Ano / Série", width_ratio=2.0, align="center"),
        ReportTableColumn(key="exam_title", header="Simulado / Avaliação", width_ratio=4.5, align="left"),
        ReportTableColumn(key="copies_needed", header="Cópias", width_ratio=1.8, align="center", is_numeric=True)
    ]
    sec2_rows = []
    for s_name in sorted(by_school_grade.keys()):
        school_grades = by_school_grade[s_name]
        school_total = 0
        for g in sorted(school_grades.keys(), key=grade_sort_key):
            g_exams = school_grades[g]
            g_total = 0
            for ex_title, count in sorted(g_exams.items()):
                sec2_rows.append({
                    "school_name": s_name,
                    "grade_year": g,
                    "exam_title": ex_title,
                    "copies_needed": count
                })
                g_total += count
                school_total += count
            if len(g_exams) > 1:
                sec2_rows.append({
                    "school_name": s_name,
                    "grade_year": f"Subtotal {g}",
                    "exam_title": f"Subtotal do {g} na Escola",
                    "copies_needed": g_total
                })
        sec2_rows.append({
            "school_name": f"TOTAL {s_name}",
            "grade_year": "-",
            "exam_title": "Total da Escola (Todas as Séries e Provas)",
            "copies_needed": school_total
        })

    sec2 = ReportTableSection(
        title="2. QUANTITATIVO POR ESCOLA, ANO ESCOLAR E GABARITO",
        columns=sec2_columns,
        rows=sec2_rows,
        subtitle="Divisão de cópias e cadernos de avaliação por escola e por ano escolar"
    )

    # Section 3: LOGÍSTICA DETALHADA POR TURMA (ENVELOPAMENTO)
    sec3_columns = [
        ReportTableColumn(key="school_name", header="Escola", width_ratio=3.2, align="left"),
        ReportTableColumn(key="classroom_name", header="Turma", width_ratio=2.5, align="left"),
        ReportTableColumn(key="shift", header="Turno", width_ratio=1.5, align="center"),
        ReportTableColumn(key="student_count", header="Alunos", width_ratio=1.3, align="center", is_numeric=True),
        ReportTableColumn(key="exam_title", header="Avaliação Vinculada", width_ratio=3.5, align="left"),
        ReportTableColumn(key="copies_needed", header="Qtd. Envelope", width_ratio=1.6, align="center", is_numeric=True)
    ]
    sec3 = ReportTableSection(
        title="3. LOGÍSTICA DETALHADA POR TURMA (ORGANIZAÇÃO DE ENVELOPES)",
        columns=sec3_columns,
        rows=classroom_rows,
        subtitle="Quantitativo exato de provas por envelope de turma para aplicação em sala"
    )

    summary_cards = [
        {"label": "Escolas Atendidas", "value": len(distinct_schools)},
        {"label": "Turmas Vinculadas", "value": len(distinct_classrooms)},
        {"label": "Alunos Matriculados", "value": total_enrolled},
        {"label": "Total Geral de Cópias", "value": total_copies_all}
    ]

    title_text = "Relatório Oficial de Tiragem e Impressão de Provas"
    if selected_school_name:
        title_text += f" — {selected_school_name}"

    return ReportData(
        title=title_text,
        metadata=meta,
        columns=sec1_columns,
        rows=sec1_rows,
        summary_cards=summary_cards,
        sections=[sec1, sec2, sec3],
        signatures=["Coordenador(a) Geral de Avaliações", "Secretário(a) Municipal de Educação"]
    )


