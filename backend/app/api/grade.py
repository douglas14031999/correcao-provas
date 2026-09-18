import os
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from starlette.concurrency import run_in_threadpool
from app.services.database import get_exam, save_submission, list_exams
from app.services.omr_engine import grade_submission

router = APIRouter(prefix="/api/grade", tags=["Grading"])

STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage"
)

@router.post("")
async def grade_exam_sheet(
    file: UploadFile = File(...),
    exam_id: Optional[str] = Form(None),
    student_name: Optional[str] = Form("Aluno")
):
    """
    Receives photo of the answer sheet from mobile camera or file upload.
    Aligns sheet via ArUco, reads bubble fills, calculates grade and returns annotated X-Ray image.
    Executes CPU-intensive OMR pipeline in a background thread pool to prevent blocking the async event loop.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Nenhum arquivo de imagem foi enviado.")
        
    target_exam = None
    if exam_id and exam_id.strip() and exam_id.strip() != "AUTO":
        target_exam = await run_in_threadpool(get_exam, exam_id.strip())
        if not target_exam:
            raise HTTPException(status_code=404, detail=f"Simulado com ID '{exam_id}' não encontrado.")
    else:
        # Auto Mode / QR code detection: use most recent exam for initial geometric alignment
        exams = await run_in_threadpool(list_exams)
        if not exams:
            raise HTTPException(status_code=400, detail="Nenhum simulado cadastrado no sistema. Crie um primeiro.")
        target_exam = exams[0]
        
    try:
        result = await run_in_threadpool(
            grade_submission,
            image_bytes=contents,
            exam=target_exam,
            student_name=student_name or "Aluno",
            storage_dir=STORAGE_DIR
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento OMR: {str(e)}")
        
    # Persist submission into database asynchronously via threadpool
    await run_in_threadpool(save_submission, result)
    
    return result
