import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body

from starlette.concurrency import run_in_threadpool
from app.services.database import get_exam, save_submission, list_exams, get_submission, delete_submission
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
    Executes CPU-intensive OMR pipeline in a background thread pool.
    NOTE: Does NOT persist to database until confirmed by operator via /api/grade/confirm.
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
        
    # Mark as pending confirmation - NOT yet in database
    result["is_confirmed"] = False
    return result


@router.post("/confirm")
async def confirm_graded_exam(submission_data: Dict[str, Any] = Body(...)):
    """
    Persists a scanned submission into the database ONLY after the operator confirms it.
    Preserves the annotated X-Ray overlay image for visual auditing and removes the raw scanned photo
    to save server disk space and keep backups lightweight.
    """
    if not submission_data or "id" not in submission_data or "exam_id" not in submission_data:
        raise HTTPException(status_code=400, detail="Dados de correção inválidos.")

    # Check if already saved previously
    existing = await run_in_threadpool(get_submission, submission_data["id"])
    if existing:
        return {"success": True, "message": "Correção já confirmada anteriormente.", "submission": existing}

    # Delete raw scan image from disk upon confirmation, keeping only the overlay (Raio-X)
    raw_scan_url = submission_data.get("scanned_image_url")
    if raw_scan_url and raw_scan_url.startswith("/storage/"):
        rel_path = raw_scan_url.replace("/storage/", "").replace("/", os.sep)
        file_path = os.path.join(STORAGE_DIR, rel_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

    sub_id = submission_data.get("id")
    if sub_id:
        scan_disk_path = os.path.join(STORAGE_DIR, "scans", f"scanned_{sub_id}.jpg")
        if os.path.exists(scan_disk_path):
            try:
                os.remove(scan_disk_path)
            except Exception:
                pass

    # Point scanned_image_url to overlay_image_url so any visual view requests will display the Raio-X
    overlay_url = submission_data.get("overlay_image_url")
    if overlay_url:
        submission_data["scanned_image_url"] = overlay_url

    saved = await run_in_threadpool(save_submission, submission_data)
    return {"success": True, "message": "Prova confirmada e registrada com sucesso!", "submission": saved}


@router.post("/discard")
async def discard_graded_exam(payload: Dict[str, Any] = Body(...)):
    """
    Discards a scanned submission preview and immediately deletes both overlay and scanned images from disk.
    """
    sub_id = payload.get("id") or payload.get("submission_id")
    if sub_id:
        await run_in_threadpool(delete_submission, sub_id)
        for folder, prefix in [("overlays", "overlay"), ("scans", "scanned")]:
            fpath = os.path.join(STORAGE_DIR, folder, f"{prefix}_{sub_id}.jpg")
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass

    for url_key in ["overlay_image_url", "scanned_image_url"]:
        url = payload.get(url_key)
        if url and url.startswith("/storage/"):
            rel_path = url.replace("/storage/", "").replace("/", os.sep)
            file_path = os.path.join(STORAGE_DIR, rel_path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    return {"success": True, "message": "Leitura descartada com sucesso e arquivos temporários removidos."}

