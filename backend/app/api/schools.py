import os
import csv
import io
import unicodedata
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Query, Header
from fastapi.responses import StreamingResponse

from app.services.database import (
    get_or_create_school,
    get_school,
    delete_school,
    delete_classroom,
    get_or_create_classroom,
    get_or_create_student,
    list_schools_tree,
    get_classroom_with_details,
    get_classroom_report,
    compare_classroom_exams,
    get_exam,
    link_exams_to_classroom,
    get_classroom_exams,
    update_classroom
)
from app.services.pdf_generator import generate_batch_classroom_pdf, generate_envelope_labels_pdf, DEFAULT_LOGO_PATH
from app.api.auth import require_roles

router = APIRouter(tags=["Escolas e Turmas"])

class CreateSchoolRequest(BaseModel):
    name: str
    inep_code: Optional[str] = ""

class UpdateClassroomRequest(BaseModel):
    name: Optional[str] = None
    shift: Optional[str] = None
    grade_year: Optional[str] = None

class LinkExamsRequest(BaseModel):
    exam_ids: List[str]

def sanitize_header_filename(name: str) -> str:
    """Sanitizes filename for HTTP Content-Disposition headers (strictly ASCII)."""
    if not name:
        return "arquivo"
    nfkd = unicodedata.normalize('NFKD', str(name))
    ascii_name = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    import re
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', ascii_name)
    return re.sub(r'_+', '_', clean).strip('_')

def normalize_key(s: str) -> str:
    """Normalizes header string: fixes mojibake, strips accents, lowers case, trims."""
    if not s:
        return ""
    s = s.replace("\ufeff", "").strip()
    # Fix potential UTF-8 double-encoding/mojibake (e.g. CÃ³digo -> Código)
    try:
        if "Ã" in s or "Ã³" in s or "Â" in s:
            s = s.encode("latin-1").decode("utf-8")
    except Exception:
        pass
    nfkd = unicodedata.normalize('NFKD', s)
    ascii_str = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return ascii_str.strip().lower().replace("\ufeff", "").replace("_", "").replace(" ", "").replace("-", "")

@router.get("/schools")
def list_all_schools():
    """Lists all schools with their classrooms and student counts."""
    return list_schools_tree()

@router.get("/schools/{school_id}/envelope-labels-pdf")
def download_school_envelope_labels_pdf(school_id: str, classroom_id: Optional[str] = Query(None)):
    """
    Gera e faz download do PDF de etiquetas de envelope (grade 4x1) para as turmas de uma escola.
    Pode gerar para uma turma específica (se classroom_id informado) ou para todas as turmas da escola.
    """
    school = get_school(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada.")

    schools_tree = list_schools_tree()
    target_sch = next((s for s in schools_tree if str(s["id"]) == str(school_id)), None)

    classrooms = target_sch.get("classrooms", []) if target_sch else []
    if not classrooms:
        raise HTTPException(status_code=400, detail="Esta escola não possui turmas cadastradas para geração de etiquetas.")

    school_name = (school.get("name") or "Escola").strip()

    if classroom_id:
        target_cl = next((c for c in classrooms if str(c.get("id")) == str(classroom_id)), None)
        if not target_cl:
            raise HTTPException(status_code=404, detail="Turma não encontrada nesta escola.")
        classrooms = [target_cl]
        raw_filename = f"{target_cl.get('name', 'Turma')} - Etiquetas - {school_name}.pdf"
    elif len(classrooms) == 1:
        raw_filename = f"{classrooms[0].get('name', 'Turma')} - Etiquetas - {school_name}.pdf"
    else:
        raw_filename = f"Turmas - Etiquetas - {school_name}.pdf"

    pdf_bytes = generate_envelope_labels_pdf(
        school=target_sch or school,
        classrooms=classrooms
    )

    safe_name = sanitize_header_filename(raw_filename[:-4]) + ".pdf"
    import urllib.parse
    encoded_filename = urllib.parse.quote(raw_filename)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"; filename*=UTF-8\'\'{encoded_filename}'
        }
    )

