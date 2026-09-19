import os
import uuid
import base64
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Response, UploadFile, File, Header
from pydantic import BaseModel, Field

from app.services.database import (
    save_exam, get_exam, list_exams, update_exam, delete_exam,
    get_submissions_by_exam, update_exam_template,
    get_submission, delete_submission, delete_submissions_by_exam,
    get_exam_linked_schools
)
from app.services.pdf_generator import generate_answer_sheet_pdf, DEFAULT_LOGO_PATH
from app.api.auth import require_roles

router = APIRouter(prefix="/api/exams", tags=["Exams"])
submissions_router = APIRouter(prefix="/api/submissions", tags=["Submissions"])

STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage"
)
ASSETS_DIR = os.path.join(STORAGE_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

class CreateExamRequest(BaseModel):
    title: str = Field(..., example="PROVA CANOA 2026 – LÍNGUA PORTUGUESA")
    subtitle: Optional[str] = Field("2º ANO DO ENSINO FUNDAMENTAL", example="2º ANO DO ENSINO FUNDAMENTAL")
    school_name: Optional[str] = Field("", example="E.M.E.F. Monsenhor Clóvis Duarte")
    classroom: Optional[str] = Field("", example="2º ANO A")
    student_name: Optional[str] = Field("", example="")
    shift: Optional[str] = Field("(  ) MANHÃ       (  ) TARDE", example="(  ) MANHÃ       (  ) TARDE")
    logo_base64: Optional[str] = None
    num_questions: int = Field(20, ge=1, le=100)
    num_alternatives: int = Field(4, ge=2, le=5)
    points_per_question: float = Field(1.0, gt=0)
    answer_key: Dict[str, str] = Field(default_factory=dict)
    weights: Optional[Dict[str, float]] = Field(default_factory=dict)
    header_color: Optional[str] = Field("#244061", example="#244061")

@router.post("/upload-logo")
async def upload_logo_file(file: UploadFile = File(...), authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin", "coordenador"], authorization, x_auth_token)
    ext = os.path.splitext(file.filename)[1] or ".png"
    logo_filename = f"custom_logo_{uuid.uuid4().hex[:8]}{ext}"
    logo_save_path = os.path.join(ASSETS_DIR, logo_filename)
    
    contents = await file.read()
    with open(logo_save_path, "wb") as f:
        f.write(contents)
        
    return {
        "success": True,
        "filename": logo_filename,
        "logo_path": logo_save_path,
        "logo_url": f"/storage/assets/{logo_filename}"
    }

@router.post("", status_code=201)
def create_exam(req: CreateExamRequest, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin", "coordenador"], authorization, x_auth_token)
    exam_id = str(uuid.uuid4())
    
    # Process custom logo if sent in base64
    logo_path = None
    if req.logo_base64:
        try:
            b64_data = req.logo_base64
            if "," in b64_data:
                b64_data = b64_data.split(",")[1]
            raw_logo = base64.b64decode(b64_data)
            logo_path = os.path.join(ASSETS_DIR, f"exam_{exam_id[:8]}_logo.png")
            with open(logo_path, "wb") as lf:
                lf.write(raw_logo)
        except Exception as e:
            logo_path = None
            
    if not logo_path and os.path.exists(DEFAULT_LOGO_PATH):
        logo_path = DEFAULT_LOGO_PATH

    # Generate default answer key if empty
    ans_key = req.answer_key
    if not ans_key:
        opts = ["A", "B", "C", "D", "E"][:req.num_alternatives]
        ans_key = {str(i): opts[(i - 1) % len(opts)] for i in range(1, req.num_questions + 1)}
        
    pdf_path = os.path.join(STORAGE_DIR, "sheets", f"exam_{exam_id}.pdf")
    pdf_bytes, template_data = generate_answer_sheet_pdf(
        exam_id=exam_id,
        title=req.title,
        subtitle=req.subtitle or "2º ANO DO ENSINO FUNDAMENTAL",
        school_name=req.school_name or "",
        student_name=req.student_name or "",
        classroom=req.classroom or "",
        shift=req.shift or "(  ) MANHÃ       (  ) TARDE",
        num_questions=req.num_questions,
        num_alternatives=req.num_alternatives,
        logo_path=logo_path,
        output_path=pdf_path,
        header_color=req.header_color or "#244061"
    )
    
    exam_data = {
        "id": exam_id,
        "title": req.title,
        "subtitle": req.subtitle or "2º ANO DO ENSINO FUNDAMENTAL",
        "school_name": req.school_name or "",
        "classroom": req.classroom or "",
        "student_name": req.student_name or "",
        "shift": req.shift or "(  ) MANHÃ       (  ) TARDE",
        "logo_path": logo_path,
        "num_questions": req.num_questions,
        "num_alternatives": req.num_alternatives,
        "points_per_question": req.points_per_question,
        "answer_key": ans_key,
        "weights": req.weights or {},
        "sheet_template": template_data,
        "header_color": req.header_color or "#244061"
    }
    
    saved = save_exam(exam_data)
    return saved

@router.get("")
def get_all_exams():
    exams = list_exams()
    for ex in exams:
        subs = get_submissions_by_exam(ex["id"])
        ex["submissions_count"] = len(subs)
        linked = get_exam_linked_schools(ex["id"])
        ex["linked_schools"] = linked
        ex["is_linked_to_school"] = len(linked) > 0
    return exams

@router.get("/{exam_id}")
def get_single_exam(exam_id: str):
    exam = get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    subs = get_submissions_by_exam(exam_id)
    exam["submissions_count"] = len(subs)
    linked = get_exam_linked_schools(exam_id)
    exam["linked_schools"] = linked
    exam["is_linked_to_school"] = len(linked) > 0
    return exam

@router.put("/{exam_id}")
def update_existing_exam(exam_id: str, req: CreateExamRequest, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin", "coordenador"], authorization, x_auth_token)
    existing = get_exam(exam_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
        
    logo_path = existing.get("logo_path")
    if req.logo_base64:
        if req.logo_base64 == "NONE":
            logo_path = "NONE"
        else:
            try:
                b64_data = req.logo_base64
                if "," in b64_data:
                    b64_data = b64_data.split(",")[1]
                raw_logo = base64.b64decode(b64_data)
                logo_path = os.path.join(ASSETS_DIR, f"exam_{exam_id[:8]}_logo.png")
                with open(logo_path, "wb") as lf:
                    lf.write(raw_logo)
            except Exception:
                pass
                
    if not logo_path and os.path.exists(DEFAULT_LOGO_PATH):
        logo_path = DEFAULT_LOGO_PATH

    ans_key = req.answer_key
    if not ans_key:
        opts = ["A", "B", "C", "D", "E"][:req.num_alternatives]
        ans_key = {str(i): opts[(i - 1) % len(opts)] for i in range(1, req.num_questions + 1)}
        
    # Regenerate sheet PDF
    pdf_path = os.path.join(STORAGE_DIR, "sheets", f"exam_{exam_id}.pdf")
    pdf_bytes, template_data = generate_answer_sheet_pdf(
        exam_id=exam_id,
        title=req.title,
        subtitle=req.subtitle or "2º ANO DO ENSINO FUNDAMENTAL",
        school_name=req.school_name or "",
        student_name=req.student_name or "",
        classroom=req.classroom or "",
        shift=req.shift or "(  ) MANHÃ       (  ) TARDE",
        num_questions=req.num_questions,
        num_alternatives=req.num_alternatives,
        logo_path=logo_path,
        output_path=pdf_path,
        header_color=req.header_color or existing.get("header_color", "#244061")
    )
    
    updated_data = {
        "id": exam_id,
        "title": req.title,
        "subtitle": req.subtitle or "2º ANO DO ENSINO FUNDAMENTAL",
        "school_name": req.school_name or "",
        "classroom": req.classroom or "",
        "student_name": req.student_name or "",
        "shift": req.shift or "(  ) MANHÃ       (  ) TARDE",
        "logo_path": logo_path,
        "num_questions": req.num_questions,
        "num_alternatives": req.num_alternatives,
        "points_per_question": req.points_per_question,
        "answer_key": ans_key,
        "weights": req.weights or {},
        "sheet_template": template_data,
        "header_color": req.header_color or existing.get("header_color", "#244061")
    }
    
    res = update_exam(exam_id, updated_data)
    return res

def cleanup_submission_files(sub: Dict[str, Any]):
    """Removes image files of a submission from disk."""
    for url_key in ["overlay_image_url", "scanned_image_url"]:
        url = sub.get(url_key)
        if url and url.startswith("/storage/"):
            rel_path = url.replace("/storage/", "").replace("/", os.sep)
            file_path = os.path.join(STORAGE_DIR, rel_path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

@router.delete("/{exam_id}")
def remove_exam(exam_id: str, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin"], authorization, x_auth_token)
    exam = get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")

    # Only allow deleting if not linked to any school
    linked_schools = get_exam_linked_schools(exam_id)
    if linked_schools:
        school_items = []
        for s in linked_schools:
            if s.get("classrooms"):
                turmas = ", ".join(s["classrooms"][:3])
                if len(s["classrooms"]) > 3:
                    turmas += f" e mais {len(s['classrooms']) - 3} turma(s)"
                school_items.append(f"• {s['name']} (Turmas: {turmas})")
            else:
                school_items.append(f"• {s['name']}")
        escolas_detalhe = "\n".join(school_items)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Não é permitido excluir o gabarito '{exam['title']}' pois ele está vinculado à(s) seguinte(s) escola(s):\n"
                f"{escolas_detalhe}\n\n"
                "Para excluí-lo, desvincule este gabarito das turmas na aba 'Turmas'."
            )
        )

    # Clean up associated submission files
    subs = get_submissions_by_exam(exam_id)
    for s in subs:
        cleanup_submission_files(s)

    # Clean up generated PDF sheet
    pdf_path = os.path.join(STORAGE_DIR, "sheets", f"exam_{exam_id}.pdf")
    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception:
            pass

    # Clean up custom logo if generated specifically for this exam
    logo_path = exam.get("logo_path")
    if logo_path and os.path.exists(logo_path) and f"exam_{exam_id[:8]}" in logo_path:
        try:
            os.remove(logo_path)
        except Exception:
            pass

    success = delete_exam(exam_id)
    if not success:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    return {"message": "Simulado removido com sucesso"}

@router.delete("/{exam_id}/submissions")
def remove_all_submissions_of_exam(exam_id: str, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin"], authorization, x_auth_token)
    exam = get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    subs = get_submissions_by_exam(exam_id)
    for s in subs:
        cleanup_submission_files(s)
    deleted_count = delete_submissions_by_exam(exam_id)
    return {"message": f"{deleted_count} correções foram excluídas com sucesso."}

@submissions_router.get("/{submission_id}")
def get_single_submission(submission_id: str):
    sub = get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Correção não encontrada")
    return sub

@submissions_router.delete("/{submission_id}")
def remove_single_submission(submission_id: str, authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    require_roles(["admin"], authorization, x_auth_token)
    sub = get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Correção não encontrada")
    cleanup_submission_files(sub)
    delete_submission(submission_id)
    return {"message": "Correção excluída com sucesso."}

@router.get("/{exam_id}/sheet.pdf")
def download_sheet_pdf(exam_id: str, layout: str = "single", filled: bool = True):
    exam = get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
        
    sheets_per_page = 2 if (layout == "double" or layout == "2") else 1
    
    logo_p = exam.get("logo_path")
    if not logo_p or not os.path.exists(logo_p):
        logo_p = DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None

    # Determine if answers should be filled (Gabarito Oficial)
    ans_key = exam.get("answer_key", {}) if filled else None
    student_title = exam.get("student_name", "")
    if filled and not student_title:
        student_title = "GABARITO OFICIAL"

    # Generate on the fly with requested layout, selected color and filled answers
    pdf_bytes, template_data = generate_answer_sheet_pdf(
        exam_id=exam_id,
        title=exam["title"],
        subtitle=exam.get("subtitle", "2º ANO DO ENSINO FUNDAMENTAL"),
        school_name=exam.get("school_name", ""),
        student_name=student_title,
        classroom=exam.get("classroom", ""),
        shift=exam.get("shift", "(  ) MANHÃ       (  ) TARDE"),
        num_questions=exam["num_questions"],
        num_alternatives=exam["num_alternatives"],
        sheets_per_page=sheets_per_page,
        logo_path=logo_p,
        header_color=exam.get("header_color", "#244061"),
        filled_answers=ans_key
    )
    
    # Keep exam template in sync with high-precision bubble positions
    if sheets_per_page == 1 and template_data and not filled:
        try:
            update_exam_template(exam_id, template_data)
        except Exception:
            pass
            
    filename_suffix = "2_por_folha" if sheets_per_page == 2 else "completa"
    prefix = "gabarito_oficial_preenchido" if filled else "gabarito"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{prefix}_{exam_id[:8]}_{filename_suffix}.pdf"'}
    )

@router.get("/{exam_id}/submissions")
def get_exam_submissions(exam_id: str):
    exam = get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    return get_submissions_by_exam(exam_id)
