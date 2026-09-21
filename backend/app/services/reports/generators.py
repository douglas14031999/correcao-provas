from typing import Optional, Dict, Any, List
import os
import re
import math
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

def shorten_exam_name(title: str) -> str:
    """Extracts clean subject/exam name from verbose exam titles to keep tables legible."""
    if not title:
        return "Geral"
    up = title.upper()
    if "LÍNGUA PORTUGUESA" in up or "LINGUA PORTUGUESA" in up or "PORTUGUÊS" in up or "PORTUGUES" in up:
        return "Língua Portuguesa"
    if "MATEMÁTICA" in up or "MATEMATICA" in up:
        return "Matemática"
    if "CIÊNCIAS" in up or "CIENCIAS" in up:
        return "Ciências"
    if "HISTÓRIA" in up or "HISTORIA" in up:
        return "História"
    if "GEOGRAFIA" in up:
        return "Geografia"
    if "INGLÊS" in up or "INGLES" in up:
        return "Inglês"
    cleaned = re.sub(r'^(PROVA\s+[A-Z0-9\s]+[–\-\:]\s*|SIMULADO\s+[A-Z0-9\s]*[–\-\:]\s*)', '', title, flags=re.IGNORECASE).strip()
    return cleaned or title

def generate_print_run_report_data(
    school_id: Optional[str] = None,
    exam_id: Optional[str] = None,
    mode: str = "provas",
    duplex: bool = True
) -> Optional[ReportData]:
    """Generates the Print Run / Copies Logistics Report for municipal exam printing.
    
    Supports:
    - mode="provas": Quantitativo de cadernos/provas por aluno.
    - mode="folhas": Quantitativo detalhado de folhas de papel A4 a serem impressas,
                     considerando páginas por prova e opção Frente/Verso (duplex).
    """
    raw_data = get_print_run_data(school_id=school_id, exam_id=exam_id)
    if not raw_data:
        return None

    is_sheets_mode = (mode == "folhas")
    duplex_label = "Frente e Verso (Duplex)" if duplex else "Só Frente (Simplex)"

    # Resolve School info if single school
    selected_school_name = ""
    if school_id:
        sch = get_school(school_id)
        if sch:
            selected_school_name = sch["name"]

    meta_title = "Planejamento de Tiragem e Impressão de Provas"
    if is_sheets_mode:
        meta_title += f" — Quantitativo Detalhado de Folhas ({duplex_label})"

    meta = get_base_metadata(
        school_name=selected_school_name or "REDE MUNICIPAL DE ENSINO",
        exam_title=meta_title
    )

    # 1. Structure data by Classroom, Grade and School
    classrooms_dict = {}
    distinct_schools = set()
    total_copies_all = 0
    total_sheets_all = 0

    # Intermediate buckets
    by_grade = defaultdict(lambda: {"students": 0, "classrooms": set(), "exams": defaultdict(lambda: {"copies": 0, "pages": 1, "sheets_per_exam": 1, "sheets": 0})})
    by_school_grade = defaultdict(lambda: defaultdict(lambda: {"students": 0, "classrooms": set(), "exams": defaultdict(lambda: {"copies": 0, "pages": 1, "sheets_per_exam": 1, "sheets": 0})}))

    # First pass: map distinct classrooms and their student counts
    for r in raw_data:
        c_id = r["classroom_id"]
        s_name = r["school_name"]
        c_name = r["classroom_name"]
        c_shift = r["shift"] or "MANHÃ"
        st_count = int(r["student_count"] or 0)
        e_title = r["exam_title"]
        clean_g = extract_clean_grade(r["grade_year"], c_name)
        short_e = shorten_exam_name(e_title)
        p_count = max(1, int(r.get("page_count") or 1))

        if duplex:
            sheets_per_copy = max(1, math.ceil(p_count / 2))
        else:
            sheets_per_copy = max(1, p_count)

        row_sheets = st_count * sheets_per_copy

        distinct_schools.add(s_name)

        if c_id not in classrooms_dict:
            classrooms_dict[c_id] = {
                "school_name": s_name,
                "classroom_name": c_name,
                "shift": c_shift,
                "grade_year": clean_g,
                "student_count": st_count,
                "exams": []
            }

        classrooms_dict[c_id]["exams"].append({
            "title": short_e,
            "full_title": e_title,
            "copies": st_count,
            "pages": p_count,
            "sheets_per_exam": sheets_per_copy,
            "sheets": row_sheets
        })

        by_grade[clean_g]["exams"][short_e]["copies"] += st_count
        by_grade[clean_g]["exams"][short_e]["pages"] = p_count
        by_grade[clean_g]["exams"][short_e]["sheets_per_exam"] = sheets_per_copy
        by_grade[clean_g]["exams"][short_e]["sheets"] += row_sheets

        by_school_grade[s_name][clean_g]["exams"][short_e]["copies"] += st_count
        by_school_grade[s_name][clean_g]["exams"][short_e]["pages"] = p_count
        by_school_grade[s_name][clean_g]["exams"][short_e]["sheets_per_exam"] = sheets_per_copy
        by_school_grade[s_name][clean_g]["exams"][short_e]["sheets"] += row_sheets

        total_copies_all += st_count
        total_sheets_all += row_sheets

    # Calculate real non-duplicated student counts
    for c_id, c_data in classrooms_dict.items():
        g = c_data["grade_year"]
        s = c_data["school_name"]
        st = c_data["student_count"]

        by_grade[g]["students"] += st
        by_grade[g]["classrooms"].add(c_id)

        by_school_grade[s][g]["students"] += st
        by_school_grade[s][g]["classrooms"].add(c_id)

    total_enrolled = sum(c["student_count"] for c in classrooms_dict.values())

    def grade_sort_key(g):
        digits = re.findall(r'\d+', g)
        if digits:
            return (0, int(digits[0]), g)
        return (1, 99, g)

    sorted_grades = sorted(by_grade.keys(), key=grade_sort_key)

    # -------------------------------------------------------------------------
    # Section 1: CONSOLIDADO GERAL DA REDE POR ANO / SÉRIE ESCOLAR
    # -------------------------------------------------------------------------
    if is_sheets_mode:
        sec1_columns = [
            ReportTableColumn(key="grade_year", header="Ano / Série Escolar", width_ratio=2.0, align="center"),
            ReportTableColumn(key="student_count", header="Qtd. Alunos", width_ratio=1.3, align="center", is_numeric=True),
            ReportTableColumn(key="exams_breakdown", header=f"Detalhamento das Provas e Folhas ({duplex_label})", width_ratio=5.2, align="left"),
            ReportTableColumn(key="total_copies", header="Total Provas", width_ratio=1.5, align="center", is_numeric=True),
            ReportTableColumn(key="total_sheets", header="Total Folhas", width_ratio=1.8, align="center", is_numeric=True)
        ]
    else:
        sec1_columns = [
            ReportTableColumn(key="grade_year", header="Ano / Série Escolar", width_ratio=2.2, align="center"),
            ReportTableColumn(key="student_count", header="Qtd. Alunos", width_ratio=1.5, align="center", is_numeric=True),
            ReportTableColumn(key="exams_breakdown", header="Detalhamento das Avaliações (Cadernos)", width_ratio=5.5, align="left"),
            ReportTableColumn(key="total_copies", header="Total de Provas", width_ratio=2.0, align="center", is_numeric=True)
        ]

    sec1_rows = []
    for g in sorted_grades:
        g_info = by_grade[g]
        exams_items = g_info["exams"]

        if is_sheets_mode:
            breakdown_parts = [
                f"{ex_name}: {info['copies']} prov. × {info['pages']} pág. ({info['sheets_per_exam']} fl{'s' if info['sheets_per_exam'] > 1 else ''}) = {info['sheets']} fls"
                for ex_name, info in sorted(exams_items.items())
            ]
            grade_total_copies = sum(info["copies"] for info in exams_items.values())
            grade_total_sheets = sum(info["sheets"] for info in exams_items.values())
            sec1_rows.append({
                "grade_year": g,
                "student_count": g_info["students"],
                "exams_breakdown": "  •  ".join(breakdown_parts),
                "total_copies": grade_total_copies,
                "total_sheets": grade_total_sheets
            })
        else:
            breakdown_parts = [f"{ex_name}: {info['copies']} cópias" for ex_name, info in sorted(exams_items.items())]
            grade_total_copies = sum(info["copies"] for info in exams_items.values())
            sec1_rows.append({
                "grade_year": g,
                "student_count": g_info["students"],
                "exams_breakdown": "  •  ".join(breakdown_parts),
                "total_copies": grade_total_copies
            })

    total_row_sec1 = {
        "grade_year": "TOTAL GERAL DA REDE",
        "student_count": total_enrolled,
        "exams_breakdown": "Consolidado de todas as séries e avaliações da rede municipal",
        "total_copies": total_copies_all
    }
    if is_sheets_mode:
        total_row_sec1["total_sheets"] = total_sheets_all
    sec1_rows.append(total_row_sec1)

    sec1_subtitle = "Quantitativo total de folhas de papel a serem impressas por série/ano" if is_sheets_mode else "Quantitativo total de cadernos de avaliação a serem impressos por série/ano"
    sec1 = ReportTableSection(
        title="1. CONSOLIDADO GERAL DA REDE POR ANO / SÉRIE ESCOLAR",
        columns=sec1_columns,
        rows=sec1_rows,
        subtitle=sec1_subtitle
    )

    # -------------------------------------------------------------------------
    # Section 2: QUANTITATIVO POR ESCOLA E ANO ESCOLAR
    # -------------------------------------------------------------------------
    if is_sheets_mode:
        sec2_columns = [
            ReportTableColumn(key="school_name", header="Unidade Escolar", width_ratio=3.2, align="left"),
            ReportTableColumn(key="grade_year", header="Ano / Série", width_ratio=1.6, align="center"),
            ReportTableColumn(key="student_count", header="Alunos", width_ratio=1.2, align="center", is_numeric=True),
            ReportTableColumn(key="exams_breakdown", header=f"Detalhamento de Folhas ({duplex_label})", width_ratio=4.5, align="left"),
            ReportTableColumn(key="total_copies", header="Provas", width_ratio=1.4, align="center", is_numeric=True),
            ReportTableColumn(key="total_sheets", header="Total Folhas", width_ratio=1.8, align="center", is_numeric=True)
        ]
    else:
        sec2_columns = [
            ReportTableColumn(key="school_name", header="Unidade Escolar", width_ratio=3.8, align="left"),
            ReportTableColumn(key="grade_year", header="Ano / Série", width_ratio=1.8, align="center"),
            ReportTableColumn(key="student_count", header="Alunos", width_ratio=1.4, align="center", is_numeric=True),
            ReportTableColumn(key="exams_breakdown", header="Detalhamento das Provas e Cópias", width_ratio=4.5, align="left"),
            ReportTableColumn(key="total_copies", header="Total Cópias", width_ratio=1.8, align="center", is_numeric=True)
        ]

    sec2_rows = []
    for s_name in sorted(by_school_grade.keys()):
        school_grades = by_school_grade[s_name]
        sorted_school_g = sorted(school_grades.keys(), key=grade_sort_key)
        school_total_copies = 0
        school_total_sheets = 0
        school_total_students = 0

        for idx, g in enumerate(sorted_school_g):
            sg_info = school_grades[g]
            sg_exams = sg_info["exams"]
            g_copies = sum(info["copies"] for info in sg_exams.values())
            g_sheets = sum(info["sheets"] for info in sg_exams.values())
            school_total_copies += g_copies
            school_total_sheets += g_sheets
            school_total_students += sg_info["students"]

            display_school = s_name if idx == 0 else ""

            if is_sheets_mode:
                breakdown_parts = [
                    f"{ex_name}: {info['copies']}p ({info['sheets']} fls)"
                    for ex_name, info in sorted(sg_exams.items())
                ]
                sec2_rows.append({
                    "school_name": display_school,
                    "grade_year": g,
                    "student_count": sg_info["students"],
                    "exams_breakdown": "  •  ".join(breakdown_parts),
                    "total_copies": g_copies,
                    "total_sheets": g_sheets
                })
            else:
                breakdown_parts = [f"{ex_name}: {info['copies']}" for ex_name, info in sorted(sg_exams.items())]
                sec2_rows.append({
                    "school_name": display_school,
                    "grade_year": g,
                    "student_count": sg_info["students"],
                    "exams_breakdown": "  •  ".join(breakdown_parts),
                    "total_copies": g_copies
                })

        # Subtotal per school
        if len(sorted_school_g) > 1:
            subtotal_row = {
                "school_name": f"SUBTOTAL {s_name}",
                "grade_year": f"{len(sorted_school_g)} séries",
                "student_count": school_total_students,
                "exams_breakdown": "Total consolidado desta unidade escolar",
                "total_copies": school_total_copies
            }
            if is_sheets_mode:
                subtotal_row["total_sheets"] = school_total_sheets
            sec2_rows.append(subtotal_row)

    total_row_sec2 = {
        "school_name": "TOTAL GERAL DE TODAS AS ESCOLAS",
        "grade_year": "-",
        "student_count": total_enrolled,
        "exams_breakdown": "Consolidado geral da rede municipal de ensino",
        "total_copies": total_copies_all
    }
    if is_sheets_mode:
        total_row_sec2["total_sheets"] = total_sheets_all
    sec2_rows.append(total_row_sec2)

    sec2_subtitle = "Divisão de folhas e cadernos de avaliação por escola e por ano escolar" if is_sheets_mode else "Divisão de cópias e cadernos de avaliação por escola e por ano escolar"
    sec2 = ReportTableSection(
        title="2. QUANTITATIVO POR ESCOLA E ANO ESCOLAR",
        columns=sec2_columns,
        rows=sec2_rows,
        subtitle=sec2_subtitle
    )

    # -------------------------------------------------------------------------
    # Section 3: LOGÍSTICA DETALHADA POR TURMA (ORGANIZAÇÃO DE ENVELOPES)
    # -------------------------------------------------------------------------
    if is_sheets_mode:
        sec3_columns = [
            ReportTableColumn(key="school_name", header="Escola", width_ratio=3.0, align="left"),
            ReportTableColumn(key="classroom_name", header="Turma", width_ratio=2.2, align="left"),
            ReportTableColumn(key="shift", header="Turno", width_ratio=1.3, align="center"),
            ReportTableColumn(key="grade_year", header="Série", width_ratio=1.4, align="center"),
            ReportTableColumn(key="student_count", header="Alunos", width_ratio=1.1, align="center", is_numeric=True),
            ReportTableColumn(key="envelope_content", header=f"Conteúdo do Envelope ({duplex_label})", width_ratio=4.5, align="left"),
            ReportTableColumn(key="total_envelope", header="Provas", width_ratio=1.3, align="center", is_numeric=True),
            ReportTableColumn(key="total_sheets", header="Total Folhas", width_ratio=1.7, align="center", is_numeric=True)
        ]
    else:
        sec3_columns = [
            ReportTableColumn(key="school_name", header="Escola", width_ratio=3.2, align="left"),
            ReportTableColumn(key="classroom_name", header="Turma", width_ratio=2.4, align="left"),
            ReportTableColumn(key="shift", header="Turno", width_ratio=1.4, align="center"),
            ReportTableColumn(key="grade_year", header="Série", width_ratio=1.6, align="center"),
            ReportTableColumn(key="student_count", header="Alunos", width_ratio=1.2, align="center", is_numeric=True),
            ReportTableColumn(key="envelope_content", header="Conteúdo do Envelope (Cadernos)", width_ratio=4.4, align="left"),
            ReportTableColumn(key="total_envelope", header="Total Envelope", width_ratio=1.8, align="center", is_numeric=True)
        ]

    sec3_rows = []
    sorted_classrooms = sorted(
        classrooms_dict.values(),
        key=lambda c: (c["school_name"], grade_sort_key(c["grade_year"]), c["classroom_name"])
    )

    for c in sorted_classrooms:
        st_count = c["student_count"]
        total_env = st_count * len(c["exams"])

        if is_sheets_mode:
            parts = [
                f"{st_count}x {ex['title']} ({ex['sheets']} fls)"
                for ex in c["exams"]
            ]
            class_total_sheets = sum(ex["sheets"] for ex in c["exams"])
            sec3_rows.append({
                "school_name": c["school_name"],
                "classroom_name": c["classroom_name"],
                "shift": c["shift"],
                "grade_year": c["grade_year"],
                "student_count": st_count,
                "envelope_content": "  •  ".join(parts),
                "total_envelope": total_env,
                "total_sheets": class_total_sheets
            })
        else:
            parts = [f"{st_count}x {ex['title']}" for ex in c["exams"]]
            sec3_rows.append({
                "school_name": c["school_name"],
                "classroom_name": c["classroom_name"],
                "shift": c["shift"],
                "grade_year": c["grade_year"],
                "student_count": st_count,
                "envelope_content": "  •  ".join(parts),
                "total_envelope": total_env
            })

    total_row_sec3 = {
        "school_name": "TOTAL GERAL DE ENVELOPES",
        "classroom_name": f"{len(classrooms_dict)} turmas",
        "shift": "-",
        "grade_year": "-",
        "student_count": total_enrolled,
        "envelope_content": "Total de cadernos organizados para envelopamento",
        "total_envelope": total_copies_all
    }
    if is_sheets_mode:
        total_row_sec3["total_sheets"] = total_sheets_all
    sec3_rows.append(total_row_sec3)

    sec3 = ReportTableSection(
        title="3. LOGÍSTICA DETALHADA POR TURMA (ORGANIZAÇÃO DE ENVELOPES)",
        columns=sec3_columns,
        rows=sec3_rows,
        subtitle="Quantitativo exato de provas e folhas por envelope de turma para aplicação em sala"
    )

    if is_sheets_mode:
        estimated_reams = math.ceil(total_sheets_all / 500)
        summary_cards = [
            {"label": "Escolas Atendidas", "value": len(distinct_schools)},
            {"label": "Turmas Vinculadas", "value": len(classrooms_dict)},
            {"label": "Total de Provas", "value": f"{total_copies_all:,}".replace(",", ".")},
            {"label": "Total de Folhas", "value": f"{total_sheets_all:,}".replace(",", ".")},
            {"label": "Resmas A4 (~500 fls)", "value": f"{estimated_reams} ({duplex_label})"}
        ]
    else:
        summary_cards = [
            {"label": "Escolas Atendidas", "value": len(distinct_schools)},
            {"label": "Turmas Vinculadas", "value": len(classrooms_dict)},
            {"label": "Alunos Matriculados", "value": total_enrolled},
            {"label": "Total Geral de Cópias", "value": total_copies_all}
        ]

    title_text = "Relatório Oficial de Tiragem e Impressão de Provas"
    if is_sheets_mode:
        title_text += f" — Detalhamento de Folhas ({duplex_label})"
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