@router.post("/schools")
def create_school_manual(req: CreateSchoolRequest, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Creates a new school manually."""
    require_roles(["admin", "coordenador"], authorization, x_auth_token)
    if not req.name or not req.name.strip():
        raise HTTPException(status_code=400, detail="Nome da escola é obrigatório.")
    return get_or_create_school(req.name.strip(), inep_code=req.inep_code or "")

@router.delete("/schools/{school_id}")
def remove_school(school_id: str, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Deletes a school and cascades to its classrooms and students."""
    require_roles(["admin"], authorization, x_auth_token)
    success = delete_school(school_id)
    if not success:
        raise HTTPException(status_code=404, detail="Escola não encontrada.")
    return {"success": True, "message": "Escola removida com sucesso."}

@router.delete("/classrooms/{classroom_id}")
def remove_classroom(classroom_id: str, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Deletes a classroom and its students."""
    require_roles(["admin"], authorization, x_auth_token)
    success = delete_classroom(classroom_id)
    if not success:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return {"success": True, "message": "Turma removida com sucesso."}

@router.put("/classrooms/{classroom_id}")
@router.patch("/classrooms/{classroom_id}")
def edit_classroom(classroom_id: str, req: UpdateClassroomRequest, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Updates classroom details such as name, shift, and grade_year."""
    require_roles(["admin", "coordenador"], authorization, x_auth_token)
    updated = update_classroom(
        classroom_id=classroom_id,
        name=req.name,
        shift=req.shift,
        grade_year=req.grade_year
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return updated


@router.get("/classrooms/{classroom_id}")
def get_classroom(classroom_id: str):
    """Gets details for a classroom including student list and linked exams."""
    classroom = get_classroom_with_details(classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    return classroom

@router.get("/classrooms/{classroom_id}/exams")
def get_exams_linked_to_classroom(classroom_id: str):
    """Returns the list of exams linked to a classroom."""
    classroom = get_classroom_with_details(classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return get_classroom_exams(classroom_id)

@router.post("/classrooms/{classroom_id}/exams")
def set_exams_linked_to_classroom(classroom_id: str, req: LinkExamsRequest):
    """Updates the list of exams linked to a classroom."""
    classroom = get_classroom_with_details(classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    try:
        saved_ids = link_exams_to_classroom(classroom_id, req.exam_ids)
        return {"success": True, "linked_exam_ids": saved_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar gabaritos vinculados: {str(e)}")

@router.get("/students/csv-template")
def download_csv_template(etapa: Optional[str] = Query(None)):
    """Downloads a sample CSV file demonstrating the expected format with Ano Escolar."""
    if etapa in ["fundamental2", "fund2", "6-9", "anosfinais"]:
        csv_content = (
            "Código da Turma;Turma;Ano Escolar;Turno;Matrícula;Estudante\n"
            "TURMA6A;6º ANO A;6º ANO;MANHÃ;20260601;ANA CLARA DOS SANTOS\n"
            "TURMA6A;6º ANO A;6º ANO;MANHÃ;20260602;BRUNO GABRIEL RODRIGUES\n"
            "TURMA6B;6º ANO B;6º ANO;TARDE;20260603;CAIO VINICIUS ALMEIDA\n"
            "TURMA7A;7º ANO A;7º ANO;MANHÃ;20260701;DANIEL ALVES FERREIRA\n"
            "TURMA7B;7º ANO B;7º ANO;TARDE;20260702;EDUARDA SILVA PEREIRA\n"
            "TURMA8A;8º ANO A;8º ANO;MANHÃ;20260801;FELIPE AUGUSTO DE SOUZA\n"
            "TURMA8B;8º ANO B;8º ANO;TARDE;20260802;GABRIELA LIMA DOS REIS\n"
            "TURMA9A;9º ANO A;9º ANO;MANHÃ;20260901;HEITOR BARBOSA NETO\n"
            "TURMA9B;9º ANO B;9º ANO;TARDE;20260902;ISABELA BEZERRA DIAS\n"
        )
        filename = "modelo_fundamental_2_6_ao_9_ano.csv"
    else:
        csv_content = (
            "Código da Turma;Turma;Ano Escolar;Estudante\n"
            "e2iv8e17d526;turma 1 Aline;1º ANO;ENZO GABRIEL IZIDORO DANTAS\n"
            "e2iv8e17d526;turma 1 Aline;1º ANO;LARIELY HENRIQUE DE MELO\n"
            "e2iv8e17d526;turma 1 Aline;1º ANO;LAÍSE GABRIELLY BEZERRA DE OLIVEIRA\n"
            "e2iv8e17d526;turma 1 Aline;2º ANO;LUIZ LORENZO PADILHA MENDES\n"
            "e2iv8e17d526;turma 1 Aline;2º ANO;MARIA CECÍLIA ALVES DA SILVA\n"
        )
        filename = "modelo_importacao_alunos.csv"

    # UTF-8 BOM so Excel opens with proper accents
    bom_content = "\ufeff" + csv_content
    return Response(
        content=bom_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post("/students/import-csv")
async def import_students_csv(
    file: UploadFile = File(...),
    school_id: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None)
):
    """
    Imports students and classrooms from a CSV file.
    Can be assigned to a specific manually created school (via school_id).
    Supports specific columns: "Código da Turma", "Turma", and "Estudante".
    """
    require_roles(["admin", "coordenador"], authorization, x_auth_token)
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Arquivo CSV vazio.")
        
    # Decode bytes
    text = ""
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            text = contents.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
            
    if not text:
        raise HTTPException(status_code=400, detail="Não foi possível decodificar o arquivo CSV.")
        
    # Detect delimiter
    first_line = text.strip().split("\n")[0] if text else ""
    delimiter = ";" if ";" in first_line else ","
    if "\t" in first_line and "\t" not in first_line.replace("\t", ""):
        delimiter = "\t"
        
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    
    # Map header fields (com suporte ampliado para CNCA, CAEd, SGE e Censo)
    field_map = {}
    for raw_header in reader.fieldnames or []:
        norm = normalize_key(raw_header)
        if norm in ["codigodaturma", "codturma", "codigoturma", "turmacodigo", "idturma", "cdturma", "id_turma"]:
            field_map[raw_header] = "class_code"
        elif norm in ["turma", "classe", "nomedaturma", "nometurma", "identificacaodaturma", "turmaturno", "dsturma"]:
            field_map[raw_header] = "classroom"
        elif norm in ["estudante", "aluno", "nome", "nomedoestudante", "nomedoaluno", "estudantes", "alunos", "nomeestudante", "nomealuno", "noaluno", "nmaluno", "nomecompleto"]:
            field_map[raw_header] = "student_name"
        elif norm in ["anoescolar", "ano", "grau", "serie", "anoetapa", "etapadeensino", "etapa", "series", "anodeescolaridade", "anodeensino", "anoensino", "dsetapa", "nuano", "anoserie", "escolaridade"]:
            field_map[raw_header] = "grade_year"
        elif norm in ["turno", "periodo", "horario", "dsturno", "turnodefuncionamento"]:
            field_map[raw_header] = "shift"
        elif norm in ["matricula", "id", "registro", "codigo", "ra", "codigodoaluno", "codigodoestudante", "iddoestudante", "idaluno", "cdaluno", "idestudante"]:
            field_map[raw_header] = "registration"
        elif norm in ["escola", "escolanome", "nomedaescola", "colegio", "unidade", "nomedainstituicao", "instituicaodeensino", "cdescola", "noescola", "nomeescola", "instituicao", "inep"]:
            field_map[raw_header] = "school"
            
    selected_school = None
    if school_id and isinstance(school_id, str) and school_id.strip():
        selected_school = get_school(school_id.strip())

    schools_cache = {}
    if selected_school:
        schools_cache[selected_school["id"]] = selected_school
        
    classrooms_cache = {}
    imported_count = 0
    skipped_count = 0
    
    for row in reader:
        school_name = selected_school["name"] if selected_school else "Escola Municipal"
        classroom_name = "Turma Geral"
        shift = "(  ) MANHÃ       (  ) TARDE"
        student_name = ""
        registration = ""
        class_code = ""
        grade_year = ""
        
        for raw_k, v in row.items():
            if not v:
                continue
            val = str(v).strip()
            mapped = field_map.get(raw_k)
            if mapped == "school" and not selected_school and val:
                school_name = val
            elif mapped == "classroom" and val:
                classroom_name = val
            elif mapped == "class_code" and val:
                class_code = val
            elif mapped == "student_name" and val:
                student_name = val
            elif mapped == "grade_year" and val:
                grade_year = val
            elif mapped == "shift" and val:
                shift = val
            elif mapped == "registration" and val:
                registration = val

        if not student_name:
            skipped_count += 1
            continue
            
        # Target school
        if selected_school:
            target_school = selected_school
        else:
            if school_name not in schools_cache:
                schools_cache[school_name] = get_or_create_school(school_name)
            target_school = schools_cache[school_name]
        
        # Target classroom under this school - uniquely identified by (school, name, grade_year)
        effective_grade = grade_year if grade_year else class_code
        class_key = (target_school["id"], classroom_name, effective_grade)
        if class_key not in classrooms_cache:
            classrooms_cache[class_key] = get_or_create_classroom(
                target_school["id"], 
                classroom_name, 
                grade_year=effective_grade, 
                shift=shift
            )
        classroom = classrooms_cache[class_key]
        
        # Target student (use class_code as registration if no individual matricula given)
        student_reg = registration or class_code
        get_or_create_student(
            classroom_id=classroom["id"], 
            name=student_name, 
            registration=student_reg,
            school_id=target_school["id"]
        )
        imported_count += 1
        
    return {
        "success": True,
        "imported_students": imported_count,
        "skipped_rows": skipped_count,
        "school_id": selected_school["id"] if selected_school else None,
        "school_name": selected_school["name"] if selected_school else None,
        "classrooms_count": len(classrooms_cache)
    }

@router.get("/classrooms/{classroom_id}/exams/{exam_id}/batch-pdf")
@router.get("/classrooms/{classroom_id}/batch-pdf")
def download_classroom_batch_pdf(
    classroom_id: str,
    exam_id: str = "both",
    layout: str = Query("double", description="'single' or 'double'")
):
    """
    Generates a merged PDF containing personalized answer sheets for EVERY student in the classroom.
    If exam_id is 'both', 'all', or 'linked' (or when 2 exams are linked and layout is 'double'):
    Emits both exams. In 2-per-page mode, each student receives BOTH exams on a single sheet:
    Exam 1 on top half and Exam 2 on bottom half.
    """
    classroom = get_classroom_with_details(classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
        
    students = classroom.get("students", [])
    if not students:
        raise HTTPException(status_code=400, detail="A turma não possui alunos cadastrados.")
        
    sheets_per_page = 2 if (layout == "double" or layout == "2") else 1
    linked_exams = classroom.get("linked_exams", [])

    school_name = (classroom.get("school_name") or "").strip()
    if not school_name and classroom.get("school_id"):
        sch = get_school(classroom["school_id"])
        if sch:
            school_name = (sch.get("name") or "").strip()

    class_name = (classroom.get("name") or "Turma").strip()
    if school_name and class_name:
        filename = f"{class_name} - GABARITOS - {school_name}.pdf"
    elif class_name:
        filename = f"{class_name} - GABARITOS.pdf"
    elif school_name:
        filename = f"GABARITOS - {school_name}.pdf"
    else:
        filename = "GABARITOS.pdf"

    exams_to_render = []

    if exam_id in ["both", "all", "linked"] or (len(linked_exams) == 2 and exam_id == "both"):
        if not linked_exams:
            raise HTTPException(status_code=400, detail="Esta turma não possui simulados vinculados.")
        for le in linked_exams:
            full_ex = get_exam(le["id"])
            if full_ex:
                exams_to_render.append(full_ex)
    else:
        exam = get_exam(exam_id)
        if not exam:
            # Fallback if linked_exams exist
            if linked_exams:
                for le in linked_exams:
                    full_ex = get_exam(le["id"])
                    if full_ex:
                        exams_to_render.append(full_ex)
            if not exams_to_render:
                raise HTTPException(status_code=404, detail="Simulado não encontrado")
        else:
            exams_to_render = [exam]

    pdf_bytes = generate_batch_classroom_pdf(
        exam=exams_to_render[0] if exams_to_render else None,
        classroom=classroom,
        students=students,
        sheets_per_page=sheets_per_page,
        exams=exams_to_render if len(exams_to_render) > 1 else None
    )
    
    import urllib.parse
    ascii_clean = sanitize_header_filename(filename.replace(".pdf", ""))
    safe_ascii = f"{ascii_clean}.pdf"
    encoded_filename = urllib.parse.quote(filename)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded_filename}'
        }
    )

@router.get("/classrooms/{classroom_id}/exams/{exam_id}/report")
def get_classroom_exam_report(classroom_id: str, exam_id: str):
    """Returns structured report data for the classroom on a specific exam."""
    report = get_classroom_report(classroom_id, exam_id)
    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return report

@router.get("/classrooms/{classroom_id}/exams/{exam_id}/report/csv")
def export_classroom_exam_report_csv(classroom_id: str, exam_id: str):
    """Exports classroom exam results as a CSV spreadsheet."""
    report = get_classroom_report(classroom_id, exam_id)
    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
        
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    
    # Headers
    writer.writerow([
        "Posicao", "Matricula", "Nome do Aluno", "Nota", "Nota Maxima",
        "Aproveitamento (%)", "Acertos", "Erros", "Brancos", "Duplas", "Status"
    ])
    
    rank = 1
    default_max = report["exam"].get("max_score", float(report["exam"].get("num_questions", 20)) * float(report["exam"].get("points_per_question", 1.0)))
    for st in report.get("student_results", []):
        sub = st.get("submission")
        if sub:
            status = "Corrigido"
            score = sub.get("score", 0)
            max_s = sub.get("max_score", default_max)
            pct = round((score / max(1.0, max_s)) * 100, 1) if max_s else 0
            correct = sub.get("correct_count", 0)
            wrong = sub.get("wrong_count", 0)
            blank = sub.get("blank_count", 0)
            double = sub.get("double_count", 0)
        else:
            status = "Pendente"
            score = "-"
            max_s = default_max
            pct = "-"
            correct = "-"
            wrong = "-"
            blank = "-"
            double = "-"
            
        writer.writerow([
            rank if sub else "-",
            st.get("registration", ""),
            st.get("name", ""),
            score,
            max_s,
            f"{pct}%" if pct != "-" else "-",
            correct,
            wrong,
            blank,
            double,
            status
        ])
        if sub:
            rank += 1
            
    csv_data = "\ufeff" + output.getvalue()
    safe_class = sanitize_header_filename(report["classroom"]["name"])
    return Response(
        content=csv_data.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="Relatorio_Turma_{safe_class}.csv"'}
    )


@router.get("/classrooms/{classroom_id}/compare")
def get_classroom_exams_comparison(classroom_id: str, exam1: str = Query(...), exam2: str = Query(...)):
    """Returns side-by-side comparison analytics between two exams for a classroom."""
    comp = compare_classroom_exams(classroom_id, exam1, exam2)
    if not comp:
        raise HTTPException(status_code=404, detail="Dados comparativos não encontrados.")
    return comp


@router.get("/classrooms/{classroom_id}/compare/csv")
def export_classroom_exams_comparison_csv(classroom_id: str, exam1: str = Query(...), exam2: str = Query(...)):
    """Exports classroom comparison results as a CSV spreadsheet."""
    comp = compare_classroom_exams(classroom_id, exam1, exam2)
    if not comp:
        raise HTTPException(status_code=404, detail="Dados comparativos não encontrados.")
        
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    
    ex1_title = comp["exam1"]["title"]
    ex2_title = comp["exam2"]["title"]
    
    # Header
    writer.writerow([
        "Matricula", "Nome do Aluno",
        f"Nota ({ex1_title})", f"Acertos ({ex1_title})", f"Status ({ex1_title})",
        f"Nota ({ex2_title})", f"Acertos ({ex2_title})", f"Status ({ex2_title})",
        "Media Combinada", "Diferenca (Delta)", "Melhor Desempenho"
    ])
    
    for st in comp.get("students", []):
        delta_str = f"{st['delta']:+0.1f}" if st.get("delta") is not None else "-"
        writer.writerow([
            st.get("registration", ""),
            st.get("name", ""),
            st.get("score1") if st.get("score1") is not None else "-",
            st.get("correct1") if st.get("score1") is not None else "-",
            st.get("status1", "PENDENTE"),
            st.get("score2") if st.get("score2") is not None else "-",
            st.get("correct2") if st.get("score2") is not None else "-",
            st.get("status2", "PENDENTE"),
            st.get("combined_avg") if st.get("combined_avg") is not None else "-",
            delta_str,
            st.get("best_exam", "-")
        ])
        
    csv_data = "\ufeff" + output.getvalue()
    safe_class = sanitize_header_filename(comp["classroom"]["name"])
    return Response(
        content=csv_data.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="Comparativo_Gabaritos_{safe_class}.csv"'}
    )

