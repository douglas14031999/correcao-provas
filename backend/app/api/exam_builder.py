import os
import uuid
import shutil
import urllib.parse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Query, Depends
from starlette.concurrency import run_in_threadpool

from app.api.auth import get_authenticated_user
from app.services.exam_builder_db import (
    init_builder_db,
    list_builder_exams,
    get_builder_exam,
    create_builder_exam,
    update_builder_exam,
    delete_builder_exam,
    delete_builder_exams_batch,
    delete_question_from_bank,
    duplicate_builder_exam,
    sync_builder_exam_to_main_exams,
    get_builder_exam_grading_status,
    get_question_bank,
    get_question_bank_filters
)
from app.services.exam_builder_pdf import render_exam_html, generate_exam_pdf_bytes
from app.services.exam_builder_docx import generate_exam_docx_bytes
from app.services.database import list_schools_tree
from app.api.schools import sanitize_header_filename

router = APIRouter(
    prefix="/api/exam-builder",
    tags=["Elaborador de Provas"],
    dependencies=[Depends(get_authenticated_user)]
)

# Garantir diretório de armazenamento de imagens
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILDER_IMAGES_DIR = os.path.join(BASE_DIR, "storage", "builder_images")
os.makedirs(BUILDER_IMAGES_DIR, exist_ok=True)

# Inicializar tabelas dedicadas ao carregar o router
try:
    init_builder_db()
except Exception as e:
    import logging
    logging.getLogger("uvicorn").error(f"Erro ao inicializar tabelas do exam builder: {e}")

class AlternativePayload(BaseModel):
    id: Optional[str] = None
    letter: str
    text: str
    is_correct: bool = False
    image_url: Optional[str] = ""
    image_width: Optional[str] = "180px"
    image_align: Optional[str] = "center"
    image: Optional[Dict[str, Any]] = None

class QuestionPayload(BaseModel):
    id: Optional[str] = None
    question_number: int
    statement: str
    points: float = 1.0
    image_url: Optional[str] = ""
    image_position: Optional[str] = "after_statement"
    image_width: Optional[str] = "50%"
    image_caption: Optional[str] = ""
    bncc_code: Optional[str] = ""
    skill: Optional[str] = ""
    discipline: Optional[str] = ""
    grade_year: Optional[str] = ""
    difficulty: Optional[str] = "medio"
    type: Optional[str] = "4"
    alternatives: List[AlternativePayload] = []

class ExamPayload(BaseModel):
    title: str
    institution: Optional[str] = "PREFEITURA MUNICIPAL DE LAGOA DA CANOA - SEMED"
    school_name: Optional[str] = "SEMED - LAGOA DA CANOA"
    discipline: Optional[str] = "MATEMÁTICA"
    teacher_name: Optional[str] = ""
    grade_year: Optional[str] = "9º ANO"
    grade: Optional[str] = ""
    classroom: Optional[str] = "TURMA A"
    shift: Optional[str] = "MATUTINO"
    exam_date: Optional[str] = ""
    max_score: float = 10.0
    columns_layout: Optional[int] = 2
    columns: Optional[int] = 2
    font_size: Optional[str] = "medium"
    header_style: Optional[str] = "standard"
    include_header: Optional[bool] = True
    footer_text: Optional[str] = "Boa Prova!"
    include_answer_sheet: Optional[Any] = 1
    margin_top: Optional[float] = 3.0
    margin_bottom: Optional[float] = 2.0
    margin_left: Optional[float] = 3.0
    margin_right: Optional[float] = 2.0
    questions: Optional[List[QuestionPayload]] = []

@router.get("/exams")
def get_all_exams():
    """Retorna lista resumida de todas as avaliações elaboradas."""
    return list_builder_exams()

@router.get("/schools-autocomplete")
def get_schools_autocomplete():
    """Retorna nomes de escolas cadastradas no sistema para preenchimento rápido."""
    try:
        schools = list_schools_tree()
        return [{"id": s["id"], "name": s["name"]} for s in schools]
    except Exception:
        return []

@router.get("/exams/{exam_id}")
def get_exam_details(exam_id: str):
    """Retorna dados completos da avaliação com questões e alternativas."""
    exam = get_builder_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    return exam

@router.post("/exams")
def create_new_exam(payload: ExamPayload):
    """Cria uma nova avaliação no elaborador."""
    return create_builder_exam(payload.dict())

@router.put("/exams/{exam_id}")
def update_existing_exam(exam_id: str, payload: ExamPayload):
    """Atualiza dados e questões de uma avaliação existente."""
    updated = update_builder_exam(exam_id, payload.dict())
    if not updated:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada para atualização.")
    return updated

class BatchDeletePayload(BaseModel):
    exam_ids: List[str]

@router.delete("/exams/{exam_id}")
def delete_exam(exam_id: str):
    """Remove uma avaliação, mantendo as questões salvas no Banco de Questões."""
    success = delete_builder_exam(exam_id)
    return {"success": success}

@router.post("/exams/batch-delete")
def batch_delete_exams_endpoint(payload: BatchDeletePayload):
    """Exclui múltiplas avaliações em lote, mantendo todas as questões salvas no Banco de Questões."""
    count = delete_builder_exams_batch(payload.exam_ids)
    return {"success": True, "deleted_count": count}

class CreateGradingExamPayload(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    school_name: Optional[str] = None
    classroom: Optional[str] = None
    shift: Optional[str] = None
    page_count: Optional[int] = None
    cover_model: Optional[str] = "opcao_4_azul_nautico_lagoa"
    cover_title: Optional[str] = "PROVA CANOA"
    cover_subtitle: Optional[str] = None
    cover_instructions: Optional[str] = None
    header_color: Optional[str] = "#244061"

@router.post("/exams/{exam_id}/duplicate")
def duplicate_exam(exam_id: str):
    """Duplica uma avaliação existente com todas as suas questões e alternativas."""
    copy_exam = duplicate_builder_exam(exam_id)
    if not copy_exam:
        raise HTTPException(status_code=404, detail="Avaliação original não encontrada.")
    return copy_exam

@router.get("/exams/{exam_id}/grading-status")
def get_exam_grading_status(exam_id: str):
    """
    Retorna o status atual do gabarito oficial vinculado, validação de questões (Edge Case 1)
    e dados pré-preenchidos para o modal de configuração de gabarito e capa.
    """
    try:
        return get_builder_exam_grading_status(exam_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status do gabarito: {str(e)}")

@router.post("/exams/{exam_id}/create-grading-exam")
async def create_grading_exam_endpoint(exam_id: str, payload: Optional[CreateGradingExamPayload] = None):
    """
    Cria ou sincroniza o gabarito OMR oficial no sistema de correção a partir da prova elaborada,
    vinculando ao modelo de capa selecionado e gerando a folha de respostas OMR em PDF.
    """
    try:
        custom_data = payload.dict() if payload else {}
        result = await run_in_threadpool(sync_builder_exam_to_main_exams, exam_id, custom_data)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar gabarito OMR: {str(e)}")

@router.post("/exams/{exam_id}/sync-gabarito")
async def sync_gabarito(exam_id: str, payload: Optional[CreateGradingExamPayload] = None):
    """
    Compatibilidade retroativa: sincroniza o gabarito da prova com a tabela oficial de exames.
    """
    try:
        custom_data = payload.dict() if payload else {}
        result = await run_in_threadpool(sync_builder_exam_to_main_exams, exam_id, custom_data)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao sincronizar gabarito OMR: {str(e)}")

@router.get("/bank/questions")
def get_bank_questions_endpoint(
    query: str = Query("", description="Busca no enunciado"),
    discipline: str = Query("", description="Filtro por disciplina"),
    grade_year: str = Query("", description="Filtro por ano/série"),
    bncc_code: str = Query("", description="Filtro por código BNCC"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Retorna questões cadastradas de todas as provas para o Banco de Questões com alternativas e imagens."""
    return get_question_bank(
        query=query,
        discipline=discipline,
        grade_year=grade_year,
        bncc_code=bncc_code,
        limit=limit,
        offset=offset
    )

@router.get("/bank/filters")
def get_bank_filters_endpoint():
    """Retorna disciplinas, anos e códigos BNCC existentes no banco para popular filtros da UI."""
    return get_question_bank_filters()

@router.delete("/bank/questions/{question_id}")
def delete_bank_question_endpoint(question_id: str):
    """Exclui permanentemente uma questão e suas alternativas diretamente do Banco de Questões."""
    success = delete_question_from_bank(question_id)
    return {"success": success}

@router.post("/upload-image")
async def upload_question_image(file: UploadFile = File(...)):
    """
    Faz upload de imagem para anexar na questão ou alternativa.
    Converte automaticamente para WebP otimizado (preservando canal alfa e rotação EXIF),
    reduzindo o tamanho dos arquivos em até 80% antes do salvamento.
    Mantém arquivos .svg como vetoriais nativos.
    """
    filename = file.filename or "image.png"
    ext = os.path.splitext(filename)[1].lower()
    allowed_exts = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".svg"]
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado. Use PNG, JPG, WebP ou SVG.")
    
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Arquivo de imagem vazio.")

    # Se for SVG vetorial, mantém como .svg
    if ext == ".svg":
        unique_name = f"qimg_{uuid.uuid4().hex[:12]}.svg"
        dest_path = os.path.join(BUILDER_IMAGES_DIR, unique_name)
        with open(dest_path, "wb") as buffer:
            buffer.write(file_bytes)
        return {"url": f"/storage/builder_images/{unique_name}"}

    # Para imagens raster (PNG, JPG, BMP, etc.), converter para WebP
    try:
        from PIL import Image, ImageOps
        import io

        img = Image.open(io.BytesIO(file_bytes))
        
        # Corrigir orientação com base no EXIF (fotos de smartphone)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Tratar modos de cor e transparência
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Redimensionamento inteligente se for gigantesca (> 2048px)
        max_dim = 2048
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        unique_name = f"qimg_{uuid.uuid4().hex[:12]}.webp"
        dest_path = os.path.join(BUILDER_IMAGES_DIR, unique_name)
        
        # Salva em WebP com compressão de alta qualidade
        img.save(dest_path, format="WEBP", quality=85, method=6)
        return {"url": f"/storage/builder_images/{unique_name}"}

    except Exception:
        # Fallback de segurança se Pillow falhar em decodificar
        unique_name = f"qimg_{uuid.uuid4().hex[:12]}{ext}"
        dest_path = os.path.join(BUILDER_IMAGES_DIR, unique_name)
        with open(dest_path, "wb") as buffer:
            buffer.write(file_bytes)
        return {"url": f"/storage/builder_images/{unique_name}"}

@router.post("/preview-html")
def preview_exam_html_post(payload: Dict[str, Any], show_answers: bool = Query(False)):
    """Gera visualização HTML pronta para Live Preview a partir do payload recebido."""
    content = render_exam_html(payload, show_answers=show_answers)
    return Response(content=content, media_type="text/html; charset=utf-8")

@router.post("/generate-pdf")
async def generate_exam_pdf_post(payload: Dict[str, Any], show_answers: bool = Query(False)):
    """Gera e retorna o PDF da prova diagramada a partir do payload em edição."""
    try:
        pdf_bytes = await run_in_threadpool(generate_exam_pdf_bytes, payload, show_answers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao compilar PDF da prova: {str(e)}")
        
    raw_title = str(payload.get("title") or "Prova").strip()
    import re
    clean_title = re.sub(r'\.pdf$', '', raw_title, flags=re.IGNORECASE).strip() or "Prova"
    safe_title = sanitize_header_filename(clean_title)
    encoded_filename = urllib.parse.quote(f"{clean_title}.pdf")
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}.pdf"; filename*=UTF-8\'\'{encoded_filename}'
        }
    )

@router.post("/generate-docx")
async def generate_exam_docx_post(payload: Dict[str, Any], show_answers: bool = Query(False)):
    """Gera e retorna o documento Word (.docx) da prova diagramada a partir do payload em edição."""
    try:
        docx_bytes = await run_in_threadpool(generate_exam_docx_bytes, payload, show_answers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao compilar documento DOCX da prova: {str(e)}")
        
    raw_title = str(payload.get("title") or "Prova").strip()
    import re
    clean_title = re.sub(r'\.docx$', '', raw_title, flags=re.IGNORECASE).strip() or "Prova"
    safe_title = sanitize_header_filename(clean_title)
    encoded_filename = urllib.parse.quote(f"{clean_title}.docx")
    
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}.docx"; filename*=UTF-8\'\'{encoded_filename}'
        }
    )

@router.get("/exams/{exam_id}/html")
def preview_exam_html(exam_id: str, show_answers: bool = Query(False)):
    """Gera visualização HTML pronta para impressão ou Live Preview."""
    exam = get_builder_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    
    content = render_exam_html(exam, show_answers=show_answers)
    return Response(content=content, media_type="text/html; charset=utf-8")

@router.get("/exams/{exam_id}/pdf")
async def download_exam_pdf(exam_id: str, show_answers: bool = Query(False)):
    """Gera e retorna o PDF da prova diagramada em 1 ou 2 colunas com KaTeX."""
    exam = await run_in_threadpool(get_builder_exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    
    try:
        pdf_bytes = await run_in_threadpool(generate_exam_pdf_bytes, exam, show_answers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao compilar PDF da prova: {str(e)}")
        
    raw_title = str(exam.get("title") or "Prova").strip()
    import re
    clean_title = re.sub(r'\.pdf$', '', raw_title, flags=re.IGNORECASE).strip() or "Prova"
    safe_title = sanitize_header_filename(clean_title)
    encoded_filename = urllib.parse.quote(f"{clean_title}.pdf")
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}.pdf"; filename*=UTF-8\'\'{encoded_filename}'
        }
    )

@router.get("/exams/{exam_id}/docx")
async def download_exam_docx(exam_id: str, show_answers: bool = Query(False)):
    """Gera e retorna o documento Word (.docx) da prova diagramada para download direto."""
    exam = await run_in_threadpool(get_builder_exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    
    try:
        docx_bytes = await run_in_threadpool(generate_exam_docx_bytes, exam, show_answers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao compilar documento DOCX da prova: {str(e)}")
        
    raw_title = str(exam.get("title") or "Prova").strip()
    import re
    clean_title = re.sub(r'\.docx$', '', raw_title, flags=re.IGNORECASE).strip() or "Prova"
    safe_title = sanitize_header_filename(clean_title)
    encoded_filename = urllib.parse.quote(f"{clean_title}.docx")
    
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}.docx"; filename*=UTF-8\'\'{encoded_filename}'
        }
    )

@router.get("/classrooms/{classroom_id}/builder-exams")
async def get_classroom_builder_exams(classroom_id: str):
    """
    Retorna as avaliações do elaborador vinculadas à turma especificada.
    Usado para popular o modal de emissão de provas.
    """
    from app.services.database import get_classroom_with_details
    cl = await run_in_threadpool(get_classroom_with_details, classroom_id)
    if not cl:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
        
    linked_exams = cl.get("linked_exams") or []
    builder_exams_found = []
    
    for le in linked_exams:
        b_id = le.get("builder_exam_id")
        if b_id:
            b_exam = await run_in_threadpool(get_builder_exam, b_id)
            if b_exam:
                builder_exams_found.append({
                    "id": b_exam.get("id"),
                    "linked_exam_id": le.get("id"),
                    "title": b_exam.get("title") or le.get("title"),
                    "discipline": b_exam.get("discipline") or "GERAL",
                    "grade_year": b_exam.get("grade_year") or cl.get("grade_year") or "",
                    "question_count": len(b_exam.get("questions") or []),
                    "page_count": b_exam.get("page_count") or 1,
                    "updated_at": b_exam.get("updated_at")
                })
                
    return {
        "classroom_id": classroom_id,
        "classroom_name": cl.get("name") or "Turma",
        "school_name": cl.get("school_name") or "",
        "grade_year": cl.get("grade_year") or "",
        "builder_exams": builder_exams_found
    }

@router.get("/classrooms/{classroom_id}/download-provas")
async def download_classroom_provas(
    classroom_id: str,
    format: str = Query("pdf", regex="^(pdf|docx)$"),
    exam_ids: str = Query("", description="IDs separados por vírgula dos builder_exams a emitir. Se vazio, emite todos."),
    show_answers: bool = Query(False)
):
    """
    Gera e baixa as provas prontas no elaborador vinculadas à turma.
    - Se apenas 1 prova for solicitada/vinculada: download direto do arquivo .pdf ou .docx.
    - Se mais de 1 prova: download de arquivo .ZIP com as provas organizadas por disciplina.
    """
    import io, zipfile, re
    from app.services.database import get_classroom_with_details
    
    cl = await run_in_threadpool(get_classroom_with_details, classroom_id)
    if not cl:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
        
    linked_exams = cl.get("linked_exams") or []
    builder_exams_map = {}
    
    for le in linked_exams:
        b_id = le.get("builder_exam_id")
        if b_id:
            b_exam = await run_in_threadpool(get_builder_exam, b_id)
            if b_exam:
                builder_exams_map[b_id] = b_exam
                
    if not builder_exams_map:
        raise HTTPException(status_code=400, detail="Esta turma não possui provas do elaborador vinculadas para impressão.")
        
    requested_ids = [i.strip() for i in exam_ids.split(",") if i.strip()] if exam_ids else []
    if requested_ids:
        target_exams = [builder_exams_map[bid] for bid in requested_ids if bid in builder_exams_map]
    else:
        target_exams = list(builder_exams_map.values())
        
    if not target_exams:
        raise HTTPException(status_code=400, detail="Nenhuma prova válida selecionada para emissão.")
        
    cl_name = (cl.get("name") or "Turma").strip()
    safe_cl = sanitize_header_filename(cl_name)
    fmt = format.lower()
    
    # Caso 1: Apenas 1 prova -> Download direto do arquivo (.pdf ou .docx)
    if len(target_exams) == 1:
        single_exam = target_exams[0]
        raw_title = str(single_exam.get("title") or f"Prova_{cl_name}").strip()
        clean_title = re.sub(rf'\.{fmt}$', '', raw_title, flags=re.IGNORECASE).strip() or "Prova"
        safe_title = sanitize_header_filename(clean_title)
        encoded_filename = urllib.parse.quote(f"{clean_title}.{fmt}")
        
        if fmt == "pdf":
            file_bytes = await run_in_threadpool(generate_exam_pdf_bytes, single_exam, show_answers)
            media_type = "application/pdf"
        else:
            file_bytes = await run_in_threadpool(generate_exam_docx_bytes, single_exam, show_answers)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}.{fmt}"; filename*=UTF-8\'\'{encoded_filename}'
            }
        )
        
    # Caso 2: Múltiplas provas -> Pacote .ZIP organizado
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, ex in enumerate(target_exams):
            disc = (ex.get("discipline") or "GERAL").strip()
            title = (ex.get("title") or f"Prova_{idx+1}").strip()
            safe_file_title = re.sub(r'[\/\\:\*\?"<>\|]+', '_', f"{idx+1:02d}_{disc}_{title}")[:60].strip()
            
            if fmt == "pdf":
                f_bytes = await run_in_threadpool(generate_exam_pdf_bytes, ex, show_answers)
                zf.writestr(f"{safe_file_title}.pdf", f_bytes)
            else:
                f_bytes = await run_in_threadpool(generate_exam_docx_bytes, ex, show_answers)
                zf.writestr(f"{safe_file_title}.docx", f_bytes)
                
    zip_bytes = zip_buffer.getvalue()
    zip_filename = f"Provas_{safe_cl}_{fmt.upper()}.zip"
    encoded_zip_filename = urllib.parse.quote(zip_filename)
    
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"; filename*=UTF-8\'\'{encoded_zip_filename}'
        }
    )
